from app.services.extraction.models import ExtractedContent
from app.services.extraction.trafilatura_provider import (
    trafilatura_provider,
)


class ExtractionManager:

    def __init__(self):

        self.providers = [
            trafilatura_provider,
        ]

    def extract(
        self,
        url: str
    ) -> ExtractedContent:

        last_result = None

        for provider in self.providers:

            result = provider.extract(url)

            if result.success:

                return result

            last_result = result

        return last_result


extraction_manager = ExtractionManager()