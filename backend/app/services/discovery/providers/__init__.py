"""Free discovery providers used by TMI OS."""

from app.services.discovery.providers.base import DiscoveryProvider
from app.services.discovery.providers.google_news import (
    GoogleNewsProvider,
    google_news_provider,
)
from app.services.discovery.providers.rss import RSSProvider
from app.services.discovery.providers.searxng import (
    SearxngProvider,
    searxng_provider,
)

__all__ = [
    "DiscoveryProvider",
    "GoogleNewsProvider",
    "RSSProvider",
    "SearxngProvider",
    "google_news_provider",
    "searxng_provider",
]
