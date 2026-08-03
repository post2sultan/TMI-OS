from __future__ import annotations

import re
import shutil
import subprocess
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content_creation_job import ContentCreationJob
from app.models.campaign import Campaign
from app.services.stock_media_service import StockMediaService


class LocalVideoService:
    """Build watermarked vertical and landscape videos from cached stock media."""

    VOICES = {
        "af_heart", "af_bella", "af_nicole", "am_adam",
        "am_michael", "bf_emma", "bm_george",
    }
    MODEL = "/opt/kokoro/kokoro-v1.0.onnx"
    VOICE_DATA = "/opt/kokoro/voices-v1.0.bin"

    def __init__(self, db: Session, media_root: str = "/app/media") -> None:
        self.db = db
        self.media_root = Path(media_root)

    def generate(
        self, campaign_id: int, voice_name: str = "af_heart"
    ) -> ContentCreationJob:
        job = self.db.scalar(
            select(ContentCreationJob).where(
                ContentCreationJob.campaign_id == campaign_id
            )
        )
        if job is None or not job.video_script.strip():
            raise ValueError("Generate the approved content package first.")
        self._validate_voice(voice_name)
        if not shutil.which("ffmpeg"):
            raise ValueError("Local media tools are unavailable.")
        campaign = self.db.get(Campaign, campaign_id)
        if campaign is None:
            raise ValueError("Campaign was not found.")

        target = self.media_root / f"campaign-{campaign_id}"
        target.mkdir(parents=True, exist_ok=True)
        audio = target / "voiceover.wav"
        video = target / "video.mp4"
        landscape = target / "video-landscape.mp4"
        subtitles = target / "captions.srt"
        logo = Path("/app/assets/brand/tmi-logo.png")
        if not logo.is_file():
            logo = Path(__file__).resolve().parents[2] / "assets" / "brand" / "tmi-logo.png"
        if not logo.is_file():
            raise ValueError("The mandatory TMI logo watermark is unavailable.")

        self._synthesize(job.video_script, voice_name, audio)
        duration = self._duration(audio)
        subtitles.write_text(
            self._subtitles(job.video_script, duration), encoding="utf-8"
        )
        try:
            stock = StockMediaService().collect(campaign, target / "stock")
        except Exception:
            stock = []
        self._render(stock, audio, subtitles, logo, video, 1080, 1920, duration)
        self._render(stock, audio, subtitles, logo, landscape, 1920, 1080, duration)
        if any(path.stat().st_size < minimum for path, minimum in ((audio, 1000), (video, 10_000), (landscape, 10_000))):
            raise ValueError("Local media generation produced an invalid file.")

        job.audio_url = f"/api/media/campaign-{campaign_id}/voiceover.wav"
        job.video_url = f"/api/media/campaign-{campaign_id}/video.mp4"
        job.media_generated_at = datetime.now(timezone.utc)
        job.voice_name = voice_name
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    @staticmethod
    def _render(stock: list[Path], audio: Path, subtitles: Path, logo: Path,
                output: Path, width: int, height: int, duration: float) -> None:
        target = output.parent
        normalized: list[Path] = []
        for index, source in enumerate(stock[:3]):
            clip = target / f"clip-{width}x{height}-{index:02}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-i", str(source), "-t", "6", "-an",
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps=30",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", str(clip),
            ], check=True, capture_output=True, timeout=180)
            normalized.append(clip)

        if normalized:
            listing = target / f"clips-{width}x{height}.txt"
            listing.write_text("".join(f"file '{path.name}'\n" for path in normalized), encoding="utf-8")
            visual = ["-stream_loop", "-1", "-f", "concat", "-safe", "0", "-i", listing.name]
        else:
            visual = ["-f", "lavfi", "-i", f"color=c=0x034C6B:s={width}x{height}:r=30"]

        logo_width = 170 if height > width else 220
        margin = 40 if height > width else 55
        subtitle_size = 18 if height > width else 22
        margin_v = 220 if height > width else 105
        filters = (
            f"[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=0x034C6B@0.18:t=fill,"
            f"drawbox=x=0:y=0:w=iw:h=10:color=0xF37F17@0.85:t=fill[base];"
            f"[2:v]scale={logo_width}:-1[mark];"
            f"[base][mark]overlay=W-w-{margin}:{margin}:format=auto[branded];"
            f"[branded]subtitles={subtitles.name}:force_style='FontName=Noto Sans,FontSize={subtitle_size},"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H006B4C03,BorderStyle=3,Outline=2,"
            f"Alignment=2,MarginL=80,MarginR=80,MarginV={margin_v}'[v]"
        )
        subprocess.run([
            "ffmpeg", "-y", *visual, "-i", str(audio), "-loop", "1", "-i", str(logo),
            "-filter_complex", filters, "-map", "[v]", "-map", "1:a", "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
        ], cwd=target, check=True, capture_output=True, timeout=600)

    @classmethod
    def preview(
        cls, voice_name: str, media_root: str = "/app/media"
    ) -> str:
        cls._validate_voice(voice_name)
        target = Path(media_root) / "voice-previews"
        target.mkdir(parents=True, exist_ok=True)
        output = target / f"{voice_name}.wav"
        cls._synthesize(
            "Welcome to TMI OS. Clear evidence, thoughtful analysis, and "
            "confident decisions for campaigns that matter.",
            voice_name,
            output,
        )
        return f"/api/media/voice-previews/{voice_name}.wav"

    @classmethod
    def _synthesize(cls, text: str, voice_name: str, output: Path) -> None:
        import soundfile as sf

        samples, sample_rate = cls._engine().create(
            text, voice=voice_name, speed=1.0, lang="en-us"
        )
        sf.write(output, samples, sample_rate)
        if output.stat().st_size < 1000:
            raise ValueError("Kokoro produced an invalid audio file.")

    @classmethod
    @lru_cache(maxsize=1)
    def _engine(cls):
        from kokoro_onnx import Kokoro

        return Kokoro(cls.MODEL, cls.VOICE_DATA)

    @classmethod
    def _validate_voice(cls, voice_name: str) -> None:
        if voice_name not in cls.VOICES:
            raise ValueError("Unsupported Kokoro voice.")

    @staticmethod
    def _duration(audio: Path) -> float:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(audio),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return max(float(result.stdout.strip()), 1.0)

    @staticmethod
    def _subtitles(script: str, duration: float) -> str:
        words = re.findall(r"\S+", script)
        chunks = [" ".join(words[index:index + 9]) for index in range(0, len(words), 9)]
        slot = duration / max(len(chunks), 1)
        entries = []
        for index, chunk in enumerate(chunks):
            entries.append(
                f"{index + 1}\n"
                f"{LocalVideoService._timestamp(index * slot)} --> "
                f"{LocalVideoService._timestamp(min((index + 1) * slot, duration))}\n"
                f"{chunk}\n"
            )
        return "\n".join(entries)

    @staticmethod
    def _timestamp(seconds: float) -> str:
        millis = int(seconds * 1000)
        hours, millis = divmod(millis, 3_600_000)
        minutes, millis = divmod(millis, 60_000)
        secs, millis = divmod(millis, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"
