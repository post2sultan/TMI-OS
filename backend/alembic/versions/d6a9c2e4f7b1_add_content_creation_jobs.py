"""add content creation jobs

Revision ID: d6a9c2e4f7b1
Revises: c5f8a1d3e6b9
Create Date: 2026-07-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d6a9c2e4f7b1"
down_revision: Union[str, Sequence[str], None] = "c5f8a1d3e6b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_creation_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="queued",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["analyses.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_id", name="uq_content_jobs_analysis"),
    )
    op.create_index(
        "ix_content_creation_jobs_campaign_id",
        "content_creation_jobs",
        ["campaign_id"],
    )
    op.create_index(
        "ix_content_creation_jobs_analysis_id",
        "content_creation_jobs",
        ["analysis_id"],
    )
    op.create_index(
        "ix_content_creation_jobs_status",
        "content_creation_jobs",
        ["status"],
    )
    op.execute(
        """
        INSERT INTO content_creation_jobs (campaign_id, analysis_id, status)
        SELECT a.campaign_id, a.id,
               CASE WHEN c.status = 'published' THEN 'published' ELSE 'queued' END
        FROM analyses a
        JOIN campaigns c ON c.id = a.campaign_id
        WHERE a.review_status = 'approved'
          AND a.id = (
              SELECT MAX(latest.id)
              FROM analyses latest
              WHERE latest.campaign_id = a.campaign_id
          )
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_content_creation_jobs_status",
        table_name="content_creation_jobs",
    )
    op.drop_index(
        "ix_content_creation_jobs_analysis_id",
        table_name="content_creation_jobs",
    )
    op.drop_index(
        "ix_content_creation_jobs_campaign_id",
        table_name="content_creation_jobs",
    )
    op.drop_table("content_creation_jobs")
