from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.campaign_document import CAMPAIGN_DOCUMENT_TYPES
from app.models.campaign_document import CampaignDocument


class CampaignDocumentRepository:

    def create(
        self,
        *,
        session: Session,
        campaign_id: int,
        document_type: str,
        source_url: str | None = None,
        title: str = "",
        content: str = "",
    ) -> CampaignDocument:

        if document_type not in CAMPAIGN_DOCUMENT_TYPES:
            raise ValueError(
                f"Unsupported campaign document type: {document_type}"
            )

        document = CampaignDocument(
            campaign_id=campaign_id,
            document_type=document_type,
            source_url=source_url,
            title=title,
            content=content,
        )
        session.add(document)
        session.flush()
        return document

    def list_by_campaign(
        self,
        *,
        session: Session,
        campaign_id: int,
    ) -> list[CampaignDocument]:

        statement = (
            select(CampaignDocument)
            .where(
                CampaignDocument.campaign_id
                == campaign_id
            )
            .order_by(
                CampaignDocument.created_at,
                CampaignDocument.id,
            )
        )
        return list(
            session.scalars(statement).all()
        )


campaign_document_repository = CampaignDocumentRepository()
