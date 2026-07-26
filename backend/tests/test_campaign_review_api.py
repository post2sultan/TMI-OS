import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.models.analysis import Analysis
from app.services.analysis.review_service import ReviewService


class CampaignReviewServiceTests(unittest.TestCase):

    def test_edit_creates_new_analysis_without_overwriting_original(self) -> None:
        database = Mock()
        campaign = SimpleNamespace(id=7, status="needs_review")
        original = Analysis(
            id=10,
            campaign_id=7,
            total_score=75,
            confidence=0.8,
            framework_name="TMI",
            framework_version="1.0",
            constitution_version="1",
            model_name="model",
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

