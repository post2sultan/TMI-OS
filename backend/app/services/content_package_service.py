from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.campaign import Campaign
from app.models.content_creation_job import ContentCreationJob
from app.services.ai.router import AIRouter, ai_router


class ContentPackageService:
    def __init__(self, database: Session, ai_client: AIRouter = ai_router) -> None:
        self.database = database
        self.ai_client = ai_client

    @staticmethod
    def _extract_payload(raw: str) -> dict:
        normalized = re.sub(
            r"^\s*```(?:json)?\s*|\s*```\s*$",
            "",
            raw.strip(),
            flags=re.IGNORECASE,
        )
        start = normalized.find("{")
        end = normalized.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Content model did not return a JSON object.")
        payload = json.loads(normalized[start : end + 1])
        if not isinstance(payload, dict):
            raise ValueError("Content package must be a JSON object.")
        return payload

    @staticmethod
    def _clean_hashtags(values: object) -> list[str]:
        if not isinstance(values, list):
            return []
        cleaned: list[str] = []
        for value in values[:8]:
            tag = re.sub(r"[^A-Za-z0-9_]", "", str(value))
            if tag:
                cleaned.append(f"#{tag}")
        return list(dict.fromkeys(cleaned))

    def generate(self, campaign_id: int) -> ContentCreationJob | None:
        campaign = self.database.get(Campaign, campaign_id)
        if campaign is None or campaign.status not in {"approved", "published"}:
            return None
        analysis = self.database.scalar(
            select(Analysis)
            .where(Analysis.campaign_id == campaign_id)
            .order_by(Analysis.created_at.desc(), Analysis.id.desc())
            .limit(1)
        )
        if analysis is None or analysis.review_status != "approved":
            return None
        job = self.database.scalar(
            select(ContentCreationJob).where(
                ContentCreationJob.analysis_id == analysis.id
            )
        )
        if job is None:
            job = ContentCreationJob(
                campaign_id=campaign.id,
                analysis_id=analysis.id,
            )
            self.database.add(job)

        prompt = "\n".join(
            [
                "Create a concise social content package from this approved campaign.",
                "Return only one JSON object with keys: video_script, social_caption, hashtags.",
                "video_script: 90-140 words for a 45-60 second factual voiceover.",
                "social_caption: 35-70 words with a clear hook and no invented claims.",
                "hashtags: array of 3-6 short relevant hashtags.",
                f"Campaign: {campaign.title}",
                f"Description: {campaign.description}",
                f"TMI score: {analysis.total_score}",
                f"Summary: {analysis.summary}",
                f"Strengths: {'; '.join(map(str, analysis.strengths))}",
                f"Recommendations: {'; '.join(map(str, analysis.recommendations))}",
            ]
        )
        payload = self._extract_payload(
            self.ai_client.generate(prompt, require_json=False)
        )
        script = str(payload.get("video_script", "")).strip()
        caption = str(payload.get("social_caption", "")).strip()
        hashtags = self._clean_hashtags(payload.get("hashtags"))
        if len(script) < 80 or len(caption) < 20 or len(hashtags) < 3:
            raise ValueError("Generated content package is incomplete.")

        job.video_script = script[:5000]
        job.social_caption = caption[:3000]
        job.hashtags = hashtags
        job.status = (
            "published" if campaign.status == "published" else "generated"
        )
        job.generated_at = datetime.now(timezone.utc)
        self.database.commit()
        self.database.refresh(job)
        return job
