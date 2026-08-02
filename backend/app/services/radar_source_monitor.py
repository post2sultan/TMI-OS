from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin
from xml.etree import ElementTree

import feedparser
import requests
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.campaign_source import CampaignSource
from app.models.radar_source import RadarSource
from app.services.radar_signal_service import radar_signal_service


@dataclass(slots=True)
class SourcePollResult:
    source_id: int
    status: str
    discovered: int = 0
    created: int = 0
    updated: int = 0
    error: str = ""


class RadarSourceMonitor:
    max_sources_per_run = 10
    max_items_per_source = 50

    @staticmethod
    def _tokens(query: str) -> set[str]:
        return {token.casefold() for token in query.split() if len(token.strip()) >= 3}

    def _matches(self, title: str, description: str, query: str) -> bool:
        tokens = self._tokens(query)
        text = f"{title} {description}".casefold()
        return not tokens or any(token in text for token in tokens)

    def collect_feed(self, source: RadarSource) -> list[CampaignSource]:
        response = requests.get(source.url, headers={"User-Agent": "TMI-OS/0.3"}, timeout=20)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if feed.bozo and not feed.entries:
            raise ValueError(f"Invalid feed: {feed.bozo_exception}")
        items = []
        for entry in feed.entries[: self.max_items_per_source]:
            url = str(entry.get("link") or "").strip()
            title = str(entry.get("title") or url).strip()
            description = str(entry.get("summary") or entry.get("description") or "").strip()
            if url and self._matches(title, description, source.query):
                items.append(CampaignSource(title=title, url=url, source=source.name, description=description, content=""))
        return items

    def collect_sitemap(self, source: RadarSource) -> list[CampaignSource]:
        response = requests.get(source.url, headers={"User-Agent": "TMI-OS/0.3"}, timeout=20)
        response.raise_for_status()
        items = []
        root = ElementTree.fromstring(response.content)
        locations = [node.text.strip() for node in root.findall(".//{*}loc") if node.text]
        for url in locations[: self.max_items_per_source]:
            title = str(url.rsplit("/", 1)[-1].replace("-", " ") or url).strip()
            if url and self._matches(title, "", source.query):
                items.append(CampaignSource(title=title, url=urljoin(source.url, url), source=source.name, description="", content=""))
        return items

    def collect(self, source: RadarSource) -> list[CampaignSource]:
        if source.source_type in {"rss", "atom"}:
            return self.collect_feed(source)
        if source.source_type == "sitemap":
            return self.collect_sitemap(source)
        raise ValueError(f"Unsupported source type: {source.source_type}")

    def run(self, database: Session, force: bool = False) -> list[SourcePollResult]:
        now = datetime.now(timezone.utc)
        query = select(RadarSource).where(RadarSource.enabled.is_(True))
        if not force:
            query = query.where(or_(RadarSource.next_poll_at.is_(None), RadarSource.next_poll_at <= now))
        sources = list(database.scalars(query.order_by(RadarSource.next_poll_at.asc().nullsfirst(), RadarSource.id).limit(self.max_sources_per_run)))
        results = []
        for source in sources:
            try:
                items = self.collect(source)
                persisted = radar_signal_service.persist(database, f"source:{source.name}", items)
                source.last_status = "healthy"
                source.last_error = ""
                source.last_results = len(items)
                results.append(SourcePollResult(source.id, "healthy", len(items), persisted.created, persisted.updated))
            except Exception as exc:
                database.rollback()
                source = database.get(RadarSource, source.id)
                source.last_status = "error"
                source.last_error = str(exc)[:1000]
                source.last_results = 0
                results.append(SourcePollResult(source.id, "error", error=source.last_error))
            source.last_polled_at = now
            source.next_poll_at = now + timedelta(minutes=source.poll_interval_minutes)
            database.commit()
        return results


radar_source_monitor = RadarSourceMonitor()
