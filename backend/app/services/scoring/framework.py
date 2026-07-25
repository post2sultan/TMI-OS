from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


class ScoringDimensionName(StrEnum):

    STRATEGIC_CLARITY = "strategic_clarity"

    CREATIVE_STRENGTH = "creative_strength"

    BRAND_FIT = "brand_fit"

    CUSTOMER_VALUE = "customer_value"

    CULTURAL_RELEVANCE = "cultural_relevance"

    EXECUTION_QUALITY = "execution_quality"

    COMMERCIAL_POTENTIAL = "commercial_potential"


class ScoringDimension(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    name: ScoringDimensionName

    label: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str = Field(
        min_length=1,
        max_length=500,
    )

    weight: float = Field(
        gt=0,
        le=1,
    )

    max_score: float = Field(
        default=100,
        gt=0,
    )


class ScoringFramework(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    name: str = Field(
        min_length=1,
        max_length=100,
    )

    version: str = Field(
        min_length=1,
        max_length=20,
    )

    market: str = Field(
        min_length=1,
        max_length=100,
    )

    definition: str = Field(
        min_length=1,
        max_length=1000,
    )

    dimensions: tuple[ScoringDimension, ...]

    @model_validator(
        mode="after",
    )
    def validate_framework(
        self,
    ) -> "ScoringFramework":

        if not self.dimensions:
            raise ValueError(
                "Scoring framework must contain dimensions."
            )

        dimension_names = [
            dimension.name
            for dimension in self.dimensions
        ]

        if len(dimension_names) != len(
            set(dimension_names)
        ):
            raise ValueError(
                "Scoring framework contains duplicate dimensions."
            )

        total_weight = sum(
            dimension.weight
            for dimension in self.dimensions
        )

        if abs(total_weight - 1.0) > 0.000001:
            raise ValueError(
                "Scoring dimension weights must total 1.0."
            )

        return self


TMI_FRAMEWORK_V1 = ScoringFramework(
    name="The Mi'yar Index",
    version="1.0",
    market="Saudi Arabia",
    definition=(
        "The effectiveness of a marketing campaign in the "
        "Saudi market, based on strategy, creative quality, "
        "customer value, execution and likely commercial impact."
    ),
    dimensions=(
        ScoringDimension(
            name=ScoringDimensionName.STRATEGIC_CLARITY,
            label="Strategic Clarity",
            description=(
                "Measures the clarity of the campaign objective, "
                "target audience, proposition and intended action."
            ),
            weight=0.15,
        ),
        ScoringDimension(
            name=ScoringDimensionName.CREATIVE_STRENGTH,
            label="Creative Strength",
            description=(
                "Measures the originality, distinctiveness, "
                "storytelling quality and attention value of the idea."
            ),
            weight=0.15,
        ),
        ScoringDimension(
            name=ScoringDimensionName.BRAND_FIT,
            label="Brand Fit",
            description=(
                "Measures brand consistency, recognizability and "
                "alignment with the brand's identity and positioning."
            ),
            weight=0.10,
        ),
        ScoringDimension(
            name=ScoringDimensionName.CUSTOMER_VALUE,
            label="Customer Value",
            description=(
                "Measures the relevance and strength of the benefit, "
                "offer or reason provided for the customer to act."
            ),
            weight=0.15,
        ),
        ScoringDimension(
            name=ScoringDimensionName.CULTURAL_RELEVANCE,
            label="Cultural Relevance",
            description=(
                "Measures localization, cultural sensitivity and "
                "relevance to Saudi audiences and market context."
            ),
            weight=0.15,
        ),
        ScoringDimension(
            name=ScoringDimensionName.EXECUTION_QUALITY,
            label="Execution Quality",
            description=(
                "Measures the quality, consistency and suitability "
                "of the campaign's channel and creative execution."
            ),
            weight=0.15,
        ),
        ScoringDimension(
            name=ScoringDimensionName.COMMERCIAL_POTENTIAL,
            label="Commercial Potential",
            description=(
                "Measures the campaign's likely ability to generate "
                "attention, engagement, action, demand or sales."
            ),
            weight=0.15,
        ),
    ),
)