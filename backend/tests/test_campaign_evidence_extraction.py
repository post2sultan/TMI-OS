
import unittest
from datetime import datetime
from datetime import timezone
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch

from app.api.extraction import extract_campaign
from app.services.extraction.models import ExtractionResult


class CampaignEvidenceExtractionTests(unittest.TestCase):

    def test_campaign_extraction_persists_structured_document(self) -> None:
        database = Mock()
        campaign = SimpleNamespace(
            id=7,
            url="https://example.com/campaign",
            title="Original title",
            description="",
            content="",
        )
        database.get.return_value = campaign
        document = SimpleNamespace(id=55)
        result = ExtractionResult(
            url=campaign.url,
            final_url=campaign.url,
            title="Noor Launch",
            publisher="Noor",
            language="en-SA",
            published_at=datetime.now(timezone.utc),
            hero_image="https://example.com/hero.jpg",
            content="Extracted campaign evidence.",
            extraction_method="httpx+trafilatura",
            status="SUCCESS",
        )

        with (
            patch(
                "app.api.extraction.extraction_engine.extract",
                return_value=result,
            ),
            patch(
                "app.api.extraction.campaign_document_repository"
                ".get_by_source_url",
                return_value=document,
            ),
            patch(
                "app.api.extraction.campaign_document_repository"
                ".apply_extraction"
            ) as apply_extraction,
        ):
            response = extract_campaign(
                campaign_id=campaign.id,
                database=database,
            )

        self.assertTrue(response.saved)
        self.assertEqual(response.document_id, 55)
        self.assertEqual(campaign.content, result.content)
        self.assertEqual(
            apply_extraction.call_args.kwargs["brand"],
            "Noor",
        )
        self.assertEqual(
            apply_extraction.call_args.kwargs["media_assets"],
            ["https://example.com/hero.jpg"],
        )
        database.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
