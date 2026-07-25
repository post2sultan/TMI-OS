import requests


class ContentExtractor:

    def extract(self, url: str) -> str:

        response = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        return response.text


content_extractor = ContentExtractor()