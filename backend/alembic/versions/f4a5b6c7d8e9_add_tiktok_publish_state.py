"""add tiktok draft upload state

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
"""
from alembic import op
import sqlalchemy as sa

revision = "f4a5b6c7d8e9"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content_creation_jobs", sa.Column("tiktok_status", sa.String(30), nullable=False, server_default="not_queued"))
    op.add_column("content_creation_jobs", sa.Column("tiktok_publish_id", sa.String(128), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("tiktok_error", sa.Text(), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("tiktok_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("content_creation_jobs", sa.Column("tiktok_requested_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for name in ("tiktok_requested_at", "tiktok_attempts", "tiktok_error", "tiktok_publish_id", "tiktok_status"):
        op.drop_column("content_creation_jobs", name)
