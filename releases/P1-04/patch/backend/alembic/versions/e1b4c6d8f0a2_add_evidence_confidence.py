
"""add evidence confidence

Revision ID: e1b4c6d8f0a2
Revises: d0a3b5c7e9f1
Create Date: 2026-07-26
"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "e1b4c6d8f0a2"
down_revision: Union[str, Sequence[str], None] = "d0a3b5c7e9f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "campaign_documents",
        sa.Column(
            "evidence_origin",
            sa.String(length=30),
            server_default="",
            nullable=False,
        ),
    )
    op.add_column(
        "campaign_documents",
        sa.Column(
            "confidence_score",
            sa.Float(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "campaign_documents",
        sa.Column(
            "evidence_representation",
            sa.String(length=20),
            server_default="",
            nullable=False,
        ),
    )
    op.add_column(
        "campaign_documents",
        sa.Column(
            "supporting_source",
            sa.Text(),
            server_default="",
            nullable=False,
        ),
    )


def downgrade() -> None:
    for column in (
        "supporting_source",
        "evidence_representation",
        "confidence_score",
        "evidence_origin",
    ):
        op.drop_column("campaign_documents", column)
