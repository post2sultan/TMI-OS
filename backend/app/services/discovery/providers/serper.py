import httpx

from app.core.settings import settings
from app.models.campaign_source import CampaignSource
from app.services.discovery.providers.base import DiscoveryProvider


class SerperProvider(DiscoveryProvider):

    def search(
        self,
        query: str
    ) -> list[CampaignSource]:

        response = httpx.post(
            settings.SERPER_URL,
            headers={
                "X-API-KEY": settings.serper_api_key_value,
                "Content-Type": "application/json"
            },
            json={
                "q": query,
                "num": 10
            },
            timeout=settings.SERPER_TIMEOUT
        )

        response.raise_for_status()

        payload = response.json()

        campaigns: list[CampaignSource] = []

        for result in payload.get("organic", []):

            campaigns.append(
                CampaignSource(
                    title=result.get("title", ""),
                    url=result.get("link", ""),
                    source="Serper",
                    description=result.get("snippet", ""),
                    content=""
                )
            )

        return campaigns


serper_provider = SerperProvider()