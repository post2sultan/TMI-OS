import unittest

from types import SimpleNamespace
from unittest.mock import Mock

from app.models.content_creation_job import ContentCreationJob
from app.services.content_package_service import ContentPackageService


class ContentPackageServiceTests(unittest.TestCase):
    def test_generates_and_persists_complete_content_package(self) -> None:
        database = Mock()
        campaign = SimpleNamespace(
            id=7,
            status="approved",
            title="Campaign Seven",
            description="A documented campaign.",
        )
        analysis = SimpleNamespace(
            id=10,
            review_status="approved",
            total_score=82,
            summary="A strong campaign with a clear audience.",
            strengths=["Clear proposition"],
            recommendations=["Add a measurable call to action"],
        )
        job = ContentCreationJob(
            campaign_id=7,
            analysis_id=10,
            status="queued",
            video_script="",
            social_caption="",
            hashtags=[],
        )
        database.get.return_value = campaign
        database.scalar.side_effect = [analysis, job]
        ai_client = Mock()
        ai_client.generate.return_value = """
        {
          "video_script": "This approved campaign shows how a clear proposition earns attention. Its focused audience and strong execution create a useful example. The Mi'yar Index highlights the strongest choices while identifying one practical next step: add a measurable call to action that connects creative attention to observable business impact.",
          "social_caption": "A clear proposition earns attention, but measurable action turns attention into impact. This campaign scores strongly and offers one practical lesson for marketers.",
          "hashtags": ["TMIOS", "#Marketing", "CampaignAnalysis"]
        }
        """

        generated = ContentPackageService(database, ai_client).generate(7)

        self.assertIs(generated, job)
        self.assertEqual(job.status, "generated")
        self.assertTrue(job.video_script.startswith("This approved campaign"))
        self.assertGreaterEqual(len(job.video_script.split()), 80)
        self.assertEqual(
            job.hashtags,
            ["#TMIOS", "#Marketing", "#CampaignAnalysis"],
        )
        self.assertIsNotNone(job.generated_at)
        database.commit.assert_called_once()
        self.assertEqual(ai_client.generate.call_count, 2)

    def test_rejects_generation_for_unapproved_campaign(self) -> None:
        database = Mock()
        database.get.return_value = SimpleNamespace(id=7, status="needs_review")

        result = ContentPackageService(database, Mock()).generate(7)

        self.assertIsNone(result)
        database.commit.assert_not_called()

    def test_published_campaign_keeps_published_status(self) -> None:
        database = Mock()
        campaign = SimpleNamespace(
            id=7,
            status="published",
            title="Published Campaign",
            description="Published description.",
        )
        analysis = SimpleNamespace(
            id=10,
            review_status="approved",
            total_score=80,
            summary="Published summary.",
            strengths=["Strength"],
            recommendations=["Recommendation"],
        )
        job = ContentCreationJob(
            campaign_id=7,
            analysis_id=10,
            status="published",
            video_script="",
            social_caption="",
            hashtags=[],
        )
        database.get.return_value = campaign
        database.scalar.side_effect = [analysis, job]
        ai_client = Mock()
        ai_client.generate.return_value = (
            '{"video_script":"'
            + ("A factual campaign sentence. " * 22)
            + '","social_caption":"A factual published campaign caption '
            "with a clear marketing lesson for teams seeking stronger "
            "audience relevance, measurable action, credible evidence, "
            'and repeatable commercial impact.","hashtags":'
            '["TMIOS","Marketing","Campaign"]}'
        )

        generated = ContentPackageService(database, ai_client).generate(7)

        self.assertIs(generated, job)
        self.assertEqual(job.status, "published")


if __name__ == "__main__":
    unittest.main()
