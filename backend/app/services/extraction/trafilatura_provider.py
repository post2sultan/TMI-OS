import httpx
import trafilatura

from app.services.extraction.models import ExtractedContent


class TrafilaturaProvider:

    def extract(self, url: str) -> ExtractedContent:

        try:
            response = httpx.get(
                url,
                timeout=30,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    )
                },
            )

            response.raise_for_status()

            downloaded = response.text

            extracted = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                include_links=False,
                favor_precision=True,
            )

            if not extracted:
                return ExtractedContent(
                    url=url,
                    final_url=str(response.url),
                    title="",
                    content="",
                    excerpt="",
                    author="",
                    published_date="",
                    language="",
                    word_count=0,
                    success=False,
                    extractor="Trafilatura",
                    error="No content extracted",
                )

            return ExtractedContent(
                url=url,
                final_url=str(response.url),
                title="",
                content=extracted,
                excerpt=extracted[:500],
                author="",
                published_date="",
                language="",
                word_count=len(extracted.split()),
                success=True,
                extractor="Trafilatura",
            )

        except Exception as ex:

            print("URL:", url)
            print("EXCEPTION:", repr(ex))

            return ExtractedContent(
                url=url,
                final_url=url,
                title="",
                content="",
                excerpt="",
                author="",
                published_date="",
                language="",
                word_count=0,
                success=False,
                extractor="Trafilatura",
                error=str(ex),
            )


trafilatura_provider = TrafilaturaProvider()