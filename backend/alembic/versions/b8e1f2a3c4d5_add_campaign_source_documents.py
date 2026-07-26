"""add campaign source documents

Revision ID: b8e1f2a3c4d5
Revises: 9c7b2d4e6f80
Create Date: 2026-07-26
"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "b8e1f2a3c4d5"
down_revision: Union[str, Sequence[str], None] = "9c7b2d4e6f80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaign_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=30), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
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
        sa.UniqueConstraint(
            "campaign_id",
            "source_url",
            name="uq_campaign_documents_campaign_source_url",
        ),
    )
    op.create_index(
        "ix_campaign_documents_campaign_id",
        "campaign_documents",
        ["campaign_id"],
        unique=False,
    )
    op.create_index(
        "ix_campaign_documents_document_type",
        "campaign_documents",
        ["document_type"],
        unique=False,
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO campaign_documents (
                campaign_id,
                document_type,
                source_url,
                title,
                content
            )
            SELECT
                id,
                'web_page',
                url,
                title,
                content
            FROM campaigns
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_campaign_documents_document_type",
        table_name="campaign_documents",
    )
    op.drop_index(
        "ix_campaign_documents_campaign_id",
        table_name="campaign_documents",
    )
    op.drop_table("campaign_documents")
