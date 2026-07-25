import logging
from dataclasses import dataclass, field
from time import perf_counter

from app.models.campaign_source import CampaignSource
from app.services.discovery.providers.base import DiscoveryProvider
from app.services.discovery.providers.google_news import (
    google_news_provider,
)
from app.services.discovery.providers.searxng import (
    searxng_provider,
)
from app.services.url_normalizer import normalize_url

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ProviderExecution:
    provider: str
    status: str
    results: int
    duration_ms: int
    error: str = ""


@dataclass(slots=True)
class DiscoveryManagerResult:
    campaigns: list[CampaignSource] = field(
        default_factory=list
    )
    providers: list[ProviderExecution] = field(
        default_factory=list
    )


class DiscoveryManager:
    def __init__(
        self,
        providers: list[DiscoveryProvider] | None = None,
    ) -> None:
        self.providers = sorted(
            providers or [],
            key=lambda provider: provider.priority,
        )

    def register(
        self,
        provider: DiscoveryProvider,
    ) -> None:
        self.providers.append(provider)
        self.providers.sort(
            key=lambda item: item.priority
        )

    def search_with_report(
        self,
        query: str,
        limit_per_provider: int = 20,
        total_limit: int = 50,
    ) -> DiscoveryManagerResult:
        normalized_query = query.strip()

        if not normalized_query:
            return DiscoveryManagerResult()

        campaigns: list[CampaignSource] = []
        executions: list[ProviderExecution] = []
        seen_urls: set[str] = set()

        for provider in self.providers:
            started = perf_counter()

            try:
                results = provider.search(
                    query=normalized_query,
                    limit=limit_per_provider,
                )

                duration_ms = int(
                    (perf_counter() - started)
                    * 1000
                )

                executions.append(
                    ProviderExecution(
                        provider=provider.name,
                        status="SUCCESS",
                        results=len(results),
                        duration_ms=duration_ms,
                    )
                )

                for campaign in results:
                    normalized_url = normalize_url(
                        campaign.url
                    )

                    if (
                        not normalized_url
                        or normalized_url in seen_urls
                    ):
                        continue

                    seen_urls.add(normalized_url)

                    campaigns.append(
                        campaign.model_copy(
                            update={
                                "url": normalized_url
                            }
                        )
                    )

                    if len(campaigns) >= total_limit:
                        return DiscoveryManagerResult(
                            campaigns=campaigns,
                            providers=executions,
                        )

            except Exception as error:
                duration_ms = int(
                    (perf_counter() - started)
                    * 1000
                )

                logger.exception(
                    "Discovery provider %s failed",
                    provider.name,
                )

                executions.append(
                    ProviderExecution(
                        provider=provider.name,
                        status="FAILED",
                        results=0,
                        duration_ms=duration_ms,
                        error=str(error)[:500],
                    )
                )

        return DiscoveryManagerResult(
            campaigns=campaigns,
            providers=executions,
        )

    def search(
        self,
        query: str,
    ) -> list[CampaignSource]:
        return self.search_with_report(
            query=query
        ).campaigns


discovery_manager = DiscoveryManager(
    providers=[
        searxng_provider,
        google_news_provider,
    ]
)
