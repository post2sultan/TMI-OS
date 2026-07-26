

import unittest
from datetime import datetime
from datetime import timezone
from unittest.mock import Mock

from app.models.campaign_document import CAMPAIGN_DOCUMENT_TYPES
from app.models.campaign_document import CampaignDocument
from app.repositories.campaign_document_repository import (
    CampaignDocumentRepository,
)
from app.services.evidence_deduplicator import EvidenceDeduplicator


class CampaignDocumentRepositoryTests(unittest.TestCase):

    def test_all_backlog_document_types_are_supported(self) -> None:
        self.assertEqual(
            set(CAMPAIGN_DOCUMENT_TYPES),
            {
                "web_page",
                "news_article",
                "press_release",
                "social_post",
                "video_page",
                "image",
                "uploaded_document",
                "manual_observation",
            },
        )

    def test_create_adds_document_to_caller_transaction(self) -> None:
        session = Mock()
        session.scalars.return_value.all.return_value = []

        document = CampaignDocumentRepository().create(
            session=session,
            campaign_id=7,
            document_type="news_article",
            source_url="https://example.com/news",
            title="Launch coverage",
            extracted_text="Campaign evidence",
        )

        self.assertIsInstance(document, CampaignDocument)
        self.assertEqual(document.campaign_id, 7)
        self.assertEqual(document.document_type, "news_article")
        session.add.assert_called_once_with(document)
        session.flush.assert_called_once()
        session.commit.assert_not_called()

    def test_apply_extraction_stores_structured_evidence(self) -> None:
        session = Mock()
        session.scalars.return_value.all.return_value = []
        document = CampaignDocument(
            campaign_id=7,
            document_type="web_page",
            source_url="https://example.com",
        )
        now = datetime.now(timezone.utc)

        result = CampaignDocumentRepository().apply_extraction(
            session=session,
            document=document,
            title="Campaign launch",
            extracted_text="Structured campaign evidence.",
            published_at=now,
            retrieved_at=now,
            language="en-SA",
            brand="Noor",
            media_assets=["https://example.com/image.jpg"],
            extraction_status="SUCCESS",
            extraction_method="httpx+trafilatura",
        )

        self.assertEqual(result.extracted_text, "Structured campaign evidence.")
        self.assertEqual(result.language, "en-SA")
        self.assertEqual(result.brand, "Noor")
        self.assertEqual(result.media_assets, ["https://example.com/image.jpg"])
        self.assertEqual(result.extraction_status, "success")
        session.add.assert_called_once_with(document)
        session.flush.assert_called_once()

    def test_apply_extraction_marks_semantic_duplicate(self) -> None:
        session = Mock()
        original = CampaignDocument(
            id=10,
            campaign_id=7,
            document_type="web_page",
            source_url="https://example.com/original",
            extracted_text=(
                "Noor launched a Saudi Ramadan campaign "
                "with family storytelling and local media."
            ),
            canonical_url="https://example.com/original",
            content_hash="different",
        )
        duplicate = CampaignDocument(
            id=11,
            campaign_id=7,
            document_type="news_article",
            source_url="https://news.example.com/story",
        )
        session.scalars.return_value.all.return_value = [original, duplicate]
        now = datetime.now(timezone.utc)

        CampaignDocumentRepository().apply_extraction(
            session=session,
            document=duplicate,
            title="Coverage",
            extracted_text=(
                "Noor launched the Saudi Ramadan campaign "
                "using local media and family storytelling."
            ),
            published_at=None,
            retrieved_at=now,
            language="en",
            brand="Noor",
            media_assets=[],
            extraction_status="SUCCESS",
            extraction_method="test",
        )

        self.assertEqual(duplicate.extraction_status, "duplicate")
        self.assertEqual(duplicate.duplicate_of_id, 10)
        self.assertGreaterEqual(
            duplicate.similarity_score,
            EvidenceDeduplicator.SEMANTIC_SIMILARITY_THRESHOLD,
        )

    def test_create_rejects_unknown_document_type(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported campaign document type",
        ):
            CampaignDocumentRepository().create(
                session=Mock(),
                campaign_id=7,
                document_type="unknown",
            )

    def test_list_is_scoped_to_campaign(self) -> None:
        session = Mock()
        expected = [Mock(spec=CampaignDocument)]
        session.scalars.return_value.all.return_value = expected

        result = CampaignDocumentRepository().list_by_campaign(
            session=session,
            campaign_id=7,
        )

        self.assertEqual(result, expected)
        statement = session.scalars.call_args.args[0]
        self.assertIn(
            "campaign_documents.campaign_id",
            str(statement),
        )


if __name__ == "__main__":
    unittest.main()
