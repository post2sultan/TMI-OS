from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campaign_cluster import CampaignCluster
from app.models.discovery_signal import DiscoverySignal
from app.models.radar_watchlist import RadarWatchlist
from app.models.radar_source import RadarSource
from app.repositories.discovery_run_repository import discovery_run_repository
from app.services.discovery_service import discovery_service
from app.services.radar_query_planner import QueryPlanInput, radar_query_planner
from app.services.radar_signal_service import radar_signal_service
from app.services.radar_source_monitor import radar_source_monitor
from app.services.url_normalizer import normalize_url


router = APIRouter(prefix="/radar", tags=["radar"])


class RadarDiscoveryRequest(BaseModel):
    prompt: str = ""
    watchlist_id: int | None = None


class WatchlistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    market: str = Field(default="Saudi Arabia", min_length=1, max_length=100)
    languages: list[str] = Field(default_factory=lambda: ["en", "ar"], max_length=4)
    brands: list[str] = Field(default_factory=list, max_length=50)
    competitors: list[str] = Field(default_factory=list, max_length=50)
    categories: list[str] = Field(default_factory=list, max_length=30)
    locations: list[str] = Field(default_factory=list, max_length=30)
    campaign_terms: list[str] = Field(default_factory=list, max_length=50)
    channels: list[str] = Field(default_factory=list, max_length=20)


class RadarSourceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source_type: str = Field(pattern="^(rss|atom|sitemap)$")
    url: str = Field(min_length=8, max_length=2000, pattern="^https?://")
    query: str = Field(default="", max_length=300)
    poll_interval_minutes: int = Field(default=60, ge=15, le=10080)


class MonitorRequest(BaseModel):
    force: bool = False


def _plan_input(request: RadarDiscoveryRequest, watchlist: RadarWatchlist | None) -> QueryPlanInput:
    if watchlist is None:
        return QueryPlanInput(brief=request.prompt)
    return QueryPlanInput(
        brief=request.prompt,
        market=watchlist.market,
        languages=watchlist.languages,
        brands=watchlist.brands,
        competitors=watchlist.competitors,
        categories=watchlist.categories,
        locations=watchlist.locations,
        campaign_terms=watchlist.campaign_terms,
        channels=watchlist.channels,
    )


def _watchlist_dict(watchlist: RadarWatchlist) -> dict:
    return {
        "id": watchlist.id,
        "name": watchlist.name,
        "market": watchlist.market,
        "languages": watchlist.languages,
        "brands": watchlist.brands,
        "competitors": watchlist.competitors,
        "categories": watchlist.categories,
        "locations": watchlist.locations,
        "campaign_terms": watchlist.campaign_terms,
        "channels": watchlist.channels,
        "active": watchlist.active,
        "created_at": watchlist.created_at,
        "updated_at": watchlist.updated_at,
    }


def _source_dict(source: RadarSource) -> dict:
    return {
        "id": source.id,
        "name": source.name,
        "source_type": source.source_type,
        "url": source.url,
        "query": source.query,
        "enabled": source.enabled,
        "poll_interval_minutes": source.poll_interval_minutes,
        "last_polled_at": source.last_polled_at,
        "next_poll_at": source.next_poll_at,
        "last_status": source.last_status,
        "last_error": source.last_error,
        "last_results": source.last_results,
    }


def _cluster_dict(cluster: CampaignCluster) -> dict:
    return {
        "id": cluster.id,
        "title": cluster.title,
        "normalized_title": cluster.normalized_title,
        "status": cluster.status,
        "signal_count": cluster.signal_count,
        "source_count": cluster.source_count,
        "confidence_score": cluster.confidence_score,
        "trend_score": cluster.trend_score,
        "matched_entities": cluster.matched_entities,
        "score_rationale": cluster.score_rationale,
        "score_version": cluster.score_version,
        "first_seen_at": cluster.first_seen_at,
        "last_seen_at": cluster.last_seen_at,
    }


