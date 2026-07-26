"""upgrade analysis persistence schema

Revision ID: 63aec4ed04ac
Revises: ea59eaa9f6c1
Create Date: 2026-07-20 19:25:05.136340
"""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "63aec4ed04ac"
down_revision: Union[str, Sequence[str], None] = "ea59eaa9f6c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade the legacy analysis schema without losing existing rows."""

    op.add_column(
        "analyses",
        sa.Column(
            "total_score",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "framework_name",
            sa.String(length=100),
            nullable=False,
            server_default="The Mi'yar Index",
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "framework_version",
            sa.String(length=30),
            nullable=False,
            server_default="1.0",
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "constitution_version",
            sa.String(length=30),
            nullable=False,
            server_default="1",
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "model_name",
            sa.String(length=100),
            nullable=False,
            server_default="",
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "summary",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "dimensions",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    # Preserve compatible legacy values before removing old columns.
    op.execute(
        """
        UPDATE analyses
        SET
            total_score = score::double precision,
            model_name = model,
            framework_version = prompt_version
        """
    )

    op.drop_column("analyses", "data")
    op.drop_column("analyses", "model")
    op.drop_column("analyses", "prompt_version")
    op.drop_column("analyses", "score")
    op.drop_column("analyses", "insight")
    op.drop_column("analyses", "impact")

    # Remove temporary database defaults.
    # Application-level defaults remain defined in the ORM model.
    op.alter_column(
        "analyses",
        "total_score",
        server_default=None,
    )

    op.alter_column(
        "analyses",
        "confidence",
        server_default=None,
    )

    op.alter_column(
        "analyses",
        "framework_name",
        server_default=None,
    )

    op.alter_column(
        "analyses",
        "framework_version",
        server_default=None,
    )

    op.alter_column(
        "analyses",
        "constitution_version",
        server_default=None,
    )

    op.alter_column(
        "analyses",
        "model_name",
        server_default=None,
    )

    op.alter_column(
        "analyses",
        "summary",
        server_default=None,
    )

    op.alter_column(
        "analyses",
        "dimensions",
        server_default=None,
    )


def downgrade() -> None:
    """Restore the legacy analysis schema."""

    op.add_column(
        "analyses",
        sa.Column(
            "data",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "insight",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "impact",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "score",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "model",
            sa.String(length=100),
            nullable=False,
            server_default="",
        ),
    )

    op.add_column(
        "analyses",
        sa.Column(
            "prompt_version",
            sa.String(length=30),
            nullable=False,
            server_default="1.0",
        ),
    )

    op.execute(
        """
        UPDATE analyses
        SET
            score = ROUND(total_score)::integer,
            model = model_name,
            prompt_version = framework_version
        """
    )

    op.drop_column("analyses", "dimensions")
    op.drop_column("analyses", "summary")
    op.drop_column("analyses", "model_name")
    op.drop_column("analyses", "constitution_version")
    op.drop_column("analyses", "framework_version")
    op.drop_column("analyses", "framework_name")
    op.drop_column("analyses", "confidence")
    op.drop_column("analyses", "total_score")