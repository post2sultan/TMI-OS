from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import func

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


class DiscoveryRun(Base):

    __tablename__ = "discovery_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    query: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    results_found: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    credits_used: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    duration_ms: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="SUCCESS"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )