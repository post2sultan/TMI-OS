from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ContentCreationJob(Base):
    __tablename__ = "content_creation_jobs"
    __table_args__ = (
        UniqueConstraint("analysis_id", name="uq_content_jobs_analysis"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="queued",
        server_default="queued",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    video_script: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
    )
    social_caption: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
    )
    hashtags: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    audio_url: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    video_url: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    media_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    voice_name: Mapped[str] = mapped_column(
        String(50), nullable=False, default="af_heart", server_default="af_heart"
    )
    social_export_url: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    exported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    youtube_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="not_queued", server_default="not_queued"
    )
    youtube_video_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", server_default=""
    )
    youtube_url: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    youtube_error: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    youtube_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    youtube_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    instagram_status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_queued", server_default="not_queued")
    instagram_media_id: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    instagram_url: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    instagram_error: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    instagram_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    instagram_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    instagram_story_status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_queued", server_default="not_queued")
    instagram_story_media_id: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    instagram_story_error: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    instagram_story_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    instagram_story_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tiktok_status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_queued", server_default="not_queued")
    tiktok_publish_id: Mapped[str] = mapped_column(String(128), nullable=False, default="", server_default="")
    tiktok_error: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    tiktok_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    tiktok_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
