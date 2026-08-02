"""add linkedin video publish state

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
"""
from alembic import op
import sqlalchemy as sa

revision = "a5b6c7d8e9f0"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content_creation_jobs", sa.Column("linkedin_status", sa.String(30), nullable=False, server_default="not_queued"))
    op.add_column("content_creation_jobs", sa.Column("linkedin_post_urn", sa.String(160), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("linkedin_video_urn", sa.String(160), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("linkedin_error", sa.Text(), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("linkedin_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("content_creation_jobs", sa.Column("linkedin_requested_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for name in ("linkedin_requested_at", "linkedin_attempts", "linkedin_error", "linkedin_video_urn", "linkedin_post_urn", "linkedin_status"):
        op.drop_column("content_creation_jobs", name)
