from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.services.scoring.framework import (
    ScoringFramework,
    TMI_FRAMEWORK_V1,
)
from app.services.scoring.models import CampaignAssessment


class DimensionScore(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    dimension: str

    raw_score: float = Field(
        ge=0,
        le=100,
    )

    weight: float = Field(
        gt=0,
        le=1,
    )

    weighted_score: float = Field(
        ge=0,
        le=100,
    )


class ScoringResult(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    campaign_id: int = Field(
        gt=0,
    )

    framework_name: str

    framework_version: str

    total_score: float = Field(
        ge=0,
        le=100,
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    dimensions: tuple[DimensionScore, ...]


class ScoringEngine:

    def score(
        self,
        assessment: CampaignAssessment,
        framework: ScoringFramework = TMI_FRAMEWORK_V1,
    ) -> ScoringResult:

        if assessment.framework_version != framework.version:
            raise ValueError(
                "Assessment framework version does not match "
                "the scoring framework version."
            )

        assessments_by_dimension = {
            item.dimension: item
            for item in assessment.dimensions
        }

        dimension_scores: list[DimensionScore] = []

        total_score = 0.0
        weighted_confidence = 0.0

        for dimension in framework.dimensions:
            assessment_item = assessments_by_dimension[
                dimension.name
            ]

            weighted_score = (
                assessment_item.score
                * dimension.weight
            )

            total_score += weighted_score

            weighted_confidence += (
                assessment_item.confidence
                * dimension.weight
            )

            dimension_scores.append(
                DimensionScore(
                    dimension=dimension.name.value,
                    raw_score=round(
                        assessment_item.score,
                        2,
                    ),
                    weight=dimension.weight,
                    weighted_score=round(
                        weighted_score,
                        2,
                    ),
                )
            )

        return ScoringResult(
            campaign_id=assessment.campaign_id,
            framework_name=framework.name,
            framework_version=framework.version,
            total_score=round(
                total_score,
                2,
            ),
            confidence=round(
                weighted_confidence,
                4,
            ),
            dimensions=tuple(
                dimension_scores
            ),
        )


scoring_engine = ScoringEngine()