from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content_creation_job import ContentCreationJob


class SocialExportService:
    """Create a platform-neutral, manually publishable social package."""

    def __init__(self, db: Session, media_root: str = "/app/media") -> None:
        self.db = db
        self.media_root = Path(media_root)

    def export(self, campaign_id: int) -> ContentCreationJob:
        job = self.db.scalar(
            select(ContentCreationJob).where(
                ContentCreationJob.campaign_id == campaign_id
            )
        )
        if job is None or not job.video_url or not job.social_caption:
            raise ValueError("Generate the campaign video and social copy first.")

        campaign_dir = self.media_root / f"campaign-{campaign_id}"
        video = campaign_dir / "video.mp4"
        landscape_source = campaign_dir / "video-landscape.mp4"
        if not video.is_file() or video.stat().st_size < 10_000:
            raise ValueError("Generated campaign video was not found.")

        export_dir = campaign_dir / "social-export"
        export_dir.mkdir(parents=True, exist_ok=True)
        youtube = export_dir / "youtube-video-1920x1080.mp4"
        linkedin = export_dir / "linkedin-post-1080x1080.mp4"
        if landscape_source.is_file() and landscape_source.stat().st_size >= 10_000:
            youtube.write_bytes(landscape_source.read_bytes())
        else:
            self._render(video, youtube, "1920:1080")
        self._render(video, linkedin, "1080:1080")
        package = export_dir / f"campaign-{campaign_id}-social-package.zip"
        caption = f"{job.social_caption.strip()}\n\n{' '.join(job.hashtags)}\n"
        manifest = {
            "campaign_id": campaign_id,
            "voice": job.voice_name,
            "channels": [
                {"name": "YouTube video", "file": "youtube/video.mp4", "size": "1920x1080"},
                {"name": "YouTube Shorts", "file": "youtube/shorts.mp4", "size": "1080x1920"},
                {"name": "Instagram Reels", "file": "instagram/reel.mp4", "size": "1080x1920"},
                {"name": "Instagram Stories", "file": "instagram/story.mp4", "size": "1080x1920"},
                {"name": "TikTok", "file": "tiktok/reel.mp4", "size": "1080x1920"},
                {"name": "LinkedIn post", "file": "linkedin/post.mp4", "size": "1080x1080"},
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "paid_api_credits": 0,
        }

        with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
            archive.write(youtube, "youtube/video.mp4")
            archive.write(video, "youtube/shorts.mp4")
            archive.write(video, "instagram/reel.mp4")
            archive.write(video, "instagram/story.mp4")
            archive.write(video, "tiktok/reel.mp4")
            archive.write(linkedin, "linkedin/post.mp4")
            for channel in ("youtube", "instagram", "tiktok", "linkedin"):
                archive.writestr(f"{channel}/caption.txt", caption)
            archive.writestr("script.txt", job.video_script.strip() + "\n")
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, indent=2, ensure_ascii=False),
            )

        if package.stat().st_size < 10_000:
            raise ValueError("Social export package is invalid.")
        job.social_export_url = (
            f"/api/media/campaign-{campaign_id}/social-export/{package.name}"
        )
        job.exported_at = datetime.now(timezone.utc)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    @staticmethod
    def _render(source: Path, target: Path, size: str) -> None:
        width, height = size.split(":")
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(source),
                "-vf",
                (
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x071A2B"
                ),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "copy", "-movflags", "+faststart", str(target),
            ],
            check=True,
            capture_output=True,
            timeout=600,
        )
        if target.stat().st_size < 10_000:
            raise ValueError("Channel video rendering failed.")
