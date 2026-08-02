from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CampaignCluster(Base):
    __tablename__ = "campaign_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="candidate", server_default="candidate", index=True
    )
    signal_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    source_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0"
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

