import unittest

from app.models.campaign_source import CampaignSource
from app.services.discovery.manager import (
    _resolve_google_news_campaign,
)


class GoogleNewsLinkResolutionTests(unittest.TestCase):

    def test_high_confidence_title_match_uses_direct_url(self) -> None:
        direct = CampaignSource(
            title="Saudi Report 2026: From campaigns to ecosystems",
            url=(
                "https://campaignme.com/"
                "saudi-report-2026-from-campaigns-to-ecosystems/"
            ),
            source="SearXNG",
        )
        wrapped = CampaignSource(
            title=(
                "Saudi Report 2026: From campaigns to ecosystems "
                "- Campaign Middle East"
            ),
            url="https://news.google.com/rss/articles/example?oc=5",
            source="Google News RSS: Campaign Middle East",
        )

        resolved = _resolve_google_news_campaign(wrapped, [direct])

        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.url, direct.url)
        self.assertEqual(resolved.source, wrapped.source)

    def test_unmatched_wrapper_is_suppressed(self) -> None:
        direct = CampaignSource(
            title="Unrelated Saudi marketing article",
            url="https://example.com/unrelated",
            source="SearXNG",
        )
        wrapped = CampaignSource(
            title="A distinct campaign story - Publisher",
            url="https://news.google.com/rss/articles/example?oc=5",
            source="Google News RSS: Publisher",
        )

        self.assertIsNone(
            _resolve_google_news_campaign(wrapped, [direct])
        )

    def test_direct_google_news_result_is_unchanged(self) -> None:
        direct = CampaignSource(
            title="Publisher campaign",
            url="https://publisher.example/campaign",
            source="Google News RSS: Publisher",
        )

        resolved = _resolve_google_news_campaign(direct, [])

        self.assertEqual(resolved, direct)


if __name__ == "__main__":
    unittest.main()
