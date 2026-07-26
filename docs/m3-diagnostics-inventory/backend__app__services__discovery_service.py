import re
from dataclasses import dataclass, field
from html import unescape
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.models.campaign_source import CampaignSource
from app.services.discovery.manager import (
    DiscoveryManager,
    ProviderExecution,
    discovery_manager,
)


@dataclass(slots=True)
class DiscoveryReport:
    query: str
    discovered: int
    campaigns: list[CampaignSource] = field(
        default_factory=list
    )
    rejected: int = 0
    rejection_reasons: dict[str, int] = field(
        default_factory=dict
    )
    providers: list[ProviderExecution] = field(
        default_factory=list
    )


class DiscoveryService:
    BLOCKED_EXTENSIONS = {
        ".7z",
        ".avi",
        ".css",
        ".csv",
        ".doc",
        ".docx",
        ".exe",
        ".gif",
        ".gz",
        ".ico",
        ".jpeg",
        ".jpg",
        ".js",
        ".json",
        ".m4a",
        ".mov",
        ".mp3",
        ".mp4",
        ".mpeg",
        ".pdf",
        ".png",
        ".ppt",
        ".pptx",
        ".rar",
        ".svg",
        ".tar",
        ".txt",
        ".wav",
        ".webp",
        ".xls",
        ".xlsx",
        ".xml",
        ".zip",
    }

    BLOCKED_HOSTS = {
        "accounts.google.com",
        "docs.google.com",
        "drive.google.com",
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "login.microsoftonline.com",
        "pinterest.com",
        "tiktok.com",
        "x.com",
    }

    CAMPAIGN_TERMS = {
        "activation",
        "advert",
        "advertising",
        "brand",
        "campaign",
        "collaboration",
        "commercial",
        "creative",
        "experience",
        "launch",
        "marketing",
        "media",
        "promotion",
        "rebrand",
        "sponsorship",
    }

    SAUDI_TERMS = {
        "arabia",
        "jeddah",
        "ksa",
        "riyadh",
        "saudi",
    }

    def __init__(
        self,
        manager: DiscoveryManager,
    ) -> None:
        self.manager = manager

    @staticmethod
    def _clean_html(value: str) -> str:
        if not value:
            return ""

        text = BeautifulSoup(
            unescape(value),
            "html.parser",
        ).get_text(" ", strip=True)

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    @classmethod
    def _host_is_blocked(
        cls,
        url: str,
    ) -> bool:
        hostname = (
            urlparse(url).hostname or ""
        ).lower()

        return any(
            hostname == blocked_host
            or hostname.endswith(
                f".{blocked_host}"
            )
            for blocked_host
            in cls.BLOCKED_HOSTS
        )

    @classmethod
    def _extension_is_blocked(
        cls,
        url: str,
    ) -> bool:
        path = urlparse(url).path.lower()

        return any(
            path.endswith(extension)
            for extension
            in cls.BLOCKED_EXTENSIONS
        )

    @classmethod
    def _is_relevant(
        cls,
        query: str,
        campaign: CampaignSource,
    ) -> bool:
        searchable = " ".join(
            [
                query,
                campaign.title,
                campaign.description,
                campaign.content,
            ]
        ).casefold()

        campaign_match = any(
            term in searchable
            for term in cls.CAMPAIGN_TERMS
        )

        saudi_match = any(
            term in searchable
            for term in cls.SAUDI_TERMS
        )

        return campaign_match or saudi_match

    def discover_with_report(
        self,
        query: str,
    ) -> DiscoveryReport:
        manager_result = (
            self.manager.search_with_report(
                query=query,
                limit_per_provider=25,
                total_limit=60,
            )
        )

        rejection_reasons: dict[str, int] = {}
        qualified: list[CampaignSource] = []

        def reject(reason: str) -> None:
            rejection_reasons[reason] = (
                rejection_reasons.get(
                    reason,
                    0,
                )
                + 1
            )

        for campaign in manager_result.campaigns:
            url = campaign.url.strip()

            if not url:
                reject("missing_url")
                continue

            if self._host_is_blocked(url):
                reject("blocked_host")
                continue

            if self._extension_is_blocked(url):
                reject("blocked_file_type")
                continue

            cleaned_title = self._clean_html(
                campaign.title
            )

            cleaned_description = (
                self._clean_html(
                    campaign.description
                )
            )

            cleaned_content = self._clean_html(
                campaign.content
            )

            cleaned_campaign = (
                campaign.model_copy(
                    update={
                        "title": (
                            cleaned_title
                            or url
                        )[:500],
                        "description": (
                            cleaned_description
                        ),
                        "content": cleaned_content,
                    }
                )
            )

            if not self._is_relevant(
                query=query,
                campaign=cleaned_campaign,
            ):
                reject("low_relevance")
                continue

            qualified.append(
                cleaned_campaign
            )

        rejected = sum(
            rejection_reasons.values()
        )

        return DiscoveryReport(
            query=query,
            discovered=len(
                manager_result.campaigns
            ),
            campaigns=qualified,
            rejected=rejected,
            rejection_reasons=rejection_reasons,
            providers=manager_result.providers,
        )

    def discover(
        self,
        query: str,
    ) -> list[CampaignSource]:
        return self.discover_with_report(
            query=query
        ).campaigns


discovery_service = DiscoveryService(
    manager=discovery_manager
)
