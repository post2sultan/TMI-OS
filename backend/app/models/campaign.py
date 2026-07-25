from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


class Campaign(Base):

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
    )

    fingerprint: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="discovered",
        server_default="discovered",
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    content: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )