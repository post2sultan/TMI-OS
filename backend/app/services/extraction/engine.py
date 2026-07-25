import logging
import math
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup
from playwright.sync_api import (
    Browser,
    sync_playwright,
)
from readability import Document

from app.services.extraction.cleaner import (
    clean_text,
    html_to_markdown_like_text,
)
from app.services.extraction.metadata import (
    extract_metadata,
)
from app.services.extraction.models import (
    ExtractionResult,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FetchResult:
    html: str
    final_url: str
    method: str


class ExtractionEngine:
    USER_AGENT = (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36 "
        "TMI-OS/0.2"
    )

    BLOCKED_SCHEMES = {
        "data",
        "file",
        "ftp",
        "javascript",
        "mailto",
        "tel",
    }

    def _validate_url(
        self,
        url: str,
    ) -> str:
        normalized = url.strip()

        parsed = urlparse(normalized)

        if parsed.scheme.lower() in (
            self.BLOCKED_SCHEMES
        ):
            raise ValueError(
                "Unsupported URL scheme."
            )

        if parsed.scheme.lower() not in {
            "http",
            "https",
        }:
            raise ValueError(
                "Only HTTP and HTTPS URLs "
                "can be extracted."
            )

        if not parsed.hostname:
            raise ValueError(
                "URL hostname is missing."
            )

        return normalized

    def _fetch_http(
        self,
        url: str,
    ) -> FetchResult:
        timeout = httpx.Timeout(
            timeout=30.0,
            connect=10.0,
        )

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8"
            ),
            "Accept-Language": (
                "en-US,en;q=0.9,"
                "ar;q=0.8"
            ),
        }

        with httpx.Client(
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
        ) as client:
            response = client.get(url)

            response.raise_for_status()

            content_type = response.headers.get(
                "content-type",
                "",
            ).lower()

            if (
                "text/html" not in content_type
                and "application/xhtml+xml"
                not in content_type
            ):
                raise ValueError(
                    "The URL did not return "
                    "an HTML document."
                )

            return FetchResult(
                html=response.text,
                final_url=str(response.url),
                method="httpx",
            )

    def _fetch_playwright(
        self,
        url: str,
    ) -> FetchResult:
        with sync_playwright() as playwright:
            browser: Browser = (
                playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ],
                )
            )

            try:
                page = browser.new_page(
                    user_agent=self.USER_AGENT,
                    viewport={
                        "width": 1440,
                        "height": 1000,
                    },
                    locale="en-SA",
                )

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=45000,
                )

                try:
                    page.wait_for_load_state(
                        "networkidle",
                        timeout=10000,
                    )

                except Exception:
                    pass

                return FetchResult(
                    html=page.content(),
                    final_url=page.url,
                    method="playwright",
                )

            finally:
                browser.close()

    @staticmethod
    def _looks_rendered(
        html: str,
    ) -> bool:
        soup = BeautifulSoup(
            html,
            "lxml",
        )

        body = soup.body

        if body is None:
            return False

        visible_text = clean_text(
            body.get_text(
                " ",
                strip=True,
            )
        )

        return len(visible_text) >= 500

    def _fetch(
        self,
        url: str,
    ) -> FetchResult:
        warnings: list[str] = []

        try:
            fetched = self._fetch_http(url)

            if self._looks_rendered(
                fetched.html
            ):
                return fetched

            warnings.append(
                "HTTP response contained "
                "insufficient visible content."
            )

        except Exception as error:
            warnings.append(
                f"HTTP extraction failed: "
                f"{error}"
            )

        logger.info(
            "Using Playwright fallback for %s",
            url,
        )

        fetched = self._fetch_playwright(
            url
        )

        return fetched

    @staticmethod
    def _extract_with_trafilatura(
        html: str,
        url: str,
    ) -> tuple[str, str]:
        content = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            include_links=False,
            favor_precision=True,
            output_format="txt",
        ) or ""

        markdown = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            include_links=True,
            favor_precision=True,
            output_format="markdown",
        ) or ""

        return (
            clean_text(content),
            clean_text(markdown),
        )

    @staticmethod
    def _extract_with_readability(
        html: str,
    ) -> tuple[str, str]:
        document = Document(html)

        summary_html = document.summary(
            html_partial=True
        )

        content = BeautifulSoup(
            summary_html,
            "lxml",
        ).get_text(
            "\n",
            strip=True,
        )

        markdown = html_to_markdown_like_text(
            summary_html
        )

        return (
            clean_text(content),
            markdown,
        )

    @staticmethod
    def _extract_with_beautifulsoup(
        html: str,
    ) -> tuple[str, str]:
        soup = BeautifulSoup(
            html,
            "lxml",
        )

        target = (
            soup.find("article")
            or soup.find("main")
            or soup.body
            or soup
        )

        content = target.get_text(
            "\n",
            strip=True,
        )

        markdown = html_to_markdown_like_text(
            str(target)
        )

        return (
            clean_text(content),
            markdown,
        )

    def extract(
        self,
        url: str,
    ) -> ExtractionResult:
        validated_url = self._validate_url(
            url
        )

        fetched = self._fetch(
            validated_url
        )

        metadata = extract_metadata(
            html=fetched.html,
            base_url=fetched.final_url,
        )

        warnings: list[str] = []

        extraction_method = (
            f"{fetched.method}+trafilatura"
        )

        content, markdown = (
            self._extract_with_trafilatura(
                html=fetched.html,
                url=fetched.final_url,
            )
        )

        if len(content) < 300:
            warnings.append(
                "Trafilatura returned limited "
                "content; readability fallback used."
            )

            fallback_content, fallback_markdown = (
                self._extract_with_readability(
                    fetched.html
                )
            )

            if len(fallback_content) > len(
                content
            ):
                content = fallback_content
                markdown = fallback_markdown
                extraction_method = (
                    f"{fetched.method}+readability"
                )

        if len(content) < 300:
            warnings.append(
                "Readability returned limited "
                "content; DOM fallback used."
            )

            fallback_content, fallback_markdown = (
                self._extract_with_beautifulsoup(
                    fetched.html
                )
            )

            if len(fallback_content) > len(
                content
            ):
                content = fallback_content
                markdown = fallback_markdown
                extraction_method = (
                    f"{fetched.method}+beautifulsoup"
                )

        if not content:
            raise ValueError(
                "No readable content could be "
                "extracted from the page."
            )

        words = content.split()

        word_count = len(words)

        reading_time = max(
            1,
            math.ceil(
                word_count / 225
            ),
        )

        return ExtractionResult(
            url=validated_url,
            final_url=fetched.final_url,
            title=metadata["title"],
            description=metadata[
                "description"
            ],
            author=metadata["author"],
            publisher=metadata["publisher"],
            language=metadata["language"],
            published_at=metadata[
                "published_at"
            ],
            hero_image=metadata[
                "hero_image"
            ],
            content=content,
            markdown=markdown,
            word_count=word_count,
            reading_time_minutes=(
                reading_time
            ),
            extraction_method=(
                extraction_method
            ),
            status="SUCCESS",
            warnings=warnings,
        )


extraction_engine = ExtractionEngine()
