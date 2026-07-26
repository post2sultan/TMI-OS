import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch

from app.services.ai.router import AIRouter
from app.services.analysis.parser import AnalysisParser
from app.services.analysis.pipeline import AnalysisPipeline
from app.services.analysis.quality_validator import (
    AnalysisQualityError,
)
from app.services.scoring.framework import ScoringDimensionName
from app.services.scoring.models import (
    CampaignAssessment,
    DimensionAssessment,
    Evidence,
)


def build_assessment(
    *,
    valid: bool,
) -> CampaignAssessment:

    dimensions = list(ScoringDimensionName)

    return CampaignAssessment(
        campaign_id=1,
        framework_version="1.0",
        dimensions=[
            DimensionAssessment(
                dimension=dimension,
                score=(
                    50
                    if not valid
                    else 60 + index * 4
                ),
                confidence=0.8,
                reasoning=(
                    (
                        f"Noor demonstrates {dimension.value} "
                        "through specific details in the Saudi "
                        f"launch execution section {index + 1}."
                    )
                    if valid
                    else (
                        "Non-empty assessment grounded in the "
                        "campaign document."
                    )
                ),
                evidence=[
                    Evidence(
                        url="https://example.com/noor",
                        description=(
                            "Noor appears in the documented "
                            "Saudi launch execution."
                            if valid
                            else (
                                "Specific supporting "
                                "campaign detail."
                            )
                        ),
                    )
                ],
            )
            for index, dimension in enumerate(dimensions)
        ],
        summary=(
            "Noor uses a recognizable Saudi setting to support "
            "a clear and campaign-specific launch message."
            if valid
            else "Summary generated automatically."
        ),
        strengths=(
            ["Noor uses a recognizable Saudi setting."]
            if valid
            else []
        ),
        weaknesses=(
            ["Noor provides limited performance evidence."]
            if valid
            else []
        ),
        recommendations=(
            ["Add measurable response targets for Noor."]
            if valid
            else []
        ),
    )


class FakeProvider:

    name = "fake"

    def __init__(self) -> None:
        self.generate_calls = 0

    def generate(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        self.generate_calls += 1
        return "not json"

    def embed(
        self,
        text: str,
        model: str,
    ) -> list[float]:
        return [0.1]


class AnalysisRetryTests(unittest.TestCase):

    def setUp(self) -> None:
        self.valid = build_assessment(
            valid=True
        )
        self.invalid = build_assessment(
            valid=False
        )
        self.campaign = SimpleNamespace(
            id=1,
            title="Noor Ramadan Launch",
            description="A Saudi household campaign.",
            content="Noor introduces its service during Ramadan.",
            url="https://example.com/noor",
            source="test",
        )
        self.prompt = SimpleNamespace(
            campaign_id=1,
            framework_version="1.0",
            content="STRICT ORIGINAL PROMPT",
        )

    @staticmethod
    def build_pipeline(
        responses: list[str],
    ) -> tuple[AnalysisPipeline, Mock, Mock]:

        ai_client = Mock()
        ai_client.generate.side_effect = responses
        ai_client.embed.return_value = [0.1]
        ai_client.model = "test-model"

        repository = Mock()

        pipeline = AnalysisPipeline(
            document_builder=Mock(),
            prompt_builder=Mock(),
            ai_client=ai_client,
            parser=AnalysisParser(),
            scoring_engine=Mock(),
            repository=repository,
            vector_service=Mock(),
        )

        return pipeline, ai_client, repository

    def test_invalid_json_retries_once_with_correction(self) -> None:
        pipeline, ai_client, _ = self.build_pipeline(
            [
                "not json",
                self.valid.model_dump_json(),
            ]
        )

        assessment = pipeline._generate_validated_assessment(
            campaign=self.campaign,
            prompt=self.prompt,
        )

        self.assertEqual(assessment, self.valid)
        self.assertEqual(ai_client.generate.call_count, 2)

        first_prompt = ai_client.generate.call_args_list[0].args[0]
        second_prompt = ai_client.generate.call_args_list[1].args[0]

        self.assertEqual(
            first_prompt,
            "STRICT ORIGINAL PROMPT",
        )
        self.assertIn(
            "CORRECTION REQUIRED",
            second_prompt,
        )
        self.assertIn(
            "complete root JSON object",
            second_prompt,
        )

        for call in ai_client.generate.call_args_list:
            self.assertFalse(
                call.kwargs["require_json"]
            )

    def test_quality_failure_retries_and_accepts_valid_output(
        self,
    ) -> None:
        pipeline, ai_client, _ = self.build_pipeline(
            [
                self.invalid.model_dump_json(),
                self.valid.model_dump_json(),
            ]
        )

        assessment = pipeline._generate_validated_assessment(
            campaign=self.campaign,
            prompt=self.prompt,
        )

        self.assertEqual(assessment, self.valid)
        self.assertEqual(ai_client.generate.call_count, 2)
        self.assertIn(
            "same score",
            ai_client.generate.call_args_list[1].args[0],
        )

    def test_second_invalid_output_is_not_persisted(self) -> None:
        pipeline, ai_client, repository = self.build_pipeline(
            [
                self.invalid.model_dump_json(),
                self.invalid.model_dump_json(),
            ]
        )

        pipeline.document_builder.build.return_value = object()
        pipeline.prompt_builder.build.return_value = self.prompt
        session = Mock()

        with self.assertRaises(AnalysisQualityError):
            pipeline.run_and_save(
                session=session,
                campaign=self.campaign,
                force=True,
            )

        self.assertEqual(ai_client.generate.call_count, 2)
        repository.save.assert_not_called()
        session.rollback.assert_called_once()

    def test_router_can_return_raw_json_failure_to_pipeline(
        self,
    ) -> None:
        provider = FakeProvider()
        router = AIRouter(provider=provider)

        with (
            patch(
                "app.services.ai.router.ai_cache.get",
                return_value=None,
            ),
            patch(
                "app.services.ai.router.ai_cache.set"
            ) as cache_set,
        ):
            response = router.generate(
                "unique P0-02 retry test prompt",
                require_json=False,
            )

        self.assertEqual(response, "not json")
        self.assertEqual(provider.generate_calls, 1)
        cache_set.assert_not_called()


if __name__ == "__main__":
    unittest.main()

