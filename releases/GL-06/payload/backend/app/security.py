from __future__ import annotations

import hmac
import logging
from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from uuid import uuid4

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.database import SessionLocal
from app.core.settings import settings
from app.models.audit_event import AuditEvent


logger = logging.getLogger(__name__)
api_key_header = APIKeyHeader(
    name="X-TMI-API-Key",
    auto_error=False,
)
PUBLIC_PATHS = {"/", "/health", "/ready", "/metrics"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
REVIEW_ACTIONS = {
    "approve",
    "reject",
    "reanalyze",
    "archive",
    "analysis",
}


class RateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, identity: str, limit: int) -> bool:
        now = monotonic()
        cutoff = now - 60
        with self._lock:
            requests = self._requests[identity]
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= limit:
                return False
            requests.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._requests.clear()


rate_limiter = RateLimiter()


def _required_roles(method: str, path: str) -> set[str]:
    if method == "GET":
        return {"viewer", "operator", "reviewer", "admin"}
    action = path.rstrip("/").rsplit("/", 1)[-1]
    if action in REVIEW_ACTIONS:
        return {"reviewer", "admin"}
    return {"operator", "admin"}


def _role_for_key(candidate: str) -> str | None:
    for role, configured in settings.api_keys_by_role.items():
        if configured and hmac.compare_digest(candidate, configured):
            return role
    return None


async def authenticate_request(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> None:
    if request.url.path in PUBLIC_PATHS:
        return
    if not api_key:
        raise HTTPException(status_code=401, detail="API key is required.")
    role = _role_for_key(api_key)
    if role is None:
        raise HTTPException(status_code=401, detail="API key is invalid.")
    if role not in _required_roles(request.method, request.url.path):
        raise HTTPException(
            status_code=403,
            detail="This role is not authorized for the requested action.",
        )
    actor = request.headers.get("X-TMI-Actor", "").strip()
    if request.method in WRITE_METHODS and not actor:
        raise HTTPException(
            status_code=422,
            detail="X-TMI-Actor is required for state-changing actions.",
        )
    limit = (
        settings.AUTH_WRITE_RATE_LIMIT_PER_MINUTE
        if request.method in WRITE_METHODS
        else settings.AUTH_READ_RATE_LIMIT_PER_MINUTE
    )
    identity = f"{role}:{actor or 'anonymous-read'}:{request.method}"
    if not rate_limiter.allow(identity, limit):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    request.state.tmi_role = role
    request.state.tmi_actor = actor or role


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = getattr(request.state, "request_id", "")
        if not request_id:
            request_id = request.headers.get("X-Request-ID", "").strip()[:64]
        if not request_id:
            request_id = uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        role = getattr(request.state, "tmi_role", None)
        actor = getattr(request.state, "tmi_actor", None)
        if request.method in WRITE_METHODS and role and actor:
            try:
                with SessionLocal() as database:
                    database.add(
                        AuditEvent(
                            request_id=request_id,
                            actor=actor[:255],
                            role=role,
                            method=request.method,
                            path=request.url.path[:1000],
                            status_code=response.status_code,
                        )
                    )
                    database.commit()
            except Exception:
                logger.exception(
                    "Security audit event persistence failed",
                    extra={"request_id": request_id},
                )
        return response

