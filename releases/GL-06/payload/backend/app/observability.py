from __future__ import annotations

import json
import logging
from collections import defaultdict
from threading import Lock
from time import monotonic
from typing import Any
from uuid import uuid4

import redis
import requests
from fastapi import Request
from qdrant_client import QdrantClient
from starlette.responses import Response

from app.core.database import database_is_ready
from app.core.settings import settings


logger = logging.getLogger("tmi.requests")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in (
            "event",
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
        ):
            value = getattr(record, field, None)
            if value is not None:
                event[field] = value
        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event, separators=(",", ":"), default=str)


def configure_logging(level: str) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    if not any(getattr(handler, "_tmi_json", False) for handler in root.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        handler._tmi_json = True  # type: ignore[attr-defined]
        root.handlers.clear()
        root.addHandler(handler)


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self._duration: dict[tuple[str, str], float] = defaultdict(float)
        self._dependencies: dict[str, int] = {}

    def observe(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        with self._lock:
            self._requests[(method, path, status_code)] += 1
            self._duration[(method, path)] += duration_seconds

    def dependencies(self, states: dict[str, bool]) -> None:
        with self._lock:
            self._dependencies = {
                name: int(available) for name, available in states.items()
            }

    def render(self) -> str:
        with self._lock:
            lines = [
                "# HELP tmi_http_requests_total HTTP requests processed.",
                "# TYPE tmi_http_requests_total counter",
            ]
            for (method, path, status), count in sorted(self._requests.items()):
                lines.append(
                    "tmi_http_requests_total"
                    f'{{method="{method}",path="{path}",status="{status}"}} {count}'
                )
            lines.extend(
                [
                    "# HELP tmi_http_request_duration_seconds_total "
                    "Cumulative HTTP request duration.",
                    "# TYPE tmi_http_request_duration_seconds_total counter",
                ]
            )
            for (method, path), duration in sorted(self._duration.items()):
                lines.append(
                    "tmi_http_request_duration_seconds_total"
                    f'{{method="{method}",path="{path}"}} {duration:.6f}'
                )
            lines.extend(
                [
                    "# HELP tmi_dependency_ready Dependency availability.",
                    "# TYPE tmi_dependency_ready gauge",
                ]
            )
            for name, available in sorted(self._dependencies.items()):
                lines.append(
                    f'tmi_dependency_ready{{dependency="{name}"}} {available}'
                )
            return "\n".join(lines) + "\n"


metrics = Metrics()


def dependency_readiness() -> dict[str, bool]:
    timeout = settings.READINESS_TIMEOUT_SECONDS
    states: dict[str, bool] = {}

    checks = {
        "postgres": database_is_ready,
        "qdrant": lambda: bool(
            QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY.get_secret_value() or None,
                timeout=timeout,
            ).get_collections()
        ),
        "redis": lambda: bool(
            redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD.get_secret_value() or None,
                socket_connect_timeout=timeout,
                socket_timeout=timeout,
            ).ping()
        ),
        "searxng": lambda: requests.get(
            f"{settings.SEARXNG_URL.rstrip('/')}/healthz",
            timeout=timeout,
        ).status_code == 200,
        "ollama": lambda: requests.get(
            f"{settings.OLLAMA_URL.rstrip('/')}/api/tags",
            timeout=timeout,
        ).status_code == 200,
    }
    for name, check in checks.items():
        try:
            states[name] = bool(check())
        except Exception:
            states[name] = False
    metrics.dependencies(states)
    return states


class RequestObservabilityMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        supplied = request.headers.get("X-Request-ID", "").strip()
        request_id = supplied[:64] if supplied else uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        started = monotonic()
        status_code = 500

        async def send_with_request_id(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = [
                    header
                    for header in message.get("headers", [])
                    if header[0].lower() != b"x-request-id"
                ]
                headers.append((b"x-request-id", request_id.encode("ascii", "ignore")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            logger.exception(
                "Request failed",
                extra={"event": "request_failed", "request_id": request_id},
            )
            raise
        finally:
            duration = monotonic() - started
            route = scope.get("route")
            path = getattr(route, "path", "unmatched")
            metrics.observe(request.method, path, status_code, duration)
            logger.info(
                "Request completed",
                extra={
                    "event": "request_completed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 3),
                },
            )


def metrics_response() -> Response:
    return Response(metrics.render(), media_type="text/plain; version=0.0.4")
