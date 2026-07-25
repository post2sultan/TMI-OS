from pydantic import BaseModel
from typing import Any


class Campaign(BaseModel):

    score: int

    data: dict[str, Any]

    insight: dict[str, Any]

    impact: dict[str, Any]

    strengths: list[str]

    weaknesses: list[str]

    recommendations: list[str]