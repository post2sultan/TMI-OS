import logging
from urllib.parse import quote_plus

import feedparser

from app.models.campaign_source import CampaignSource
from app.services.discovery.providers.base import DiscoveryProvider

logger = logging.getLogger(__name__)


class GoogleNewsProvider(DiscoveryProvider):
    name = "Google News RSS"
    priority = 20

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[CampaignSource]:
        normalized_query = query.strip()

        if not normalized_query:
            return []

        encoded_query = quote_plus(normalized_query)

        feed_url = (
            "https://news.google.com/rss/search"
            f"?q={encoded_query}"
            "&hl=en-SA"
            "&gl=SA"
            "&ceid=SA:en"
        )

        feed = feedparser.parse(
            feed_url,
            request_headers={
                "User-Agent": "TMI-OS/0.2",
            },
        )

        campaigns: list[CampaignSource] = []

        for entry in feed.entries:
            if len(campaigns) >= limit:
                break

            url = str(entry.get("link") or "").strip()

            if not url:
                continue

            source_data = entry.get("source") or {}
            publisher = str(
                source_data.get("title")
                if isinstance(source_data, dict)
                else ""
            ).strip()

            description = str(
                entry.get("summary")
                or entry.get("description")
                or ""
            ).strip()

            campaigns.append(
                CampaignSource(
                    title=str(
                        entry.get("title") or url
                    ).strip(),
                    url=url,
                    source=(
                        f"{self.name}: {publisher}"
                        if publisher
                        else self.name
                    ),
                    description=description,
                    content="",
                )
            )

        logger.info(
            "Google News RSS returned %s results for query=%r",
            len(campaigns),
            normalized_query,
        )

        return campaigns


google_news_provider = GoogleNewsProvider()
