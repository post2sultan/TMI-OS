import unittest
from unittest.mock import Mock

from app.models.campaign_document import CAMPAIGN_DOCUMENT_TYPES
from app.models.campaign_document import CampaignDocument
from app.repositories.campaign_document_repository import (
    CampaignDocumentRepository,
)


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

        document = CampaignDocumentRepository().create(
            session=session,
            campaign_id=7,
            document_type="news_article",
            source_url="https://example.com/news",
            title="Launch coverage",
            content="Campaign evidence",
        )

        self.assertIsInstance(document, CampaignDocument)
        self.assertEqual(document.campaign_id, 7)
        self.assertEqual(document.document_type, "news_article")
        session.add.assert_called_once_with(document)
        session.flush.assert_called_once()
        session.commit.assert_not_called()

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
