# P3-MVP-08B — LinkedIn OpenID OAuth correction

- Uses LinkedIn's OpenID-compatible confidential OAuth endpoint.
- Removes unsupported PKCE parameters while retaining CSRF state validation and the loopback callback.
- Uses the DPAPI-encrypted Client Secret only in the server-side token exchange.
- Requests only `openid`, `profile`, and `w_member_social`.
- Includes automatic encrypted-vault backup, validation, and rollback.
- Uses no paid API or AI credits.
