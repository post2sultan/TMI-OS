from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


class Evidence(Base):

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    analysis_id: Mapped[int] = mapped_column(
        ForeignKey(
            "analyses.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    url: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    source: Mapped[str] = mapped_column(
        String(100),
        default=""
    )

    excerpt: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    relevance_score: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )