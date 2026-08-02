"""add radar signals and campaign clusters

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
"""
from alembic import op
import sqlalchemy as sa

revision = "b6c7d8e9f0a1"
down_revision = "a5b6c7d8e9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaign_clusters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cluster_key", sa.String(64), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="candidate"),
        sa.Column("signal_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("cluster_key"),
    )
    op.create_index("ix_campaign_clusters_cluster_key", "campaign_clusters", ["cluster_key"], unique=True)
    op.create_index("ix_campaign_clusters_status", "campaign_clusters", ["status"])
    op.create_table(
        "discovery_signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cluster_id", sa.Integer(), sa.ForeignKey("campaign_clusters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("source_domain", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(30), nullable=False, server_default="clustered"),
        sa.Column("detection_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("normalized_url"),
    )
    for column in ("cluster_id", "provider", "source_domain", "status"):
        op.create_index(f"ix_discovery_signals_{column}", "discovery_signals", [column])


def downgrade() -> None:
    op.drop_table("discovery_signals")
    op.drop_table("campaign_clusters")

