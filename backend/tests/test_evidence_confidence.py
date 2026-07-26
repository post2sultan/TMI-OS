
import unittest
from datetime import datetime
from datetime import timezone

from app.services.evidence_confidence import EvidenceConfidenceAssessor


class EvidenceConfidenceAssessorTests(unittest.TestCase):

    def setUp(self) -> None:
        self.assessor = EvidenceConfidenceAssessor()

    def test_high_quality_web_evidence_receives_strong_confidence(self) -> None:
        result = self.assessor.assess(
            document_type="news_article",
            source_url="https://example.com/story",
            extracted_text=" ".join(["evidence"] * 60),
            extraction_status="SUCCESS",
            extraction_method="httpx+trafilatura",
            published_at=datetime.now(timezone.utc),
        )

        self.assertEqual(result.score, 0.95)
        self.assertEqual(result.origin, "web_extraction")
        self.assertEqual(result.representation, "direct_quote")
        self.assertEqual(result.supporting_source, "https://example.com/story")

    def test_manual_observation_is_identified_as_paraphrase(self) -> None:
        result = self.assessor.assess(
            document_type="manual_observation",
            source_url=None,
            extracted_text="Observed campaign placement.",
            extraction_status="SUCCESS",
            extraction_method="manual",
            published_at=None,
        )

        self.assertEqual(result.origin, "manual")
        self.assertEqual(result.representation, "paraphrase")
        self.assertEqual(result.supporting_source, "")
        self.assertGreater(result.score, 0.0)


if __name__ == "__main__":
    unittest.main()
