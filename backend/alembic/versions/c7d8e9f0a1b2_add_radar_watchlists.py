"""add radar watchlists

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
"""
from alembic import op
import sqlalchemy as sa

revision = "c7d8e9f0a1b2"
down_revision = "b6c7d8e9f0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "radar_watchlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("market", sa.String(100), nullable=False, server_default="Saudi Arabia"),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("brands", sa.JSON(), nullable=False),
        sa.Column("competitors", sa.JSON(), nullable=False),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("locations", sa.JSON(), nullable=False),
        sa.Column("campaign_terms", sa.JSON(), nullable=False),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("radar_watchlists")
