from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import HttpUrl
from pydantic import model_validator

from app.services.scoring.framework import (
    ScoringDimensionName,
)


class Evidence(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    url: HttpUrl

    description: str = Field(
        min_length=1,
        max_length=3000,
    )


class DimensionAssessment(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    dimension: ScoringDimensionName

    score: float = Field(
        ge=0,
        le=100,
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    reasoning: str = Field(
        min_length=1,
        max_length=3000,
    )

    evidence: list[Evidence] = Field(
        default_factory=list,
    )


class CampaignAssessment(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    campaign_id: int = Field(
        gt=0,
    )

    framework_version: str = Field(
        min_length=1,
        max_length=20,
    )

    dimensions: list[DimensionAssessment]

    summary: str = Field(
        min_length=1,
        max_length=3000,
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

    @model_validator(mode="after")
    def validate_dimensions(self) -> "CampaignAssessment":

        expected_dimensions = set(
            ScoringDimensionName
        )

        received_dimensions = {
            item.dimension
            for item in self.dimensions
        }

        if received_dimensions != expected_dimensions:

            missing = expected_dimensions - received_dimensions
            extra = received_dimensions - expected_dimensions

            raise ValueError(
                "Campaign assessment must contain exactly one "
                f"assessment for every framework dimension. "
                f"Missing: {sorted(item.value for item in missing)}. "
                f"Extra: {sorted(item.value for item in extra)}."
            )

        if len(self.dimensions) != len(expected_dimensions):

            raise ValueError(
                "Campaign assessment contains duplicate dimensions."
            )

        return self