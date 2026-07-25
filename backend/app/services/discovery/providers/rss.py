import logging
from collections.abc import Iterable

import feedparser

from app.models.campaign_source import CampaignSource
from app.services.discovery.providers.base import DiscoveryProvider

logger = logging.getLogger(__name__)


class RSSProvider(DiscoveryProvider):
    name = "RSS"
    priority = 30

    def __init__(
        self,
        feeds: Iterable[str] | None = None,
    ) -> None:
        self.feeds = [
            feed.strip()
            for feed in (feeds or [])
            if feed and feed.strip()
        ]

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[CampaignSource]:
        if not self.feeds:
            return []

        query_tokens = {
            token.casefold()
            for token in query.split()
            if len(token.strip()) >= 3
        }

        campaigns: list[CampaignSource] = []

        for feed_url in self.feeds:
            feed = feedparser.parse(
                feed_url,
                request_headers={
                    "User-Agent": "TMI-OS/0.2",
                },
            )

            for entry in feed.entries:
                if len(campaigns) >= limit:
                    return campaigns

                title = str(
                    entry.get("title") or ""
                ).strip()

                description = str(
                    entry.get("summary")
                    or entry.get("description")
                    or ""
                ).strip()

                searchable = (
                    f"{title} {description}"
                ).casefold()

                if query_tokens and not any(
                    token in searchable
                    for token in query_tokens
                ):
                    continue

                url = str(
                    entry.get("link") or ""
                ).strip()

                if not url:
                    continue

                campaigns.append(
                    CampaignSource(
                        title=title or url,
                        url=url,
                        source=self.name,
                        description=description,
                        content="",
                    )
                )

        logger.info(
            "RSS returned %s results for query=%r",
            len(campaigns),
            query,
        )

        return campaigns
