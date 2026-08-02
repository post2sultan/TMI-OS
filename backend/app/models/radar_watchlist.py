from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RadarWatchlist(Base):
    __tablename__ = "radar_watchlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    market: Mapped[str] = mapped_column(String(100), nullable=False, default="Saudi Arabia")
    languages: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=lambda: ["en", "ar"])
    brands: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    competitors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    locations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    campaign_terms: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    channels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
