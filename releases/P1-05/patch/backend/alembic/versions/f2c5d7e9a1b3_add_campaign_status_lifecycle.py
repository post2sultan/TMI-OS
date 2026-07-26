
"""add campaign status lifecycle

Revision ID: f2c5d7e9a1b3
Revises: e1b4c6d8f0a2
Create Date: 2026-07-26
"""

from typing import Sequence
from typing import Union

from alembic import op


revision: str = "f2c5d7e9a1b3"
down_revision: Union[str, Sequence[str], None] = "e1b4c6d8f0a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_campaigns_status_lifecycle",
        "campaigns",
        "status IN ("
        "'discovered','shortlisted','researching','ready_for_analysis',"
        "'analyzing','analyzed','needs_review','approved','rejected',"
        "'published','archived'"
        ")",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_campaigns_status_lifecycle",
        "campaigns",
        type_="check",
    )
