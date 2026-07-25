from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import HttpUrl


class AnalysisDocument(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    campaign_id: int = Field(
        gt=0,
    )

    title: str = Field(
        min_length=1,
        max_length=500,
    )

    url: HttpUrl

    source: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str = ""

    content: str = ""

    content_type: str = Field(
        default="webpage",
        min_length=1,
        max_length=50,
    )

    language: str | None = Field(
        default=None,
        max_length=20,
    )

    published_at: datetime | None = None

    collected_at: datetime | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )