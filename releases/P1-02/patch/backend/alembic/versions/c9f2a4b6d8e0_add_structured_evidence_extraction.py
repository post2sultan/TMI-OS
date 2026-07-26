
"""add structured evidence extraction

Revision ID: c9f2a4b6d8e0
Revises: b8e1f2a3c4d5
Create Date: 2026-07-26
"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "c9f2a4b6d8e0"
down_revision: Union[str, Sequence[str], None] = "b8e1f2a3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "campaign_documents",
        "content",
        new_column_name="extracted_text",
    )
    op.add_column(
        "campaign_documents",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "campaign_documents",
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "campaign_documents",
        sa.Column("language", sa.String(length=20), server_default="", nullable=False),
    )
    op.add_column(
        "campaign_documents",
        sa.Column("brand", sa.String(length=255), server_default="", nullable=False),
    )
    op.add_column(
        "campaign_documents",
        sa.Column("media_assets", sa.JSON(), server_default="[]", nullable=False),
    )
    op.add_column(
        "campaign_documents",
        sa.Column(
            "extraction_status",
            sa.String(length=30),
            server_default="pending",
            nullable=False,
        ),
    )
    op.add_column(
        "campaign_documents",
        sa.Column(
            "extraction_method",
            sa.String(length=100),
            server_default="",
            nullable=False,
        ),
    )
    op.create_index(
        "ix_campaign_documents_extraction_status",
        "campaign_documents",
        ["extraction_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_campaign_documents_extraction_status",
        table_name="campaign_documents",
    )
    for column in (
        "extraction_method",
        "extraction_status",
        "media_assets",
        "brand",
        "language",
        "retrieved_at",
        "published_at",
    ):
        op.drop_column("campaign_documents", column)
    op.alter_column(
        "campaign_documents",
        "extracted_text",
        new_column_name="content",
    )
