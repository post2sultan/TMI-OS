"""
TMI ORM Models

Importing this package registers every SQLAlchemy model with Base.metadata.
Alembic relies on these imports during autogeneration.
"""

from app.models.campaign import Campaign
from app.models.analysis import Analysis
from app.models.evidence import Evidence
from app.models.discovery_run import DiscoveryRun
from app.models.provider import Provider

__all__ = [
    "Campaign",
    "Analysis",
    "Evidence",
    "DiscoveryRun",
    "Provider",
]