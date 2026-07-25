"""add campaign fingerprint

Revision ID: 55f03f0eafa4
Revises: 63aec4ed04ac
Create Date: 2026-07-22
"""

import hashlib
import re
import unicodedata
from typing import Sequence
from typing import Union
from urllib.parse import urlsplit

import sqlalchemy as sa
from alembic import op


revision: str = "55f03f0eafa4"
down_revision: Union[str, Sequence[str], None] = "63aec4ed04ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = unicodedata.normalize("NFKC", value)
    value = value.lower().strip()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def get_domain(url: str | None) -> str:
    if not url:
        return ""

    raw_url = url.strip()

    if "://" not in raw_url:
        raw_url = f"https://{raw_url}"

    parsed = urlsplit(raw_url)
    hostname = (parsed.hostname or "").lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    return hostname


def generate_fingerprint(
    title: str | None,
    url: str | None,
) -> str:
    normalized_title = normalize_text(title)
    normalized_domain = get_domain(url)

    fingerprint_source = f"{normalized_title}|{normalized_domain}"

    return hashlib.sha256(
        fingerprint_source.encode("utf-8")
    ).hexdigest()


def generate_collision_fingerprint(
    fingerprint: str,
    campaign_id: int,
) -> str:
    """
    Preserve existing duplicate records while ensuring that every
    existing database row receives a unique fingerprint.
    """
    collision_source = f"{fingerprint}|existing-record|{campaign_id}"

    return hashlib.sha256(
        collision_source.encode("utf-8")
    ).hexdigest()


def upgrade() -> None:
    # Add the column as nullable first because existing rows do not yet
    # have fingerprint values.
    op.add_column(
        "campaigns",
        sa.Column(
            "fingerprint",
            sa.String(length=64),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    campaigns = connection.execute(
        sa.text(
            """
            SELECT id, title, url
            FROM campaigns
            ORDER BY id ASC
            """
        )
    ).mappings()

    used_fingerprints: set[str] = set()

    for campaign in campaigns:
        campaign_id = campaign["id"]

        fingerprint = generate_fingerprint(
            title=campaign["title"],
            url=campaign["url"],
        )

        # Existing duplicate campaigns may generate the same fingerprint.
        # Keep the first record canonical and assign collision-safe hashes
        # to later historical duplicates.
        if fingerprint in used_fingerprints:
            fingerprint = generate_collision_fingerprint(
                fingerprint=fingerprint,
                campaign_id=campaign_id,
            )

        used_fingerprints.add(fingerprint)

        connection.execute(
            sa.text(
                """
                UPDATE campaigns
                SET fingerprint = :fingerprint
                WHERE id = :campaign_id
                """
            ),
            {
                "fingerprint": fingerprint,
                "campaign_id": campaign_id,
            },
        )

    # Every existing campaign now has a fingerprint.
    op.alter_column(
        "campaigns",
        "fingerprint",
        existing_type=sa.String(length=64),
        nullable=False,
    )

    op.create_index(
        "ix_campaigns_fingerprint",
        "campaigns",
        ["fingerprint"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_campaigns_fingerprint",
        table_name="campaigns",
    )

    op.drop_column(
        "campaigns",
        "fingerprint",
    )