import unittest

from app.services.radar_signal_service import (
    campaign_candidate_confidence,
    generate_cluster_key,
    normalize_signal_title,
)


class RadarSignalFoundationTests(unittest.TestCase):
    def test_title_normalization_supports_arabic_and_english(self) -> None:
        self.assertEqual(
            normalize_signal_title("حملة موسم الرياض — Brand Launch!"),
            "حملة موسم الرياض brand launch",
        )

    def test_cluster_key_is_stable_for_punctuation_variants(self) -> None:
        self.assertEqual(
            generate_cluster_key("Saudi Brand: New Campaign"),
            generate_cluster_key("Saudi Brand — New Campaign"),
        )

    def test_corroboration_increases_confidence(self) -> None:
        single = campaign_candidate_confidence(1, 1)
        corroborated = campaign_candidate_confidence(3, 2)
        self.assertGreater(corroborated, single)
        self.assertLessEqual(corroborated, 0.95)


if __name__ == "__main__":
    unittest.main()

