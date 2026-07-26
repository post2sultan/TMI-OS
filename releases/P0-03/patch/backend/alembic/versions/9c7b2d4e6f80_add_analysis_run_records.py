"""add analysis run records

Revision ID: 9c7b2d4e6f80
Revises: 55f03f0eafa4
Create Date: 2026-07-26
"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "9c7b2d4e6f80"
down_revision: Union[str, Sequence[str], None] = "55f03f0eafa4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=False),
        sa.Column("validation_status", sa.String(length=30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("force", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_analysis_runs_campaign_id",
        "analysis_runs",
        ["campaign_id"],
        unique=False,
    )
    op.create_index(
        "ix_analysis_runs_validation_status",
        "analysis_runs",
        ["validation_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analysis_runs_validation_status",
        table_name="analysis_runs",
    )
    op.drop_index(
        "ix_analysis_runs_campaign_id",
        table_name="analysis_runs",
    )
    op.drop_table("analysis_runs")

