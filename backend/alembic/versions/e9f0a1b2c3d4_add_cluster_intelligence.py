"""add cluster intelligence

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
"""
from alembic import op
import sqlalchemy as sa

revision = "e9f0a1b2c3d4"
down_revision = "d8e9f0a1b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("campaign_clusters", sa.Column("trend_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("campaign_clusters", sa.Column("matched_entities", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("campaign_clusters", sa.Column("score_rationale", sa.Text(), nullable=False, server_default=""))
    op.add_column("campaign_clusters", sa.Column("score_version", sa.String(20), nullable=False, server_default="radar-07"))
    op.create_index("ix_campaign_clusters_trend_score", "campaign_clusters", ["trend_score"])


def downgrade() -> None:
    op.drop_index("ix_campaign_clusters_trend_score", table_name="campaign_clusters")
    op.drop_column("campaign_clusters", "score_version")
    op.drop_column("campaign_clusters", "score_rationale")
    op.drop_column("campaign_clusters", "matched_entities")
    op.drop_column("campaign_clusters", "trend_score")
