from abc import ABC, abstractmethod

from app.models.campaign_source import CampaignSource


class DiscoveryProvider(ABC):
    """Contract implemented by every free discovery provider."""

    name: str = "unknown"
    priority: int = 100

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[CampaignSource]:
        raise NotImplementedError
