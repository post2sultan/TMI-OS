"""add social export fields

Revision ID: b0e4a6c8d2f5
Revises: a9d3f5b7c1e4
"""

from alembic import op
import sqlalchemy as sa

revision = "b0e4a6c8d2f5"
down_revision = "a9d3f5b7c1e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_creation_jobs",
        sa.Column(
            "social_export_url", sa.Text(), nullable=False, server_default=""
        ),
    )
    op.add_column(
        "content_creation_jobs",
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_creation_jobs", "exported_at")
    op.drop_column("content_creation_jobs", "social_export_url")
