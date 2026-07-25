from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class AnalysisResponse(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    score: float = Field(
        ge=0,
        le=100,
    )

    data: dict[str, Any] = Field(
        default_factory=dict,
    )

    insight: dict[str, Any] = Field(
        default_factory=dict,
    )

    impact: dict[str, Any] = Field(
        default_factory=dict,
    )

    strengths: list[str] = Field(
        default_factory=list,
    )

    weaknesses: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )