from urllib.parse import urlparse

from app.models.campaign_source import CampaignSource
from app.services.discovery.providers.base import DiscoveryProvider
from app.services.discovery.providers.searxng import SearxngProvider


class CompanySiteProvider(DiscoveryProvider):
    name = "Company Site Search"
    priority = 40

    def __init__(
        self,
        domains: list[str] | None = None,
    ) -> None:
        self.domains = [
            domain.strip().lower()
            for domain in (domains or [])
            if domain and domain.strip()
        ]

        self.search_provider = SearxngProvider()

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[CampaignSource]:
        if not self.domains:
            return []

        campaigns: list[CampaignSource] = []

        per_domain_limit = max(
            1,
            limit // len(self.domains),
        )

        for domain in self.domains:
            provider_results = (
                self.search_provider.search(
                    query=f"site:{domain} {query}",
                    limit=per_domain_limit,
                )
            )

            for result in provider_results:
                hostname = (
                    urlparse(result.url)
                    .hostname
                    or ""
                ).lower()

                if not (
                    hostname == domain
                    or hostname.endswith(
                        f".{domain}"
                    )
                ):
                    continue

                campaigns.append(
                    result.model_copy(
                        update={
                            "source": (
                                f"{self.name}: "
                                f"{domain}"
                            )
                        }
                    )
                )

                if len(campaigns) >= limit:
                    return campaigns

        return campaigns