@router.post("/discover", status_code=201)
def discover_signals(request: RadarDiscoveryRequest, database: Session = Depends(get_db)) -> dict:
    watchlist = None
    if request.watchlist_id is not None:
        watchlist = database.get(RadarWatchlist, request.watchlist_id)
        if watchlist is None or not watchlist.active:
            raise HTTPException(status_code=404, detail="Active Radar watchlist not found.")
    queries = radar_query_planner.plan(_plan_input(request, watchlist))
    if not queries:
        raise HTTPException(status_code=422, detail="Discovery brief or watchlist criteria are required.")

    qualified_by_url = {}
    discovered = rejected = 0
    rejection_reasons: dict[str, int] = {}
    for query in queries:
        report = discovery_service.discover_with_report(query)
        discovery_run_repository.persist_report(database, query, report.providers)
        discovered += report.discovered
        rejected += report.rejected
        for reason, count in report.rejection_reasons.items():
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + count
        for source in report.campaigns:
            key = normalize_url(source.url)
            if key:
                qualified_by_url.setdefault(key, source)

    label = request.prompt.strip() or f"watchlist:{watchlist.name}"
    sources = list(qualified_by_url.values())
    persisted = radar_signal_service.persist(database, label, sources)
    return {
        "query": label,
        "queries_executed": queries,
        "discovered": discovered,
        "qualified": len(sources),
        "rejected": rejected,
        "created": persisted.created,
        "skipped": persisted.updated,
        "rejection_reasons": rejection_reasons,
        "campaign_ids": [],
        "signal_ids": persisted.signal_ids,
        "cluster_ids": sorted(set(persisted.cluster_ids)),
    }


@router.post("/watchlists", status_code=201)
def create_watchlist(request: WatchlistRequest, database: Session = Depends(get_db)) -> dict:
    existing = database.scalar(select(RadarWatchlist).where(RadarWatchlist.name == request.name.strip()))
    if existing is not None:
        raise HTTPException(status_code=409, detail="A watchlist with this name already exists.")
    values = request.model_dump()
    values["name"] = request.name.strip()
    watchlist = RadarWatchlist(**values)
    database.add(watchlist)
    database.commit()
    database.refresh(watchlist)
    return _watchlist_dict(watchlist)


@router.get("/watchlists")
def list_watchlists(database: Session = Depends(get_db)) -> dict:
    items = list(database.scalars(select(RadarWatchlist).order_by(RadarWatchlist.name)))
    return {"items": [_watchlist_dict(item) for item in items], "total": len(items)}


@router.post("/sources", status_code=201)
def create_source(request: RadarSourceRequest, database: Session = Depends(get_db)) -> dict:
    existing = database.scalar(select(RadarSource).where((RadarSource.name == request.name.strip()) | (RadarSource.url == request.url.strip())))
    if existing is not None:
        raise HTTPException(status_code=409, detail="A Radar source with this name or URL already exists.")
    source = RadarSource(**request.model_dump())
    source.name = source.name.strip()
    source.url = source.url.strip()
    database.add(source)
    database.commit()
    database.refresh(source)
    return _source_dict(source)


@router.get("/sources")
def list_sources(database: Session = Depends(get_db)) -> dict:
    items = list(database.scalars(select(RadarSource).order_by(RadarSource.name)))
    return {"items": [_source_dict(item) for item in items], "total": len(items)}


@router.post("/monitor/run")
def run_monitor(request: MonitorRequest, database: Session = Depends(get_db)) -> dict:
    results = radar_source_monitor.run(database, force=request.force)
    return {
        "sources_polled": len(results),
        "healthy": sum(item.status == "healthy" for item in results),
        "failed": sum(item.status == "error" for item in results),
        "created": sum(item.created for item in results),
        "updated": sum(item.updated for item in results),
        "items": [asdict(item) for item in results],
        "campaign_ids": [],
    }


@router.get("/clusters")
def list_clusters(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    min_confidence: float = 0.0,
    sort: str = "recent",
    database: Session = Depends(get_db),
) -> dict:
    safe_limit = min(max(limit, 1), 200)
    safe_offset = max(offset, 0)
    query = select(CampaignCluster).where(CampaignCluster.confidence_score >= min(max(min_confidence, 0.0), 1.0))
    count_query = select(func.count(CampaignCluster.id)).where(CampaignCluster.confidence_score >= min(max(min_confidence, 0.0), 1.0))
    if status:
        query = query.where(CampaignCluster.status == status)
        count_query = count_query.where(CampaignCluster.status == status)
    order = (
        (CampaignCluster.trend_score.desc(), CampaignCluster.last_seen_at.desc())
        if sort == "trend"
        else (CampaignCluster.last_seen_at.desc(), CampaignCluster.id.desc())
    )
    items = list(database.scalars(query.order_by(*order).limit(safe_limit).offset(safe_offset)))
    total = database.scalar(count_query) or 0
    return {"items": [_cluster_dict(item) for item in items], "total": total, "limit": safe_limit, "offset": safe_offset}


@router.get("/clusters/{cluster_id}/signals")
def list_cluster_signals(cluster_id: int, database: Session = Depends(get_db)) -> dict:
    if database.get(CampaignCluster, cluster_id) is None:
        raise HTTPException(status_code=404, detail="Campaign cluster not found.")
    items = list(database.scalars(select(DiscoverySignal).where(DiscoverySignal.cluster_id == cluster_id).order_by(DiscoverySignal.last_seen_at.desc())))
    return {"items": items, "total": len(items)}
