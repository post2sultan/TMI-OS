import hashlib
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.campaign_cluster import CampaignCluster
from app.models.campaign_source import CampaignSource
from app.models.discovery_signal import DiscoverySignal
from app.services.url_normalizer import normalize_url


def normalize_signal_title(title: str) -> str:
    return re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", title.casefold()).strip()


def generate_cluster_key(title: str) -> str:
    normalized = normalize_signal_title(title)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def campaign_candidate_confidence(signal_count: int, source_count: int) -> float:
    value = 0.35 + min(signal_count, 3) * 0.15 + min(source_count, 3) * 0.10
    return round(min(value, 0.95), 2)


@dataclass(slots=True)
class SignalPersistenceResult:
    created: int = 0
    updated: int = 0
    cluster_ids: list[int] = field(default_factory=list)
    signal_ids: list[int] = field(default_factory=list)


class RadarSignalService:
    def persist(
        self,
        database: Session,
        query: str,
        sources: list[CampaignSource],
    ) -> SignalPersistenceResult:
        result = SignalPersistenceResult()
        affected_clusters: set[int] = set()

        for source in sources:
            normalized_url = normalize_url(source.url.strip())
            title = source.title.strip() or normalized_url
            normalized_title = normalize_signal_title(title)
            if not normalized_url or not normalized_title:
                continue

            existing = database.scalar(
                select(DiscoverySignal).where(
                    DiscoverySignal.normalized_url == normalized_url
                )
            )
            if existing is not None:
                existing.detection_count += 1
                existing.query = query
                existing.last_seen_at = func.now()
                affected_clusters.add(existing.cluster_id)
                result.updated += 1
                continue

            cluster_key = generate_cluster_key(title)
            cluster = database.scalar(
                select(CampaignCluster).where(CampaignCluster.cluster_key == cluster_key)
            )
            if cluster is None:
                cluster = CampaignCluster(
                    cluster_key=cluster_key,
                    title=title[:500],
                    normalized_title=normalized_title,
                )
                database.add(cluster)
                database.flush()

            hostname = (urlsplit(normalized_url).hostname or "unknown").lower()
            signal = DiscoverySignal(
                cluster_id=cluster.id,
                query=query,
                title=title[:500],
                url=source.url.strip(),
                normalized_url=normalized_url,
                provider=(source.source or "unknown")[:100],
                source_domain=hostname[:255],
                description=source.description or "",
                content=source.content or "",
            )
            database.add(signal)
            database.flush()
            affected_clusters.add(cluster.id)
            result.created += 1
            result.signal_ids.append(signal.id)

        for cluster_id in affected_clusters:
            cluster = database.get(CampaignCluster, cluster_id)
            if cluster is None:
                continue
            signal_count = database.scalar(
                select(func.count(DiscoverySignal.id)).where(
                    DiscoverySignal.cluster_id == cluster_id
                )
            ) or 0
            source_count = database.scalar(
                select(func.count(func.distinct(DiscoverySignal.source_domain))).where(
                    DiscoverySignal.cluster_id == cluster_id
                )
            ) or 0
            cluster.signal_count = int(signal_count)
            cluster.source_count = int(source_count)
            cluster.confidence_score = campaign_candidate_confidence(
                cluster.signal_count, cluster.source_count
            )
            cluster.status = (
                "corroborated"
                if cluster.source_count >= 2 or cluster.signal_count >= 3
                else "candidate"
            )
            cluster.last_seen_at = func.now()
            result.cluster_ids.append(cluster_id)

        database.commit()
        return result


radar_signal_service = RadarSignalService()

