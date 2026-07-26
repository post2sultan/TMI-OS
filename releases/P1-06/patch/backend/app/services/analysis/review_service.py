
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.campaign import Campaign
from app.models.campaign_document import CampaignDocument
from app.services.campaign_lifecycle import campaign_lifecycle


class ReviewService:
    """Handles campaign analysis review actions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_pending_reviews(self) -> dict[str, Any]:
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
                Analysis.review_status == "pending"
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

        self.db.commit()
        self.db.refresh(analysis)
        self.db.refresh(campaign)

        return True

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
            total_score=current.total_score,
            confidence=current.confidence,
            framework_name=current.framework_name,
            framework_version=current.framework_version,
            constitution_version=current.constitution_version,
            model_name=current.model_name,
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
