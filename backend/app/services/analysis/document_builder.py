import re

from app.models.campaign import Campaign
from app.services.analysis.models import AnalysisDocument


MAX_CONTENT_LENGTH = 4000


class DocumentBuilder:

    @staticmethod
    def _clean_content(content: str) -> str:
        if not content:
            return ""

        content = re.sub(r"\r\n?", "\n", content)
        content = re.sub(r"[ \t]+", " ", content)
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content.strip()[:MAX_CONTENT_LENGTH]

    def build(
        self,
        campaign: Campaign,
    ) -> AnalysisDocument:

        if campaign.id is None:
            raise ValueError(
                "Campaign must be persisted before analysis."
            )

        return AnalysisDocument(
            campaign_id=campaign.id,
            title=campaign.title,
            url=campaign.url,
            source=campaign.source,
            description=(campaign.description or "").strip(),
            content=self._clean_content(
                campaign.content or ""
            ),
            content_type="webpage",
            collected_at=campaign.created_at,
            metadata={
                "database_model": "Campaign",
                "content_truncated": len(campaign.content or "") > MAX_CONTENT_LENGTH,
            },
        )


document_builder = DocumentBuilder()