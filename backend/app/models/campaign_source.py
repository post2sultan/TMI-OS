from typing import Any

from pydantic import BaseModel


class CampaignSource(BaseModel):

    title: str

    url: str

    source: str

    description: str = ""

    content: str = ""

    analysis: dict[str, Any] | None = None