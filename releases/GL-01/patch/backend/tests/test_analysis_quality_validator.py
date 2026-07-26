import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.main import get_db
from app.services.analysis.pipeline import analysis_pipeline
from app.services.analysis.pipeline import AnalysisPipeline
from app.services.analysis.quality_validator import (
    AnalysisQualityError,
    AnalysisQualityValidator,
)
from app.services.scoring.framework import ScoringDimensionName
from app.services.scoring.models import (
    CampaignAssessment,
    DimensionAssessment,
    Evidence,
)


def build_assessment(
    *,
    scores: list[int] | None = None,
    reasoning: str | None = None,
    evidence_description: str = (
        "The Noor launch film shows the product in a Saudi home."
    ),
    summary: str = (
        "Noor connects its launch message to a recognizable "
        "Saudi household experience."
    ),
    strengths: list[str] | None = None,
    weaknesses: list[str] | None = None,
    recommendations: list[str] | None = None,
) -> CampaignAssessment:

    dimensions = list(ScoringDimensionName)
    resolved_scores = scores or [
        61,
        64,
        67,
        70,
        73,
        76,
        79,
    ]

    return CampaignAssessment(
        campaign_id=1,
        framework_version="1.0",
        dimensions=[
            DimensionAssessment(
                dimension=dimension,
                score=resolved_scores[index],
                confidence=0.8,
                reasoning=(
                    reasoning
                    or (
                        f"Noor demonstrates {dimension.value} "
                        "through a specific Saudi launch execution "
                        f"identified in source section {index + 1}."
                    )
                ),
                evidence=[
                    Evidence(
                        url="https://example.com/noor",
                        description=evidence_description,
                    )
                ],
            )
            for index, dimension in enumerate(dimensions)
        ],
        summary=summary,
        strengths=(
            strengths
            if strengths is not None
            else ["Noor uses a locally recognizable setting."]
        ),
        weaknesses=(
            weaknesses
            if weaknesses is not None
            else ["Noor provides limited performance evidence."]
        ),
        recommendations=(
            recommendations
            if recommendations is not None
            else ["Extend Noor with measurable response targets."]
        ),
    )


class AnalysisQualityValidatorTests(unittest.TestCase):

    def setUp(self) -> None:
        self.validator = AnalysisQualityValidator()
        self.context = (
            "Noor Ramadan Launch",
            "A Saudi household campaign for the Noor service.",
        )

    def test_accepts_campaign_specific_analysis(self) -> None:
        result = self.validator.validate(
            assessment=build_assessment(),
            campaign_context=self.context,
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, ())

    def test_rejects_identical_scores_and_reasoning(self) -> None:
        result = self.validator.validate(
            assessment=build_assessment(
                scores=[50] * 7,
                reasoning=(
                    "This generic reasoning repeats exactly across "
                    "every required assessment dimension without detail."
                ),
            ),
            campaign_context=self.context,
        )

        self.assertIn(
            "Every dimension has the same score.",
            result.errors,
        )
        self.assertIn(
            "Every dimension has identical reasoning.",
            result.errors,
        )

    def test_rejects_template_placeholders(self) -> None:
        result = self.validator.validate(
            assessment=build_assessment(
                evidence_description=(
                    "Specific supporting campaign detail."
                ),
                summary="Summary generated automatically.",
            ),
            campaign_context=self.context,
        )

        self.assertTrue(
            any(
                "placeholder evidence" in error
                for error in result.errors
            )
        )
        self.assertIn(
            "Summary contains placeholder text.",
            result.errors,
        )

    def test_rejects_empty_required_lists(self) -> None:
        result = self.validator.validate(
            assessment=build_assessment(
                strengths=[],
                weaknesses=[],
                recommendations=[],
            ),
            campaign_context=self.context,
        )

        self.assertIn(
            "strengths must contain at least one item.",
            result.errors,
        )
        self.assertIn(
            "weaknesses must contain at least one item.",
            result.errors,
        )
        self.assertIn(
            "recommendations must contain at least one item.",
            result.errors,
        )

    def test_rejects_analysis_without_campaign_language(self) -> None:
        assessment = build_assessment(
            reasoning=(
                "The execution uses clear visual hierarchy and "
                "provides concrete strategic support for the score."
            ),
            evidence_description=(
                "The execution provides a concrete supporting "
                "observation for the assessment."
            ),
            summary=(
                "The execution is coherent and strategically focused, "
                "with room for stronger measurement."
            ),
            strengths=[
                "The execution has a clear strategic structure."
            ],
            weaknesses=[
                "The execution lacks measured outcome evidence."
            ],
            recommendations=[
                "Add measurable response targets to the execution."
            ],
        )

        result = self.validator.validate(
            assessment=assessment,
            campaign_context=self.context,
        )

        self.assertIn(
            "Analysis contains no campaign-specific language.",
            result.errors,
        )

    def test_validate_or_raise_returns_all_failures(self) -> None:
        with self.assertRaises(AnalysisQualityError) as context:
            self.validator.validate_or_raise(
                assessment=build_assessment(
                    scores=[50] * 7,
                    reasoning=(
                        "Non-empty assessment grounded in the "
                        "campaign document."
                    ),
                    summary=(
                        "Summary generated automatically."
                    ),
                    strengths=[],
                    weaknesses=[],
                    recommendations=[],
                ),
                campaign_context=self.context,
            )

        self.assertGreaterEqual(
            len(context.exception.errors),
            6,
        )


