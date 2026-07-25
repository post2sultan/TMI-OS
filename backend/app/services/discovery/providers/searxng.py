import logging
from typing import Any

import httpx

from app.core.settings import settings
from app.models.campaign_source import CampaignSource
from app.services.discovery.providers.base import DiscoveryProvider

logger = logging.getLogger(__name__)


class SearxngProvider(DiscoveryProvider):
    name = "SearXNG"
    priority = 10

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[CampaignSource]:
        normalized_query = query.strip()

        if not normalized_query:
            return []

        params = {
            "q": normalized_query,
            "format": "json",
            "language": "all",
            "safesearch": 1,
        }

        timeout = httpx.Timeout(
            timeout=float(settings.SEARXNG_TIMEOUT),
            connect=10.0,
        )

        headers = {
            "Accept": "application/json",
            "User-Agent": "TMI-OS/0.2",
        }

        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = client.get(
                f"{settings.SEARXNG_URL.rstrip('/')}/search",
                params=params,
            )

            response.raise_for_status()
            payload: dict[str, Any] = response.json()

        campaigns: list[CampaignSource] = []

        for result in payload.get("results", []):
            if len(campaigns) >= limit:
                break

            url = str(result.get("url") or "").strip()

            if not url:
                continue

            title = str(result.get("title") or "").strip()
            description = str(
                result.get("content")
                or result.get("description")
                or ""
            ).strip()

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
            "SearXNG returned %s results for query=%r",
            len(campaigns),
            normalized_query,
        )

        return campaigns


searxng_provider = SearxngProvider()
