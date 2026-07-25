from datetime import datetime

from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    url: str
    final_url: str

    title: str = ""
    description: str = ""
    author: str = ""
    publisher: str = ""
    language: str = ""

    published_at: datetime | None = None

    hero_image: str = ""

    content: str = ""
    markdown: str = ""

    word_count: int = 0
    reading_time_minutes: int = 0

    extraction_method: str = ""
    status: str = "SUCCESS"

    warnings: list[str] = Field(
        default_factory=list
    )
