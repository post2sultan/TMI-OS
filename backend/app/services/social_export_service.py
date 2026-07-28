from __future__ import annotations

import json
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
        if not video.is_file() or video.stat().st_size < 10_000:
            raise ValueError("Generated campaign video was not found.")

        export_dir = campaign_dir / "social-export"
        export_dir.mkdir(parents=True, exist_ok=True)
        package = export_dir / f"campaign-{campaign_id}-social-package.zip"
        caption = f"{job.social_caption.strip()}\n\n{' '.join(job.hashtags)}\n"
        manifest = {
            "campaign_id": campaign_id,
            "voice": job.voice_name,
            "format": "vertical_mp4",
            "channels": ["Instagram Reels", "TikTok", "YouTube Shorts", "LinkedIn"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "paid_api_credits": 0,
        }

        with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
            archive.write(video, "video.mp4")
            archive.writestr("caption.txt", caption)
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
