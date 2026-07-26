# TMI OS P1-01 — Campaign Source Documents

Adds durable support for multiple source documents per campaign.

- Supports web pages, news articles, press releases, social posts, video
  pages, images, uploaded documents, and manual observations.
- Backfills every existing campaign URL as a web-page document.
- Prevents the same non-null source URL from being attached twice to one
  campaign.
- Keeps document creation inside the caller's database transaction.
- Includes a reversible migration and complete release automation.
