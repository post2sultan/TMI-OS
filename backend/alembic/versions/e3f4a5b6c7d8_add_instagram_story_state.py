"""add instagram story state

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
"""
from alembic import op
import sqlalchemy as sa
revision="e3f4a5b6c7d8"; down_revision="d2e3f4a5b6c7"; branch_labels=None; depends_on=None
def upgrade() -> None:
    op.add_column("content_creation_jobs", sa.Column("instagram_story_status", sa.String(30), nullable=False, server_default="not_queued"))
    op.add_column("content_creation_jobs", sa.Column("instagram_story_media_id", sa.String(64), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("instagram_story_error", sa.Text(), nullable=False, server_default=""))
    op.add_column("content_creation_jobs", sa.Column("instagram_story_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("content_creation_jobs", sa.Column("instagram_story_requested_at", sa.DateTime(timezone=True), nullable=True))
def downgrade() -> None:
    for name in ("instagram_story_requested_at","instagram_story_attempts","instagram_story_error","instagram_story_media_id","instagram_story_status"): op.drop_column("content_creation_jobs",name)
