"""add instagram publish state

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
"""
from alembic import op
import sqlalchemy as sa

revision = "d2e3f4a5b6c7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("content_creation_jobs", sa.Column("instagram_status", sa.String(30), nullable=False, server_default="not_queued"))
    op.add_column("content_creation_jobs", sa.Column("instagram_media_id", sa.String(64), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("instagram_url", sa.Text(), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("instagram_error", sa.Text(), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("instagram_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("content_creation_jobs", sa.Column("instagram_requested_at", sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    for name in ("instagram_requested_at", "instagram_attempts", "instagram_error", "instagram_url", "instagram_media_id", "instagram_status"):
        op.drop_column("content_creation_jobs", name)
