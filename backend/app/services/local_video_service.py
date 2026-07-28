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


class LocalVideoService:
    """Build a local voiceover and launch-ready vertical video."""

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

        target = self.media_root / f"campaign-{campaign_id}"
        target.mkdir(parents=True, exist_ok=True)
        audio = target / "voiceover.wav"
        video = target / "video.mp4"
        subtitles = target / "captions.srt"

        self._synthesize(job.video_script, voice_name, audio)
        duration = self._duration(audio)
        subtitles.write_text(
            self._subtitles(job.video_script, duration), encoding="utf-8"
        )
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=0x071A2B:s=1080x1920:r=30",
                "-i", str(audio),
                "-vf",
                (
                    "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/"
                    "DejaVuSans-Bold.ttf:text='TMI OS':fontcolor=0x45D6A8:"
                    "fontsize=72:x=(w-text_w)/2:y=170,"
                    "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/"
                    "DejaVuSans.ttf:text='THE MIYAR INDEX':fontcolor=white:"
                    "fontsize=38:x=(w-text_w)/2:y=270,"
                    "subtitles=captions.srt:force_style='FontName=DejaVu Sans,"
                    "FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00102030,"
                    "BorderStyle=3,Outline=2,Alignment=2,MarginV=220'"
                ),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p",
                "-shortest", "-movflags", "+faststart", str(video),
            ],
            cwd=target,
            check=True,
            capture_output=True,
            timeout=600,
        )
        if audio.stat().st_size < 1000 or video.stat().st_size < 10_000:
            raise ValueError("Local media generation produced an invalid file.")

        job.audio_url = f"/api/media/campaign-{campaign_id}/voiceover.wav"
        job.video_url = f"/api/media/campaign-{campaign_id}/video.mp4"
        job.media_generated_at = datetime.now(timezone.utc)
        job.voice_name = voice_name
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

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
