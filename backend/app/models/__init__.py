"""
TMI ORM Models

Importing this package registers every SQLAlchemy model with Base.metadata.
Alembic relies on these imports during autogeneration.
"""

from app.models.campaign import Campaign
from app.models.campaign_document import CampaignDocument
from app.models.analysis import Analysis
from app.models.analysis_run import AnalysisRun
from app.models.evidence import Evidence
from app.models.discovery_run import DiscoveryRun
from app.models.provider import Provider
from app.models.audit_event import AuditEvent
from app.models.content_creation_job import ContentCreationJob

__all__ = [
    "Campaign",
    "CampaignDocument",
    "Analysis",
    "AnalysisRun",
    "Evidence",
    "DiscoveryRun",
    "Provider",
    "AuditEvent",
    "ContentCreationJob",
]
