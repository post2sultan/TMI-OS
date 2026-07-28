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
          "video_script": "This approved campaign shows how a clear proposition can earn attention. Its focused audience and strong execution create a useful example for marketers. The Mi'yar Index score highlights the campaign's strongest choices while identifying one practical next step: add a measurable call to action. That improvement would connect creative attention to observable business impact and make the campaign easier to evaluate over time.",
          "social_caption": "A clear proposition earns attention, but measurable action turns attention into impact. This campaign scores strongly and offers one practical lesson for marketers.",
          "hashtags": ["TMIOS", "#Marketing", "CampaignAnalysis"]
        }
        """

        generated = ContentPackageService(database, ai_client).generate(7)

        self.assertIs(generated, job)
        self.assertEqual(job.status, "generated")
        self.assertTrue(job.video_script.startswith("This approved campaign"))
        self.assertEqual(
            job.hashtags,
            ["#TMIOS", "#Marketing", "#CampaignAnalysis"],
        )
        self.assertIsNotNone(job.generated_at)
        database.commit.assert_called_once()
        ai_client.generate.assert_called_once()

    def test_rejects_generation_for_unapproved_campaign(self) -> None:
        database = Mock()
        database.get.return_value = SimpleNamespace(id=7, status="needs_review")

        result = ContentPackageService(database, Mock()).generate(7)

        self.assertIsNone(result)
        database.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
