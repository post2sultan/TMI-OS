# TMI OS M3.1c — Discovery History UI

Connects the Campaign Radar page to the M3.1b discovery history API.

- Displays newest-first provider execution history.
- Shows query, provider, status, result count, and duration.
- Adds ten-row previous/next pagination.
- Refreshes history automatically after a discovery run.
- Adds strict-null guards required by the production TypeScript build.

No backend schema or database migration is required.
