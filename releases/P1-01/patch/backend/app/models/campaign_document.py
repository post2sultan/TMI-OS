from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
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
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
