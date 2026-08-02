
from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.campaign import Campaign
from app.models.campaign_document import CampaignDocument
from app.models.content_creation_job import ContentCreationJob
from app.services.campaign_lifecycle import campaign_lifecycle


class ReviewService:
    """Handles campaign analysis review actions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_reviews(self, review_status: str) -> dict[str, Any]:
        campaign_status = {
            "pending": "needs_review",
            "published": "published",
        }.get(review_status, review_status)
        analysis_status = (
            "approved" if review_status == "published" else review_status
        )
        latest_analysis_subquery = (
            select(
                Analysis.campaign_id,
                func.max(Analysis.id).label(
                    "latest_analysis_id"
                ),
            )
            .group_by(Analysis.campaign_id)
            .subquery()
        )

        statement = (
            select(
                Analysis,
                Campaign,
            )
            .join(
                latest_analysis_subquery,
                Analysis.id
                == latest_analysis_subquery.c.latest_analysis_id,
            )
            .join(
                Campaign,
                Campaign.id == Analysis.campaign_id,
            )
            .where(
                Analysis.review_status == analysis_status,
                Campaign.status == campaign_status,
            )
            .order_by(
                Analysis.created_at.desc(),
                Analysis.id.desc(),
            )
        )

        rows = self.db.execute(
            statement
        ).all()

        items: list[dict[str, Any]] = []

        for analysis, campaign in rows:
            items.append(
                {
                    "campaign_id": campaign.id,
                    "campaign_title": (
                        self._campaign_title(
                            campaign
                        )
                    ),
                    "campaign_status": (
                        campaign.status
                    ),
                    "analysis_id": analysis.id,
                    "total_score": (
                        analysis.total_score
                    ),
                    "confidence": (
                        analysis.confidence
                    ),
                    "summary": analysis.summary,
                    "review_status": (
                        analysis.review_status
                    ),
                    "created_at": (
                        analysis.created_at
                    ),
                }
            )

        return {
            "items": items,
            "total": len(items),
        }

    def get_content_creation_jobs(self) -> dict[str, Any]:
        statement = (
            select(ContentCreationJob, Campaign)
            .join(Campaign, Campaign.id == ContentCreationJob.campaign_id)
            .order_by(
                ContentCreationJob.created_at.desc(),
                ContentCreationJob.id.desc(),
            )
        )
        items = [
            {
                "id": job.id,
                "campaign_id": job.campaign_id,
                "campaign_title": self._campaign_title(campaign),
                "analysis_id": job.analysis_id,
                "status": job.status,
                "created_at": job.created_at,
                "published_at": job.published_at,
                "video_script": job.video_script,
                "social_caption": job.social_caption,
                "hashtags": list(job.hashtags),
                "generated_at": job.generated_at,
                "audio_url": job.audio_url,
                "video_url": job.video_url,
                "media_generated_at": job.media_generated_at,
                "voice_name": job.voice_name,
                "social_export_url": job.social_export_url,
                "exported_at": job.exported_at,
                "youtube_status": job.youtube_status,
                "youtube_video_id": job.youtube_video_id,
                "youtube_url": job.youtube_url,
                "youtube_error": job.youtube_error,
                "youtube_attempts": job.youtube_attempts,
                "youtube_requested_at": job.youtube_requested_at,
                "instagram_status": job.instagram_status,
                "instagram_media_id": job.instagram_media_id,
                "instagram_url": job.instagram_url,
                "instagram_error": job.instagram_error,
                "instagram_attempts": job.instagram_attempts,
                "instagram_requested_at": job.instagram_requested_at,
                "instagram_story_status": job.instagram_story_status,
                "instagram_story_media_id": job.instagram_story_media_id,
                "instagram_story_error": job.instagram_story_error,
                "instagram_story_attempts": job.instagram_story_attempts,
                "instagram_story_requested_at": job.instagram_story_requested_at,
            }
            for job, campaign in self.db.execute(statement).all()
        ]
        return {"items": items, "total": len(items)}

    def approve_analysis(
        self,
        campaign_id: int,
        approved_by: str,
    ) -> bool:
        campaign = self._get_campaign(
            campaign_id
        )

        if campaign is None:
            return False

        analysis = self._get_latest_analysis(
            campaign_id
        )

        if analysis is None:
            return False

        analysis.review_status = "approved"
        analysis.reviewed_by = (
            approved_by.strip()
        )
        analysis.review_reason = None
        analysis.reviewed_at = (
            datetime.now(timezone.utc)
        )

        campaign_lifecycle.transition(
            campaign,
            "approved",
        )
        existing_job = self.db.scalar(
            select(ContentCreationJob).where(
                ContentCreationJob.analysis_id == analysis.id
            )
        )
        if existing_job is None:
            self.db.add(
                ContentCreationJob(
                    campaign_id=campaign.id,
                    analysis_id=analysis.id,
                    status="queued",
                )
            )

        self.db.commit()
        self.db.refresh(analysis)
        self.db.refresh(campaign)

        return True

    def publish_campaign(self, campaign_id: int) -> bool:
        campaign = self._get_campaign(campaign_id)
        analysis = self._get_latest_analysis(campaign_id)
        if campaign is None or analysis is None:
            return False
        if analysis.review_status != "approved":
            return False

        job = self.db.scalar(
            select(ContentCreationJob).where(
                ContentCreationJob.analysis_id == analysis.id
            )
        )
        if job is None:
            return False
        if (
            not job.video_script.strip()
            or not job.social_caption.strip()
            or not job.video_url.strip()
        ):
            return False
        if job.youtube_status in {"queued", "uploading"}:
            return True
        job.youtube_status = "queued"
        job.youtube_error = ""
        job.youtube_requested_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(campaign)
        self.db.refresh(job)
        return True

    def next_youtube_publish(self) -> ContentCreationJob | None:
        stale_before = datetime.now(timezone.utc) - timedelta(minutes=15)
        job = self.db.scalar(
            select(ContentCreationJob)
            .where(
                or_(
                    ContentCreationJob.youtube_status == "queued",
                    (ContentCreationJob.youtube_status == "uploading")
                    & (ContentCreationJob.youtube_requested_at < stale_before),
                )
            )
            .order_by(ContentCreationJob.youtube_requested_at.asc())
            .with_for_update(skip_locked=True)
        )
        if job is None:
            return None
        job.youtube_status = "uploading"
        job.youtube_attempts += 1
        self.db.commit()
        self.db.refresh(job)
        return job

    def complete_youtube_publish(self, job_id: int, video_id: str) -> bool:
        job = self.db.get(ContentCreationJob, job_id)
        if job is None or job.youtube_status not in {"uploading", "queued"}:
            return False
        campaign = self._get_campaign(job.campaign_id)
        if campaign is None:
            return False
        job.youtube_status = "published"
        job.youtube_video_id = video_id
        job.youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        job.youtube_error = ""
        job.status = "published"
        job.published_at = datetime.now(timezone.utc)
        campaign_lifecycle.transition(campaign, "published")
        self.db.commit()
        return True

    def fail_youtube_publish(self, job_id: int, error: str) -> bool:
        job = self.db.get(ContentCreationJob, job_id)
        if job is None:
            return False
        job.youtube_status = "failed"
        job.youtube_error = error[:2000]
        self.db.commit()
        return True

    def queue_instagram_publish(self, campaign_id: int) -> bool:
        job = self.db.scalar(select(ContentCreationJob).where(ContentCreationJob.campaign_id == campaign_id))
        if job is None or not job.video_url or not job.social_caption:
            return False
        if job.instagram_status in {"queued", "uploading"}:
            return True
        job.instagram_status = "queued"
        job.instagram_error = ""
        job.instagram_requested_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def next_instagram_publish(self) -> ContentCreationJob | None:
        stale = datetime.now(timezone.utc) - timedelta(minutes=15)
        job = self.db.scalar(
            select(ContentCreationJob)
            .where(or_(ContentCreationJob.instagram_status == "queued", (ContentCreationJob.instagram_status == "uploading") & (ContentCreationJob.instagram_requested_at < stale)))
            .order_by(ContentCreationJob.instagram_requested_at.asc())
            .with_for_update(skip_locked=True)
        )
        if job is None:
            return None
        job.instagram_status = "uploading"
        job.instagram_attempts += 1
        self.db.commit()
        self.db.refresh(job)
        return job

    def complete_instagram_publish(self, job_id: int, media_id: str) -> bool:
        job = self.db.get(ContentCreationJob, job_id)
        if job is None:
            return False
        job.instagram_status = "published"
        job.instagram_media_id = media_id
        job.instagram_url = "https://www.instagram.com/"
        job.instagram_error = ""
        self.db.commit()
        return True

    def fail_instagram_publish(self, job_id: int, error: str) -> bool:
        job = self.db.get(ContentCreationJob, job_id)
        if job is None:
            return False
        job.instagram_status = "failed"
        job.instagram_error = error[:2000]
        self.db.commit()
        return True

    def queue_instagram_story(self, campaign_id: int) -> bool:
        job=self.db.scalar(select(ContentCreationJob).where(ContentCreationJob.campaign_id==campaign_id))
        if job is None or not job.video_url: return False
        if job.instagram_story_status in {"queued","uploading"}: return True
        job.instagram_story_status="queued"; job.instagram_story_error=""; job.instagram_story_requested_at=datetime.now(timezone.utc); self.db.commit(); return True

    def next_instagram_story(self) -> ContentCreationJob | None:
        stale=datetime.now(timezone.utc)-timedelta(minutes=15)
        job=self.db.scalar(select(ContentCreationJob).where(or_(ContentCreationJob.instagram_story_status=="queued",(ContentCreationJob.instagram_story_status=="uploading")&(ContentCreationJob.instagram_story_requested_at<stale))).order_by(ContentCreationJob.instagram_story_requested_at.asc()).with_for_update(skip_locked=True))
        if job is None: return None
        job.instagram_story_status="uploading"; job.instagram_story_attempts+=1; self.db.commit(); self.db.refresh(job); return job

    def complete_instagram_story(self, job_id: int, media_id: str) -> bool:
        job=self.db.get(ContentCreationJob,job_id)
        if job is None: return False
        job.instagram_story_status="published"; job.instagram_story_media_id=media_id; job.instagram_story_error=""; self.db.commit(); return True

    def fail_instagram_story(self, job_id: int, error: str) -> bool:
        job=self.db.get(ContentCreationJob,job_id)
        if job is None: return False
        job.instagram_story_status="failed"; job.instagram_story_error=error[:2000]; self.db.commit(); return True

    def reject_analysis(
        self,
        campaign_id: int,
        rejected_by: str,
        reason: str,
    ) -> bool:
        campaign = self._get_campaign(
            campaign_id
        )

        if campaign is None:
            return False

        analysis = self._get_latest_analysis(
            campaign_id
        )

        if analysis is None:
            return False

        analysis.review_status = "rejected"
        analysis.reviewed_by = (
            rejected_by.strip()
        )
        analysis.review_reason = (
            reason.strip()
        )
        analysis.reviewed_at = (
            datetime.now(timezone.utc)
        )

        campaign_lifecycle.transition(
            campaign,
            "rejected",
        )

        self.db.commit()
        self.db.refresh(analysis)
        self.db.refresh(campaign)

        return True

    def reanalyze_campaign(
        self,
        campaign_id: int,
    ) -> bool:
        campaign = self._get_campaign(
            campaign_id
        )

        if campaign is None:
            return False

        campaign_lifecycle.transition(
            campaign,
            "ready_for_analysis",
        )

        self.db.commit()
        self.db.refresh(campaign)

        return True

    def get_campaign_evidence(
        self,
        campaign_id: int,
    ) -> list[CampaignDocument] | None:
        if self._get_campaign(campaign_id) is None:
            return None
        statement = (
            select(CampaignDocument)
            .where(CampaignDocument.campaign_id == campaign_id)
            .order_by(CampaignDocument.created_at, CampaignDocument.id)
        )
        return list(self.db.scalars(statement).all())

    def edit_latest_analysis(
        self,
        *,
        campaign_id: int,
        edited_by: str,
        reviewer_notes: str,
        summary: str | None,
        strengths: list[str] | None,
        weaknesses: list[str] | None,
        recommendations: list[str] | None,
    ) -> Analysis | None:
        campaign = self._get_campaign(campaign_id)
        current = self._get_latest_analysis(campaign_id)
        if campaign is None or current is None:
            return None

        edited = Analysis(
            campaign_id=current.campaign_id,
            analysis_version=current.analysis_version + 1,
            previous_analysis_id=current.id,
            total_score=current.total_score,
            confidence=current.confidence,
            framework_name=current.framework_name,
            framework_version=current.framework_version,
            constitution_version=current.constitution_version,
            model_name=current.model_name,
            model_version=current.model_version,
            prompt_version=current.prompt_version,
            summary=summary if summary is not None else current.summary,
            strengths=(
                strengths if strengths is not None else list(current.strengths)
            ),
            weaknesses=(
                weaknesses if weaknesses is not None else list(current.weaknesses)
            ),
            recommendations=(
                recommendations
                if recommendations is not None
                else list(current.recommendations)
            ),
            dimensions=list(current.dimensions),
            review_status="pending",
            reviewed_by=edited_by.strip(),
            review_reason=reviewer_notes.strip() or None,
            reviewer_notes=reviewer_notes.strip() or None,
            reviewed_at=datetime.now(timezone.utc),
        )
        campaign.status = "needs_review"
        self.db.add(edited)
        self.db.commit()
        self.db.refresh(edited)
        self.db.refresh(campaign)
        return edited

    def archive_campaign(self, campaign_id: int) -> bool:
        campaign = self._get_campaign(campaign_id)
        if campaign is None:
            return False
        campaign_lifecycle.transition(campaign, "archived")
        self.db.commit()
        self.db.refresh(campaign)
        return True

    def _get_campaign(
        self,
        campaign_id: int,
    ) -> Campaign | None:
        return self.db.get(
            Campaign,
            campaign_id,
        )

    def _get_latest_analysis(
        self,
        campaign_id: int,
    ) -> Analysis | None:
        statement = (
            select(Analysis)
            .where(
                Analysis.campaign_id
                == campaign_id
            )
            .order_by(
                Analysis.created_at.desc(),
                Analysis.id.desc(),
            )
            .limit(1)
        )

        return self.db.scalar(
            statement
        )

    @staticmethod
    def _campaign_title(
        campaign: Campaign,
    ) -> str:
        if campaign.title:
            return campaign.title

        return f"Campaign {campaign.id}"
