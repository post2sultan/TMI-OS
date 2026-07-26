
"""add evidence deduplication

Revision ID: d0a3b5c7e9f1
Revises: c9f2a4b6d8e0
Create Date: 2026-07-26
"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "d0a3b5c7e9f1"
down_revision: Union[str, Sequence[str], None] = "c9f2a4b6d8e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "campaign_documents",
        sa.Column("canonical_url", sa.Text(), server_default="", nullable=False),
    )
    op.add_column(
        "campaign_documents",
        sa.Column("content_hash", sa.String(length=64), server_default="", nullable=False),
    )
    op.add_column(
        "campaign_documents",
        sa.Column("duplicate_of_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "campaign_documents",
        sa.Column("similarity_score", sa.Float(), nullable=True),
    )
    op.create_foreign_key(
        "fk_campaign_documents_duplicate_of_id",
        "campaign_documents",
        "campaign_documents",
        ["duplicate_of_id"],
        ["id"],
        ondelete="SET NULL",
    )
    for column in ("canonical_url", "content_hash", "duplicate_of_id"):
        op.create_index(
            f"ix_campaign_documents_{column}",
            "campaign_documents",
            [column],
            unique=False,
        )


def downgrade() -> None:
    for column in ("duplicate_of_id", "content_hash", "canonical_url"):
        op.drop_index(
            f"ix_campaign_documents_{column}",
            table_name="campaign_documents",
        )
    op.drop_constraint(
        "fk_campaign_documents_duplicate_of_id",
        "campaign_documents",
        type_="foreignkey",
    )
    for column in (
        "similarity_score",
        "duplicate_of_id",
        "content_hash",
        "canonical_url",
    ):
        op.drop_column("campaign_documents", column)
