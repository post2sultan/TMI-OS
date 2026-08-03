from types import SimpleNamespace
from unittest import TestCase

from app.services.stock_media_service import StockMediaService


class StockMediaServiceTests(TestCase):
    def test_queries_are_deduplicated_and_capped(self) -> None:
        queries = StockMediaService.queries(
            "Centrepoint Back to School Campaign",
            "Saudi retail fashion and family value campaign",
        )
        self.assertLessEqual(len(queries), 3)
        self.assertEqual(len(queries), len(set(queries)))
        self.assertIn("Centrepoint", queries[0])

    def test_empty_copy_still_has_safe_local_query(self) -> None:
        campaign = SimpleNamespace(title="", description="")
        self.assertEqual(
            StockMediaService.queries(campaign.title, campaign.description),
            ["Saudi Arabia marketing"],
        )
