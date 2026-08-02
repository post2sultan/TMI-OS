import unittest
from unittest.mock import Mock, patch

from app.models.radar_source import RadarSource
from app.services.radar_source_monitor import RadarSourceMonitor


class RadarSourceMonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.monitor = RadarSourceMonitor()

    @patch("app.services.radar_source_monitor.requests.get")
    def test_collects_matching_rss_entries(self, get: Mock) -> None:
        response = Mock()
        response.content = b"""<rss version='2.0'><channel><item><title>Saudi brand campaign launch</title><link>https://example.com/a</link><description>Outdoor activation</description></item><item><title>Unrelated finance</title><link>https://example.com/b</link></item></channel></rss>"""
        response.raise_for_status.return_value = None
        get.return_value = response
        source = RadarSource(id=1, name="Test feed", source_type="rss", url="https://example.com/feed", query="campaign activation")
        items = self.monitor.collect_feed(source)
        self.assertEqual([item.url for item in items], ["https://example.com/a"])

    @patch("app.services.radar_source_monitor.requests.get")
    def test_collects_matching_sitemap_urls(self, get: Mock) -> None:
        response = Mock()
        response.content = b"""<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'><url><loc>https://example.com/saudi-campaign-launch</loc></url><url><loc>https://example.com/investor-results</loc></url></urlset>"""
        response.raise_for_status.return_value = None
        get.return_value = response
        source = RadarSource(id=1, name="Test sitemap", source_type="sitemap", url="https://example.com/sitemap.xml", query="campaign")
        items = self.monitor.collect_sitemap(source)
        self.assertEqual([item.url for item in items], ["https://example.com/saudi-campaign-launch"])

    def test_rejects_unsupported_source_type(self) -> None:
        source = RadarSource(id=1, name="Bad", source_type="paid", url="https://example.com", query="")
        with self.assertRaisesRegex(ValueError, "Unsupported source type"):
            self.monitor.collect(source)


if __name__ == "__main__":
    unittest.main()
