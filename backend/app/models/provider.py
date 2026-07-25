from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import func

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


class Provider(Base):

    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=100
    )

    daily_limit: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    daily_used: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    last_status: Mapped[str] = mapped_column(
        String(30),
        default="UNKNOWN"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )