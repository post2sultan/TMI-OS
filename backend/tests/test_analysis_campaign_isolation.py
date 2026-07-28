import unittest

from types import SimpleNamespace
from unittest.mock import Mock

from app.services.analysis.pipeline import AnalysisPipeline
from app.services.scoring.engine import ScoringEngine
from app.services.scoring.framework import ScoringDimensionName
from app.services.scoring.models import (
    CampaignAssessment,
    DimensionAssessment,
)


class AnalysisCampaignIsolationTests(unittest.TestCase):

    def test_each_campaign_persists_its_own_analysis(self) -> None:
        campaign = SimpleNamespace(
            id=167,
            title="Campaign 167",
            url="https://example.com/167",
            source="test",
        )
        prompt = SimpleNamespace(
            content="campaign-specific prompt",
            prompt_version="analysis-v2",
        )
        assessment = CampaignAssessment(
            campaign_id=167,
            framework_version="1.0",
            dimensions=[
                DimensionAssessment(
                    dimension=dimension,
                    score=70,
                    confidence=0.8,
                    reasoning=f"Campaign 167 {dimension.value}.",
                )
                for dimension in ScoringDimensionName
            ],
            summary="Campaign-specific summary",
            strengths=["Clear"],
            weaknesses=["None"],
            recommendations=["Continue"],
        )
        scoring = ScoringEngine().score(assessment)
        analysis = SimpleNamespace(
            id=901,
            campaign_id=167,
            total_score=80,
            confidence=0.9,
            framework_name="TMI",
            framework_version="1.0",
            model_name="local-model",
            summary="Campaign-specific summary",
            strengths=["Clear"],
            weaknesses=["None"],
            recommendations=["Continue"],
            dimensions=[],
        )

        document_builder = Mock()
        document_builder.build.return_value = object()
        prompt_builder = Mock()
        prompt_builder.build.return_value = prompt
        ai_client = Mock()
        ai_client.embed.side_effect = [[0.1], [0.2]]
        ai_client.model = "local-model"
        scoring_engine = Mock()
        scoring_engine.score.return_value = scoring
        repository = Mock()
        repository.save.return_value = analysis
        vector_service = Mock()
        session = Mock()

        pipeline = AnalysisPipeline(
            document_builder=document_builder,
            prompt_builder=prompt_builder,
            ai_client=ai_client,
            parser=Mock(),
            scoring_engine=scoring_engine,
            repository=repository,
            vector_service=vector_service,
            quality_validator=Mock(),
            run_repository=Mock(),
        )
        pipeline._generate_validated_assessment = Mock(
            return_value=assessment
        )
        pipeline._find_semantic_duplicate = Mock(
            side_effect=AssertionError(
                "Cross-campaign analysis reuse is forbidden."
            )
        )

        saved = pipeline.run_and_save(
            session=session,
            campaign=campaign,
        )

        self.assertIs(saved, analysis)
        repository.save.assert_called_once()
        self.assertEqual(
            repository.save.call_args.kwargs[
                "result"
            ].assessment.campaign_id,
            campaign.id,
        )
        pipeline._find_semantic_duplicate.assert_not_called()
        session.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
