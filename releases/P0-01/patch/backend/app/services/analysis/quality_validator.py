from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from app.services.scoring.models import CampaignAssessment


PLACEHOLDER_TEXTS = {
    "summary generated automatically.",
    "concise overall campaign assessment.",
    "non-empty assessment grounded in the campaign document.",
    "specific supporting campaign detail.",
    "specific evidence-based strength.",
    "specific evidence-based weakness.",
    "specific actionable recommendation.",
}

MIN_REASONING_LENGTH = 40
MIN_SUMMARY_LENGTH = 40
MIN_CAMPAIGN_TOKEN_LENGTH = 4

GENERIC_CAMPAIGN_TOKENS = {
    "about",
    "after",
    "also",
    "brand",
    "campaign",
    "content",
    "could",
    "from",
    "into",
    "market",
    "media",
    "more",
    "should",
    "their",
    "this",
    "through",
    "using",
    "with",
}


@dataclass(frozen=True)
class QualityValidationResult:

    is_valid: bool
    errors: tuple[str, ...]


class AnalysisQualityError(ValueError):

    def __init__(
        self,
        errors: Iterable[str],
    ) -> None:

        self.errors = tuple(errors)

        message = (
            "Analysis quality validation failed: "
            + "; ".join(self.errors)
        )

        super().__init__(message)


class AnalysisQualityValidator:

    def validate(
        self,
        assessment: CampaignAssessment,
        campaign_context: Iterable[str] = (),
    ) -> QualityValidationResult:

        errors: list[str] = []

        self._validate_dimensions(
            assessment=assessment,
            errors=errors,
        )

        self._validate_summary(
            assessment=assessment,
            errors=errors,
        )

        self._validate_lists(
            assessment=assessment,
            errors=errors,
        )

        self._validate_campaign_specific_language(
            assessment=assessment,
            campaign_context=campaign_context,
            errors=errors,
        )

        return QualityValidationResult(
            is_valid=not errors,
            errors=tuple(errors),
        )

    def validate_or_raise(
        self,
        assessment: CampaignAssessment,
        campaign_context: Iterable[str] = (),
    ) -> None:

        result = self.validate(
            assessment=assessment,
            campaign_context=campaign_context,
        )

        if not result.is_valid:
            raise AnalysisQualityError(
                result.errors
            )

    def _validate_dimensions(
        self,
        assessment: CampaignAssessment,
        errors: list[str],
    ) -> None:

        dimensions = assessment.dimensions

        if not dimensions:
            errors.append(
                "No dimension assessments were returned."
            )
            return

        scores = [
            float(dimension.score)
            for dimension in dimensions
        ]

        if len(set(scores)) == 1:
            errors.append(
                "Every dimension has the same score."
            )

        normalized_reasoning = [
            self._normalize_text(
                dimension.reasoning
            )
            for dimension in dimensions
        ]

        if len(set(normalized_reasoning)) == 1:
            errors.append(
                "Every dimension has identical reasoning."
            )

        for dimension in dimensions:
            dimension_name = str(
                dimension.dimension
            )

            reasoning = dimension.reasoning.strip()

            if len(reasoning) < MIN_REASONING_LENGTH:
                errors.append(
                    f"{dimension_name} reasoning is too short."
                )

            if self._is_placeholder(
                reasoning
            ):
                errors.append(
                    f"{dimension_name} reasoning is placeholder text."
                )

            for evidence in dimension.evidence:
                description = evidence.description.strip()

                if self._is_placeholder(
                    description
                ):
                    errors.append(
                        f"{dimension_name} contains placeholder evidence."
                    )

                if not description:
                    errors.append(
                        f"{dimension_name} contains empty evidence."
                    )

    def _validate_summary(
        self,
        assessment: CampaignAssessment,
        errors: list[str],
    ) -> None:

        summary = assessment.summary.strip()

        if len(summary) < MIN_SUMMARY_LENGTH:
            errors.append(
                "Summary is missing or too short."
            )

        if self._is_placeholder(
            summary
        ):
            errors.append(
                "Summary contains placeholder text."
            )

    @staticmethod
    def _validate_lists(
        assessment: CampaignAssessment,
        errors: list[str],
    ) -> None:

        required_lists = {
            "strengths": assessment.strengths,
            "weaknesses": assessment.weaknesses,
            "recommendations": assessment.recommendations,
        }

        for field_name, values in required_lists.items():
            meaningful_values = [
                value.strip()
                for value in values
                if value.strip()
            ]

            if not meaningful_values:
                errors.append(
                    f"{field_name} must contain at least one item."
                )

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:

        return " ".join(
            value.lower().strip().split()
        )

    def _is_placeholder(
        self,
        value: str,
    ) -> bool:

        normalized = self._normalize_text(
            value
        )

        return normalized in PLACEHOLDER_TEXTS

    def _validate_campaign_specific_language(
        self,
        assessment: CampaignAssessment,
        campaign_context: Iterable[str],
        errors: list[str],
    ) -> None:

        campaign_tokens: set[str] = set()

        for value in campaign_context:
            campaign_tokens.update(
                self._meaningful_tokens(value)
            )

        if not campaign_tokens:
            return

        analysis_text = " ".join(
            [
                assessment.summary,
                *assessment.strengths,
                *assessment.weaknesses,
                *assessment.recommendations,
                *[
                    dimension.reasoning
                    for dimension in assessment.dimensions
                ],
                *[
                    evidence.description
                    for dimension in assessment.dimensions
                    for evidence in dimension.evidence
                ],
            ]
        )

        analysis_tokens = self._meaningful_tokens(
            analysis_text
        )

        if campaign_tokens.isdisjoint(
            analysis_tokens
        ):
            errors.append(
                "Analysis contains no campaign-specific language."
            )

    @staticmethod
    def _meaningful_tokens(
        value: str,
    ) -> set[str]:

        return {
            token
            for token in re.findall(
                r"[^\W_]+",
                value.casefold(),
                flags=re.UNICODE,
            )
            if (
                len(token) >= MIN_CAMPAIGN_TOKEN_LENGTH
                and token not in GENERIC_CAMPAIGN_TOKENS
            )
        }


analysis_quality_validator = AnalysisQualityValidator()