class AnalysisQualityPersistenceBoundaryTests(unittest.TestCase):

    def test_invalid_analysis_is_rolled_back_and_not_saved(self) -> None:
        invalid_assessment = build_assessment(
            scores=[50] * 7,
            reasoning=(
                "Non-empty assessment grounded in the "
                "campaign document."
            ),
            summary="Summary generated automatically.",
            strengths=[],
            weaknesses=[],
            recommendations=[],
        )

        document_builder = Mock()
        document_builder.build.return_value = object()

        prompt_builder = Mock()
        prompt_builder.build.return_value = SimpleNamespace(
            campaign_id=1,
            framework_version="1.0",
            prompt_version="analysis-v1",
            content="analysis prompt",
        )

        ai_client = Mock()
        ai_client.embed.return_value = [0.1]
        ai_client.generate.return_value = '{"invalid":"quality"}'

        parser = Mock()
        parser.parse.return_value = invalid_assessment

        scoring_engine = Mock()
        repository = Mock()
        vector_service = Mock()

        pipeline = AnalysisPipeline(
            document_builder=document_builder,
            prompt_builder=prompt_builder,
            ai_client=ai_client,
            parser=parser,
            scoring_engine=scoring_engine,
            repository=repository,
            vector_service=vector_service,
            run_repository=Mock(),
        )

        session = Mock()
        campaign = SimpleNamespace(
            id=1,
            title="Noor Ramadan Launch",
            description="A Saudi household campaign.",
            content="Noor introduces its service during Ramadan.",
        )

        with self.assertRaises(AnalysisQualityError):
            pipeline.run_and_save(
                session=session,
                campaign=campaign,
                force=True,
            )

        scoring_engine.score.assert_not_called()
        repository.save.assert_not_called()
        session.rollback.assert_called_once()


class AnalysisQualityApiTests(unittest.TestCase):

    def test_api_returns_structured_quality_error(self) -> None:
        database = Mock()
        database.scalar.return_value = SimpleNamespace(
            id=1,
            title="Noor Ramadan Launch",
            description="A Saudi household campaign.",
            content="Noor introduces its service during Ramadan.",
        )

        def override_get_db():
            yield database

        app.dependency_overrides[get_db] = override_get_db

        quality_error = AnalysisQualityError(
            [
                "Every dimension has the same score.",
                "Summary contains placeholder text.",
            ]
        )

        try:
            with (
                patch.object(
                    analysis_pipeline.repository,
                    "get_latest_by_campaign",
                    return_value=None,
                ),
                patch.object(
                    analysis_pipeline,
                    "run_and_save",
                    side_effect=quality_error,
                ),
            ):
                response = TestClient(app).post(
                    "/campaigns/1/analyze?force=true",
                    headers={
                        "X-TMI-API-Key": "dev-operator-key",
                        "X-TMI-Actor": "quality-test",
                    },
                )
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["detail"]["code"],
            "analysis_quality_validation_failed",
        )
        self.assertEqual(
            response.json()["detail"]["errors"],
            list(quality_error.errors),
        )
        database.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
