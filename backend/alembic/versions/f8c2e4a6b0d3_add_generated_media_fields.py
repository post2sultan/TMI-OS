"""add generated media fields

Revision ID: f8c2e4a6b0d3
Revises: e7b1d3f5a9c2
"""

from alembic import op
import sqlalchemy as sa

revision = "f8c2e4a6b0d3"
down_revision = "e7b1d3f5a9c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_creation_jobs",
        sa.Column("audio_url", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "content_creation_jobs",
        sa.Column("video_url", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "content_creation_jobs",
        sa.Column("media_generated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_creation_jobs", "media_generated_at")
    op.drop_column("content_creation_jobs", "video_url")
    op.drop_column("content_creation_jobs", "audio_url")
