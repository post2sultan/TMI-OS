

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


CAMPAIGN_DOCUMENT_TYPES = (
    "web_page",
    "news_article",
    "press_release",
    "social_post",
    "video_page",
    "image",
    "uploaded_document",
    "manual_observation",
)


class CampaignDocument(Base):

    __tablename__ = "campaign_documents"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "source_url",
            name="uq_campaign_documents_campaign_source_url",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )
    extracted_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    retrieved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    language: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="",
    )
    brand: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
    )
    media_assets: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    extraction_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )
    extraction_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
    )
    canonical_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        index=True,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="",
        index=True,
    )
    duplicate_of_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "campaign_documents.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    similarity_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
