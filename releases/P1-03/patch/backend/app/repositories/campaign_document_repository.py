

from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.campaign_document import CAMPAIGN_DOCUMENT_TYPES
from app.models.campaign_document import CampaignDocument
from app.services.evidence_deduplicator import (
    EvidenceDeduplicator,
    evidence_deduplicator,
)


class CampaignDocumentRepository:

    def __init__(
        self,
        deduplicator: EvidenceDeduplicator = evidence_deduplicator,
    ) -> None:
        self.deduplicator = deduplicator

    def create(
        self,
        *,
        session: Session,
        campaign_id: int,
        document_type: str,
        source_url: str | None = None,
        title: str = "",
        extracted_text: str = "",
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
            extracted_text=extracted_text,
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

    def get_by_source_url(
        self,
        *,
        session: Session,
        campaign_id: int,
        source_url: str,
    ) -> CampaignDocument | None:

        return session.scalar(
            select(CampaignDocument).where(
                CampaignDocument.campaign_id == campaign_id,
                CampaignDocument.source_url == source_url,
            )
        )

    def apply_extraction(
        self,
        *,
        session: Session,
        document: CampaignDocument,
        title: str,
        extracted_text: str,
        published_at: datetime | None,
        retrieved_at: datetime,
        language: str,
        brand: str,
        media_assets: list[str],
        extraction_status: str,
        extraction_method: str,
    ) -> CampaignDocument:

        identity = self.deduplicator.identity(
            source_url=document.source_url,
            content=extracted_text,
        )
        candidates = self.list_by_campaign(
            session=session,
            campaign_id=document.campaign_id,
        )
        duplicate = None
        similarity_score = None
        for candidate in candidates:
            if candidate.id == document.id:
                continue
            if (
                identity.canonical_url
                and candidate.canonical_url == identity.canonical_url
            ) or (
                identity.content_hash
                and candidate.content_hash == identity.content_hash
            ):
                duplicate = candidate
                similarity_score = 1.0
                break

            score = self.deduplicator.semantic_similarity(
                extracted_text,
                candidate.extracted_text,
            )
            if score >= self.deduplicator.SEMANTIC_SIMILARITY_THRESHOLD:
                duplicate = candidate
                similarity_score = score
                break

        document.title = title[:500]
        document.extracted_text = extracted_text
        document.published_at = published_at
        document.retrieved_at = retrieved_at
        document.language = language[:20]
        document.brand = brand[:255]
        document.media_assets = media_assets
        document.extraction_status = (
            "duplicate"
            if duplicate is not None
            else extraction_status.lower()
        )
        document.extraction_method = extraction_method[:100]
        document.canonical_url = identity.canonical_url
        document.content_hash = identity.content_hash
        document.duplicate_of_id = (
            duplicate.id if duplicate is not None else None
        )
        document.similarity_score = similarity_score
        session.add(document)
        session.flush()
        return document


campaign_document_repository = CampaignDocumentRepository()
