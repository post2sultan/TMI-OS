import json
import logging
import unittest
from io import StringIO
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.observability import JsonFormatter, Metrics


class ObservabilityTests(unittest.TestCase):
    def test_json_formatter_emits_correlation_fields(self) -> None:
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonFormatter())
        test_logger = logging.getLogger("tmi.test.observability")
        test_logger.handlers = [handler]
        test_logger.propagate = False
        test_logger.setLevel(logging.INFO)
        test_logger.info(
            "completed",
            extra={"event": "request_completed", "request_id": "trace-1"},
        )
        event = json.loads(stream.getvalue())
        self.assertEqual(event["event"], "request_completed")
        self.assertEqual(event["request_id"], "trace-1")

    def test_request_id_is_preserved(self) -> None:
        with TestClient(app) as client:
            response = client.get(
                "/health",
                headers={"X-Request-ID": "operator-trace-123"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["X-Request-ID"],
            "operator-trace-123",
        )

    def test_ready_reports_every_dependency(self) -> None:
        available = {
            "postgres": True,
            "qdrant": True,
            "redis": True,
            "searxng": True,
            "ollama": True,
        }
        with patch("app.main.dependency_readiness", return_value=available):
            with TestClient(app) as client:
                response = client.get("/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["dependencies"], available)

    def test_ready_fails_closed_with_dependency_status(self) -> None:
        unavailable = {
            "postgres": True,
            "qdrant": False,
            "redis": True,
            "searxng": True,
            "ollama": True,
        }
        with patch("app.main.dependency_readiness", return_value=unavailable):
            with TestClient(app) as client:
                response = client.get("/ready")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["detail"]["dependencies"]["qdrant"])

    def test_prometheus_metrics_are_machine_readable(self) -> None:
        registry = Metrics()
        registry.observe("GET", "/health", 200, 0.125)
        registry.dependencies({"postgres": True, "redis": False})
        rendered = registry.render()
        self.assertIn(
            'tmi_http_requests_total{method="GET",path="/health",status="200"} 1',
            rendered,
        )
        self.assertIn(
            'tmi_dependency_ready{dependency="redis"} 0',
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
