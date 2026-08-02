import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.models.analysis import Analysis
from app.models.content_creation_job import ContentCreationJob
from app.services.analysis.review_service import ReviewService


class CampaignReviewServiceTests(unittest.TestCase):

    def test_approval_queues_content_creation(self) -> None:
        database = Mock()
        database.scalar.return_value = None
        campaign = SimpleNamespace(id=7, status="needs_review")
        analysis = SimpleNamespace(
            id=10,
            review_status="pending",
            reviewed_by=None,
            review_reason=None,
            reviewed_at=None,
        )
        service = ReviewService(database)
        service._get_campaign = Mock(return_value=campaign)
        service._get_latest_analysis = Mock(return_value=analysis)

        self.assertTrue(service.approve_analysis(7, "Sultan"))

        self.assertEqual(campaign.status, "approved")
        self.assertEqual(analysis.review_status, "approved")
        queued = database.add.call_args.args[0]
        self.assertIsInstance(queued, ContentCreationJob)
        self.assertEqual(queued.campaign_id, 7)
        self.assertEqual(queued.analysis_id, 10)
        self.assertEqual(queued.status, "queued")
        database.commit.assert_called_once()

    def test_publish_queues_private_youtube_job(self) -> None:
        database = Mock()
        campaign = SimpleNamespace(id=7, status="approved")
        analysis = SimpleNamespace(id=10, review_status="approved")
        job = SimpleNamespace(
            status="generated",
            published_at=None,
            video_script="Complete video script",
            social_caption="Complete social caption",
            video_url="/media/campaign-7/video.mp4",
            youtube_status="not_queued",
            youtube_error="old",
            youtube_requested_at=None,
        )
        database.scalar.return_value = job
        service = ReviewService(database)
        service._get_campaign = Mock(return_value=campaign)
        service._get_latest_analysis = Mock(return_value=analysis)

        self.assertTrue(service.publish_campaign(7))

        self.assertEqual(campaign.status, "approved")
        self.assertEqual(job.status, "generated")
        self.assertEqual(job.youtube_status, "queued")
        self.assertEqual(job.youtube_error, "")
        self.assertIsNotNone(job.youtube_requested_at)
        database.commit.assert_called_once()

    def test_complete_youtube_publish_is_the_only_success_transition(self) -> None:
        database = Mock()
        campaign = SimpleNamespace(id=7, status="approved")
        job = SimpleNamespace(
            id=12,
            campaign_id=7,
            youtube_status="uploading",
            youtube_video_id="",
            youtube_url="",
            youtube_error="",
            status="generated",
            published_at=None,
        )
        database.get.return_value = job
        service = ReviewService(database)
        service._get_campaign = Mock(return_value=campaign)

        self.assertTrue(service.complete_youtube_publish(12, "private-video-id"))

        self.assertEqual(campaign.status, "published")
        self.assertEqual(job.youtube_status, "published")
        self.assertEqual(job.youtube_video_id, "private-video-id")
        self.assertEqual(
            job.youtube_url,
            "https://www.youtube.com/watch?v=private-video-id",
        )
        database.commit.assert_called_once()

    def test_edit_creates_new_analysis_without_overwriting_original(self) -> None:
        database = Mock()
        campaign = SimpleNamespace(id=7, status="needs_review")
        original = Analysis(
            id=10,
            campaign_id=7,
            analysis_version=1,
            total_score=75,
            confidence=0.8,
            framework_name="TMI",
            framework_version="1.0",
            constitution_version="1",
            model_name="model",
            model_version="model",
            prompt_version="analysis-v1",
            summary="Original",
            strengths=["Original strength"],
            weaknesses=["Original weakness"],
            recommendations=["Original recommendation"],
            dimensions=[],
        )
        service = ReviewService(database)
        service._get_campaign = Mock(return_value=campaign)
        service._get_latest_analysis = Mock(return_value=original)
        database.refresh.side_effect = (
            lambda item: setattr(item, "id", getattr(item, "id", None) or 11)
        )

        edited = service.edit_latest_analysis(
            campaign_id=7,
            edited_by="reviewer",
            reviewer_notes="Clarified summary",
            summary="Edited",
            strengths=None,
            weaknesses=None,
            recommendations=None,
        )

        self.assertEqual(original.summary, "Original")
        self.assertEqual(edited.summary, "Edited")
        self.assertEqual(edited.id, 11)
        self.assertEqual(edited.analysis_version, 2)
        self.assertEqual(edited.previous_analysis_id, 10)
        self.assertEqual(edited.prompt_version, "analysis-v1")
        self.assertEqual(edited.reviewer_notes, "Clarified summary")
        self.assertEqual(edited.review_status, "pending")
        database.add.assert_called_once_with(edited)
        database.commit.assert_called_once()

    def test_archive_uses_campaign_lifecycle(self) -> None:
        database = Mock()
        campaign = SimpleNamespace(id=7, status="needs_review")
        service = ReviewService(database)
        service._get_campaign = Mock(return_value=campaign)

        self.assertTrue(service.archive_campaign(7))
        self.assertEqual(campaign.status, "archived")
        database.commit.assert_called_once()

    def test_evidence_read_is_campaign_scoped(self) -> None:
        database = Mock()
        service = ReviewService(database)
        service._get_campaign = Mock(return_value=SimpleNamespace(id=7))
        database.scalars.return_value.all.return_value = [SimpleNamespace(id=1)]

        items = service.get_campaign_evidence(7)

        self.assertEqual(len(items), 1)
        self.assertIn(
            "campaign_documents.campaign_id",
            str(database.scalars.call_args.args[0]),
        )


if __name__ == "__main__":
    unittest.main()
