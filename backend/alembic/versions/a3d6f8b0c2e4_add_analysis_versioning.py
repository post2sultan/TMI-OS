"""add analysis versioning

Revision ID: a3d6f8b0c2e4
Revises: f2c5d7e9a1b3
Create Date: 2026-07-26
"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "a3d6f8b0c2e4"
down_revision: Union[str, Sequence[str], None] = "f2c5d7e9a1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("analysis_version", sa.Integer()))
    op.add_column("analyses", sa.Column("previous_analysis_id", sa.Integer()))
    op.add_column(
        "analyses",
        sa.Column("prompt_version", sa.String(length=50)),
    )
    op.add_column(
        "analyses",
        sa.Column("model_version", sa.String(length=100)),
    )
    op.add_column("analyses", sa.Column("reviewer_notes", sa.Text()))
    op.execute(
        """
        WITH versions AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY campaign_id ORDER BY created_at, id
                   ) AS version,
                   LAG(id) OVER (
                       PARTITION BY campaign_id ORDER BY created_at, id
                   ) AS previous_id
            FROM analyses
        )
        UPDATE analyses
        SET analysis_version = versions.version,
            previous_analysis_id = versions.previous_id,
            prompt_version = 'legacy',
            model_version = analyses.model_name,
            reviewer_notes = analyses.review_reason
        FROM versions
        WHERE analyses.id = versions.id
        """
    )
    op.alter_column("analyses", "analysis_version", nullable=False)
    op.alter_column("analyses", "prompt_version", nullable=False)
    op.alter_column("analyses", "model_version", nullable=False)
    op.create_foreign_key(
        "fk_analyses_previous_analysis_id",
        "analyses",
        "analyses",
        ["previous_analysis_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_analyses_previous_analysis_id",
        "analyses",
        ["previous_analysis_id"],
    )
    op.create_unique_constraint(
        "uq_analyses_campaign_version",
        "analyses",
        ["campaign_id", "analysis_version"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_analyses_campaign_version",
        "analyses",
        type_="unique",
    )
    op.drop_index("ix_analyses_previous_analysis_id", table_name="analyses")
    op.drop_constraint(
        "fk_analyses_previous_analysis_id",
        "analyses",
        type_="foreignkey",
    )
    op.drop_column("analyses", "reviewer_notes")
    op.drop_column("analyses", "model_version")
    op.drop_column("analyses", "prompt_version")
    op.drop_column("analyses", "previous_analysis_id")
    op.drop_column("analyses", "analysis_version")

