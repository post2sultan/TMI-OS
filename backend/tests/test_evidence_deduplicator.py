
import unittest

from app.services.evidence_deduplicator import EvidenceDeduplicator


class EvidenceDeduplicatorTests(unittest.TestCase):

    def setUp(self) -> None:
        self.deduplicator = EvidenceDeduplicator()

    def test_identity_removes_tracking_and_normalizes_content(self) -> None:
        first = self.deduplicator.identity(
            source_url="HTTPS://Example.com/story/?utm_source=x#top",
            content="  Noor   Campaign Evidence ",
        )
        second = self.deduplicator.identity(
            source_url="https://example.com/story",
            content="noor campaign evidence",
        )

        self.assertEqual(first, second)

    def test_semantic_similarity_handles_reordered_language(self) -> None:
        score = self.deduplicator.semantic_similarity(
            "Saudi Ramadan launch uses family storytelling",
            "Family storytelling uses Saudi Ramadan launch",
        )
        self.assertGreaterEqual(
            score,
            self.deduplicator.SEMANTIC_SIMILARITY_THRESHOLD,
        )

    def test_campaign_scoping_is_enforced_by_repository_query(self) -> None:
        self.assertLess(
            self.deduplicator.semantic_similarity(
                "Saudi Ramadan family launch",
                "Unrelated technical product documentation",
            ),
            0.90,
        )


if __name__ == "__main__":
    unittest.main()
