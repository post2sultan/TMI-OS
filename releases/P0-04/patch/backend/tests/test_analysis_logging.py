import io
import unittest

from contextlib import redirect_stderr
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.analysis.pipeline import AnalysisPipeline


class AnalysisLoggingTests(unittest.TestCase):

    def test_failure_uses_structured_logging_without_console_dump(
        self,
    ) -> None:
        document_builder = Mock()
        document_builder.build.side_effect = RuntimeError(
            "controlled failure"
        )

        pipeline = AnalysisPipeline(
            document_builder=document_builder,
            prompt_builder=Mock(),
            ai_client=Mock(),
            parser=Mock(),
            scoring_engine=Mock(),
            repository=Mock(),
            vector_service=Mock(),
            run_repository=Mock(),
        )
        session = Mock()
        campaign = SimpleNamespace(id=17)
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            redirect_stdout(stdout),
            redirect_stderr(stderr),
            self.assertLogs(
                "app.services.analysis.pipeline",
                level="ERROR",
            ) as captured,
            self.assertRaisesRegex(
                RuntimeError,
                "controlled failure",
            ),
        ):
            pipeline.run_and_save(
                session=session,
                campaign=campaign,
                force=True,
            )

        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue(
            any(
                "Analysis pipeline failed" in message
                for message in captured.output
            )
        )
        session.rollback.assert_called_once()

    def test_parse_failure_does_not_log_raw_response(
        self,
    ) -> None:
        parser = Mock()
        parser.parse.side_effect = ValueError(
            "invalid response"
        )
        pipeline = AnalysisPipeline(
            parser=parser,
            run_repository=Mock(),
        )
        sensitive_response = "PRIVATE RAW RESPONSE"

        with (
            self.assertLogs(
                "app.services.analysis.pipeline",
                level="ERROR",
            ) as captured,
            self.assertRaises(ValueError),
        ):
            pipeline._parse_response(
                campaign_id=17,
                raw_response=sensitive_response,
            )

        logs = "\n".join(captured.output)
        self.assertIn(
            "Analysis response parsing failed",
            logs,
        )
        self.assertNotIn(
            sensitive_response,
            logs,
        )


if __name__ == "__main__":
    unittest.main()
