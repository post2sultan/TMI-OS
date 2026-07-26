import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.analysis.repository import AnalysisRepository


def make_result(campaign_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        assessment=SimpleNamespace(
            campaign_id=campaign_id,
            summary="Summary",
            strengths=["Strength"],
            weaknesses=["Weakness"],
            recommendations=["Recommendation"],
            dimensions=[],
        ),
        scoring=SimpleNamespace(
            total_score=80,
            confidence=0.9,
            framework_name="TMI",
            framework_version="1.0",
        ),
    )


class AnalysisVersioningTests(unittest.TestCase):

    def test_save_links_new_version_to_previous_analysis(self) -> None:
        session = Mock()
        repository = AnalysisRepository()
        repository.get_latest_by_campaign = Mock(
            return_value=SimpleNamespace(id=41, analysis_version=3)
        )

        saved = repository.save(
            session=session,
            result=make_result(7),
            model_name="qwen:3b",
            prompt_version="analysis-v2",
            constitution_version="1",
        )

        self.assertEqual(saved.analysis_version, 4)
        self.assertEqual(saved.previous_analysis_id, 41)
        self.assertEqual(saved.prompt_version, "analysis-v2")
        self.assertEqual(saved.model_version, "qwen:3b")
        session.add.assert_called_once_with(saved)
        session.flush.assert_called_once()

    def test_first_analysis_starts_at_version_one(self) -> None:
        session = Mock()
        repository = AnalysisRepository()
        repository.get_latest_by_campaign = Mock(return_value=None)

        saved = repository.save(
            session=session,
            result=make_result(8),
            model_name="model",
            prompt_version="analysis-v1",
        )

        self.assertEqual(saved.analysis_version, 1)
        self.assertIsNone(saved.previous_analysis_id)


if __name__ == "__main__":
    unittest.main()

