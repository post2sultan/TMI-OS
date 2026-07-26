import unittest
from datetime import datetime
from datetime import timezone
from unittest.mock import Mock
from unittest.mock import patch

from app.models.analysis_run import AnalysisRun
from app.repositories.analysis_run_repository import (
    AnalysisRunRepository,
)


class AnalysisRunRepositoryTests(unittest.TestCase):

    def test_record_attempt_commits_independently(self) -> None:
        database = Mock()
        database.__enter__ = Mock(
            return_value=database
        )
        database.__exit__ = Mock(
            return_value=False
        )
        database.refresh.side_effect = (
            lambda run: setattr(run, "id", 42)
        )

        now = datetime.now(timezone.utc)

        with patch(
            "app.repositories.analysis_run_repository.SessionLocal",
            return_value=database,
        ):
            run_id = AnalysisRunRepository().record_attempt(
                campaign_id=7,
                model_name="test-model",
                prompt_version="analysis-v1",
                attempt_number=2,
                raw_response='{"result":"invalid"}',
                validation_status="failed",
                error_message="quality failure",
                started_at=now,
                completed_at=now,
                duration_ms=15,
                force=True,
            )

        self.assertEqual(run_id, 42)
        database.add.assert_called_once()
        database.commit.assert_called_once()
        database.refresh.assert_called_once()

        saved_run = database.add.call_args.args[0]
        self.assertIsInstance(saved_run, AnalysisRun)
        self.assertEqual(saved_run.campaign_id, 7)
        self.assertEqual(saved_run.attempt_number, 2)
        self.assertEqual(
            saved_run.validation_status,
            "failed",
        )
        self.assertTrue(saved_run.force)


if __name__ == "__main__":
    unittest.main()

