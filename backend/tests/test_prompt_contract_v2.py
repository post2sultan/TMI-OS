import unittest
from datetime import datetime
from datetime import timezone

from app.services.analysis.models import AnalysisDocument
from app.services.analysis.prompt_builder import (
    ANALYSIS_PROMPT_VERSION,
    prompt_builder,
)


class PromptContractV2Tests(unittest.TestCase):

    def setUp(self) -> None:
        self.prompt = prompt_builder.build(
            AnalysisDocument(
                campaign_id=109,
                title="Fixed evaluation campaign",
                url="https://example.com/campaign",
                source="test",
                description="A real campaign description.",
                content="Campaign-specific source content.",
                content_type="webpage",
                collected_at=datetime.now(timezone.utc),
                metadata={},
            )
        )

    def test_version_is_incremented(self) -> None:
        self.assertEqual(
            ANALYSIS_PROMPT_VERSION,
            "analysis-v2",
        )
        self.assertEqual(
            self.prompt.prompt_version,
            "analysis-v2",
        )

    def test_contract_contains_no_copyable_assessment_values(self) -> None:
        forbidden = (
            '"score":50',
            '"confidence":0.5',
            "Non-empty assessment grounded",
            "Specific supporting campaign detail",
            "Concise overall campaign assessment",
            "Specific evidence-based strength",
            "Specific evidence-based weakness",
            "Specific actionable recommendation",
        )

        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, self.prompt.content)

    def test_contract_requires_independent_scores_and_reasoning(self) -> None:
        self.assertIn(
            "Do not give every dimension the same score.",
            self.prompt.content,
        )
        self.assertIn(
            "all seven reasoning strings are substantively different",
            self.prompt.content,
        )
        self.assertIn(
            "Every evidence url must be the JSON string",
            self.prompt.content,
        )


if __name__ == "__main__":
    unittest.main()
