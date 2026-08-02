"""add youtube publish state

Revision ID: c1d2e3f4a5b6
Revises: b0e4a6c8d2f5
"""

from alembic import op
import sqlalchemy as sa

revision = "c1d2e3f4a5b6"
down_revision = "b0e4a6c8d2f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content_creation_jobs", sa.Column("youtube_status", sa.String(30), nullable=False, server_default="not_queued"))
    op.add_column("content_creation_jobs", sa.Column("youtube_video_id", sa.String(64), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("youtube_url", sa.Text(), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("youtube_error", sa.Text(), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("youtube_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("content_creation_jobs", sa.Column("youtube_requested_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for name in ("youtube_requested_at", "youtube_attempts", "youtube_error", "youtube_url", "youtube_video_id", "youtube_status"):
        op.drop_column("content_creation_jobs", name)
