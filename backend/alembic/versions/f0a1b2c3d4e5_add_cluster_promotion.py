"""add cluster promotion

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
"""
from alembic import op
import sqlalchemy as sa

revision = "f0a1b2c3d4e5"
down_revision = "e9f0a1b2c3d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("campaign_clusters", sa.Column("promoted_campaign_id", sa.Integer(), nullable=True))
    op.add_column("campaign_clusters", sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_campaign_clusters_promoted_campaign_id", "campaign_clusters", ["promoted_campaign_id"])
    op.create_foreign_key("fk_campaign_clusters_promoted_campaign_id", "campaign_clusters", "campaigns", ["promoted_campaign_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_campaign_clusters_promoted_campaign_id", "campaign_clusters", type_="foreignkey")
    op.drop_constraint("uq_campaign_clusters_promoted_campaign_id", "campaign_clusters", type_="unique")
    op.drop_column("campaign_clusters", "promoted_at")
    op.drop_column("campaign_clusters", "promoted_campaign_id")
