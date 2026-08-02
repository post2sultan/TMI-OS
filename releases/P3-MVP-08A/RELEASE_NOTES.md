# P3-MVP-08A — LinkedIn native PKCE correction

- Uses LinkedIn's required `/oauth/native-pkce/authorization` endpoint for loopback OAuth.
- Removes the Client Secret from the native PKCE token exchange.
- Adds a regression validation for both requirements.
- Includes automatic encrypted-vault backup and rollback.
- Uses no paid API or AI credits.
