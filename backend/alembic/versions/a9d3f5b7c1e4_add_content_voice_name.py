"""add content voice name

Revision ID: a9d3f5b7c1e4
Revises: f8c2e4a6b0d3
"""

from alembic import op
import sqlalchemy as sa

revision = "a9d3f5b7c1e4"
down_revision = "f8c2e4a6b0d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_creation_jobs",
        sa.Column(
            "voice_name",
            sa.String(length=50),
            nullable=False,
            server_default="af_heart",
        ),
    )


def downgrade() -> None:
    op.drop_column("content_creation_jobs", "voice_name")
