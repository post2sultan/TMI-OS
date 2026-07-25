import re

from bs4 import BeautifulSoup


class HTMLCleaner:

    MAX_CONTENT_LENGTH = 10000

    def clean(self, html: str) -> str:

        soup = BeautifulSoup(html, "lxml")

        for tag in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "header",
            "footer",
            "nav",
            "iframe",
            "form",
            "button",
            "aside"
        ]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        text = re.sub(r"\s+", " ", text)

        text = text.strip()

        if len(text) > self.MAX_CONTENT_LENGTH:
            text = text[:self.MAX_CONTENT_LENGTH]

        return text


html_cleaner = HTMLCleaner()