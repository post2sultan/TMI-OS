
import unittest
from types import SimpleNamespace

from app.services.campaign_lifecycle import CAMPAIGN_STATUSES
from app.services.campaign_lifecycle import CampaignLifecycle
from app.services.campaign_lifecycle import CampaignTransitionError


class CampaignLifecycleTests(unittest.TestCase):

    def setUp(self) -> None:
        self.lifecycle = CampaignLifecycle()

    def test_contains_every_backlog_status(self) -> None:
        self.assertEqual(
            CAMPAIGN_STATUSES,
            (
                "discovered",
                "shortlisted",
                "researching",
                "ready_for_analysis",
                "analyzing",
                "analyzed",
                "needs_review",
                "approved",
                "rejected",
                "published",
                "archived",
            ),
        )

    def test_happy_path_reaches_published(self) -> None:
        campaign = SimpleNamespace(status="discovered")
        for status in (
            "shortlisted",
            "researching",
            "ready_for_analysis",
            "analyzing",
            "analyzed",
            "needs_review",
            "approved",
            "published",
        ):
            self.lifecycle.transition(campaign, status)

        self.assertEqual(campaign.status, "published")

    def test_invalid_transition_is_rejected_without_mutation(self) -> None:
        campaign = SimpleNamespace(status="discovered")

        with self.assertRaises(CampaignTransitionError):
            self.lifecycle.transition(campaign, "approved")

        self.assertEqual(campaign.status, "discovered")

    def test_failed_analysis_can_return_to_ready(self) -> None:
        campaign = SimpleNamespace(status="analyzing")
        self.lifecycle.transition(campaign, "ready_for_analysis")
        self.assertEqual(campaign.status, "ready_for_analysis")

    def test_analysis_can_begin_from_discovery(self) -> None:
        campaign = SimpleNamespace(status="discovered")
        self.lifecycle.begin_analysis(campaign)
        self.assertEqual(campaign.status, "analyzing")


if __name__ == "__main__":
    unittest.main()
