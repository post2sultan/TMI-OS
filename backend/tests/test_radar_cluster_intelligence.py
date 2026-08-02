import unittest
from datetime import datetime, timedelta, timezone

from app.services.radar_cluster_intelligence import (
    extract_known_entities,
    score_cluster,
    title_similarity,
    title_tokens,
)


class RadarClusterIntelligenceTests(unittest.TestCase):
    def test_near_duplicate_bilingual_safe_title_matching(self) -> None:
        left = "Acme launches Ramadan outdoor campaign in Riyadh"
        right = "Acme Ramadan outdoor campaign launches across Riyadh"
        self.assertGreaterEqual(title_similarity(left, right), 0.62)
        self.assertNotIn("campaign", title_tokens(left))

    def test_different_campaigns_do_not_match(self) -> None:
        self.assertLess(
            title_similarity("Acme Ramadan outdoor campaign", "Bank reports quarterly earnings"),
            0.62,
        )

    def test_known_entities_are_exact_phrase_matches(self) -> None:
        entities = extract_known_entities(
            "STC launches a Riyadh activation. STC Bank is not mentioned.",
            ["STC", "Riyadh", "Mobily"],
        )
        self.assertEqual(entities, ["Riyadh", "STC"])

    def test_scoring_rewards_corroboration_and_recency(self) -> None:
        now = datetime.now(timezone.utc)
        strong = score_cluster(4, 3, 6, 1, now, now)
        weak = score_cluster(1, 1, 1, 0, now - timedelta(days=7), now)
        self.assertGreater(strong.confidence, weak.confidence)
        self.assertGreater(strong.trend, weak.trend)
        self.assertIn("independent source", strong.rationale)


if __name__ == "__main__":
    unittest.main()
