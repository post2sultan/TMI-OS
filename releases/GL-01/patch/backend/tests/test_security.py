import unittest

from fastapi import HTTPException
from starlette.requests import Request

from app.security import (
    RateLimiter,
    _required_roles,
    authenticate_request,
    rate_limiter,
)


def make_request(
    method: str,
    path: str,
    actor: str | None = None,
) -> Request:
    headers = []
    if actor is not None:
        headers.append((b"x-tmi-actor", actor.encode()))
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers,
        "query_string": b"",
        "scheme": "http",
        "server": ("test", 80),
        "client": ("127.0.0.1", 1),
    }
    return Request(scope)


class SecurityPolicyTests(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        rate_limiter.clear()

    async def test_public_health_does_not_require_key(self) -> None:
        await authenticate_request(make_request("GET", "/health"), None)

    async def test_missing_key_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            await authenticate_request(
                make_request("GET", "/campaigns"),
                None,
            )
        self.assertEqual(caught.exception.status_code, 401)

    async def test_viewer_cannot_mutate(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            await authenticate_request(
                make_request("POST", "/campaigns", "viewer"),
                "dev-viewer-key",
            )
        self.assertEqual(caught.exception.status_code, 403)

    async def test_operator_cannot_approve(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            await authenticate_request(
                make_request(
                    "POST",
                    "/campaigns/7/approve",
                    "operator",
                ),
                "dev-operator-key",
            )
        self.assertEqual(caught.exception.status_code, 403)

    async def test_reviewer_can_approve_with_actor(self) -> None:
        request = make_request(
            "POST",
            "/campaigns/7/approve",
            "reviewer@example.test",
        )
        await authenticate_request(request, "dev-reviewer-key")
        self.assertEqual(request.state.tmi_role, "reviewer")

    async def test_mutation_requires_actor(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            await authenticate_request(
                make_request("POST", "/campaigns"),
                "dev-admin-key",
            )
        self.assertEqual(caught.exception.status_code, 422)

    def test_review_policy_is_separate_from_operator_policy(self) -> None:
        self.assertEqual(
            _required_roles("PATCH", "/campaigns/7/analysis"),
            {"reviewer", "admin"},
        )
        self.assertEqual(
            _required_roles("POST", "/campaigns"),
            {"operator", "admin"},
        )

    def test_rate_limiter_rejects_request_over_limit(self) -> None:
        limiter = RateLimiter()
        self.assertTrue(limiter.allow("identity", 1))
        self.assertFalse(limiter.allow("identity", 1))


if __name__ == "__main__":
    unittest.main()

