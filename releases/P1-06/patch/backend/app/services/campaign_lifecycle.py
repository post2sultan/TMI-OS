
from app.models.campaign import Campaign


CAMPAIGN_STATUSES = (
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
)


class CampaignTransitionError(ValueError):
    pass


class CampaignLifecycle:

    TRANSITIONS = {
        "discovered": {"shortlisted", "archived"},
        "shortlisted": {"researching", "rejected", "archived"},
        "researching": {"ready_for_analysis", "archived"},
        "ready_for_analysis": {"analyzing", "archived"},
        "analyzing": {"analyzed", "ready_for_analysis"},
        "analyzed": {"needs_review", "ready_for_analysis", "archived"},
        "needs_review": {
            "approved",
            "rejected",
            "ready_for_analysis",
            "archived",
        },
        "approved": {"published", "rejected", "archived"},
        "rejected": {"ready_for_analysis", "archived"},
        "published": {"archived"},
        "archived": {"discovered"},
    }

    def transition(
        self,
        campaign: Campaign,
        target_status: str,
    ) -> Campaign:

        current = getattr(
            campaign,
            "status",
            "discovered",
        )
        if not isinstance(current, str):
            current = "discovered"
            campaign.status = current
        target = target_status.strip().lower()
        if target not in CAMPAIGN_STATUSES:
            raise CampaignTransitionError(
                f"Unknown campaign status: {target_status}"
            )
        if target == current:
            return campaign
        if target not in self.TRANSITIONS.get(current, set()):
            raise CampaignTransitionError(
                f"Campaign cannot transition from {current} to {target}."
            )

        campaign.status = target
        return campaign

    def begin_analysis(
        self,
        campaign: Campaign,
    ) -> Campaign:

        current = getattr(campaign, "status", "discovered")
        if not isinstance(current, str):
            current = "discovered"
            campaign.status = current
        paths = {
            "discovered": (
                "shortlisted",
                "researching",
                "ready_for_analysis",
                "analyzing",
            ),
            "shortlisted": (
                "researching",
                "ready_for_analysis",
                "analyzing",
            ),
            "researching": (
                "ready_for_analysis",
                "analyzing",
            ),
            "ready_for_analysis": ("analyzing",),
            "analyzed": ("ready_for_analysis", "analyzing"),
            "needs_review": ("ready_for_analysis", "analyzing"),
            "rejected": ("ready_for_analysis", "analyzing"),
        }
        for status in paths.get(current, ()):
            self.transition(campaign, status)
        if campaign.status != "analyzing":
            raise CampaignTransitionError(
                f"Campaign cannot begin analysis from {current}."
            )
        return campaign


campaign_lifecycle = CampaignLifecycle()
