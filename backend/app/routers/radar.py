from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campaign_cluster import CampaignCluster
from app.models.discovery_signal import DiscoverySignal
from app.repositories.discovery_run_repository import discovery_run_repository
from app.services.discovery_service import discovery_service
from app.services.radar_signal_service import radar_signal_service


router = APIRouter(prefix="/radar", tags=["radar"])


class RadarDiscoveryRequest(BaseModel):
    prompt: str


@router.post("/discover", status_code=201)
def discover_signals(
    request: RadarDiscoveryRequest,
    database: Session = Depends(get_db),
) -> dict:
    query = request.prompt.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Discovery query cannot be empty.")
    report = discovery_service.discover_with_report(query)
    discovery_run_repository.persist_report(database, query, report.providers)
    persisted = radar_signal_service.persist(database, query, report.campaigns)
    return {
        "query": query,
        "discovered": report.discovered,
        "qualified": len(report.campaigns),
        "rejected": report.rejected,
        "created": persisted.created,
        "skipped": persisted.updated,
        "rejection_reasons": report.rejection_reasons,
        "campaign_ids": [],
        "signal_ids": persisted.signal_ids,
        "cluster_ids": sorted(set(persisted.cluster_ids)),
    }


@router.get("/clusters")
def list_clusters(
    limit: int = 50,
    offset: int = 0,
    database: Session = Depends(get_db),
) -> dict:
    safe_limit = min(max(limit, 1), 200)
    safe_offset = max(offset, 0)
    items = list(
        database.scalars(
            select(CampaignCluster)
            .order_by(CampaignCluster.last_seen_at.desc(), CampaignCluster.id.desc())
            .limit(safe_limit)
            .offset(safe_offset)
        )
    )
    total = database.scalar(select(func.count(CampaignCluster.id))) or 0
    return {"items": items, "total": total, "limit": safe_limit, "offset": safe_offset}


@router.get("/clusters/{cluster_id}/signals")
def list_cluster_signals(
    cluster_id: int,
    database: Session = Depends(get_db),
) -> dict:
    cluster = database.get(CampaignCluster, cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail="Campaign cluster not found.")
    items = list(
        database.scalars(
            select(DiscoverySignal)
            .where(DiscoverySignal.cluster_id == cluster_id)
            .order_by(DiscoverySignal.last_seen_at.desc())
        )
    )
    return {"items": items, "total": len(items)}

