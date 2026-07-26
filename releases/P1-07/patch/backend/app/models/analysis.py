from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


class Analysis(Base):

    __tablename__ = "analyses"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "analysis_version",
            name="uq_analyses_campaign_version",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey(
            "campaigns.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    analysis_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    previous_analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    total_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    framework_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="The Mi'yar Index",
    )

    framework_version: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="1.0",
    )

    constitution_version: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="1",
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
    )

    prompt_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="legacy",
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    strengths: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    weaknesses: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    recommendations: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    dimensions: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    review_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    reviewed_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    review_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewer_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
