from unittest import TestCase

from app.routers.radar import _parse_cluster_ids


class RadarLatestScanTests(TestCase):
    def test_cluster_selection_is_safe_and_deduplicated(self) -> None:
        self.assertEqual(_parse_cluster_ids("3,2,bad,-1,3, 7"), [3, 2, 7])

    def test_cluster_selection_is_capped(self) -> None:
        value = ",".join(str(index) for index in range(1, 250))
        self.assertEqual(len(_parse_cluster_ids(value)), 200)
