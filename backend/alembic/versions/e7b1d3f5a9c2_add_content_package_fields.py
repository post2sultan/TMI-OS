"""add content package fields

Revision ID: e7b1d3f5a9c2
Revises: d6a9c2e4f7b1
Create Date: 2026-07-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e7b1d3f5a9c2"
down_revision: Union[str, Sequence[str], None] = "d6a9c2e4f7b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "content_creation_jobs",
        sa.Column(
            "video_script",
            sa.Text(),
            server_default="",
            nullable=False,
        ),
    )
    op.add_column(
        "content_creation_jobs",
        sa.Column(
            "social_caption",
            sa.Text(),
            server_default="",
            nullable=False,
        ),
    )
    op.add_column(
        "content_creation_jobs",
        sa.Column(
            "hashtags",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        "content_creation_jobs",
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_creation_jobs", "generated_at")
    op.drop_column("content_creation_jobs", "hashtags")
    op.drop_column("content_creation_jobs", "social_caption")
    op.drop_column("content_creation_jobs", "video_script")
