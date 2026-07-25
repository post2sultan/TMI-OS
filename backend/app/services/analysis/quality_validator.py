from __future__ import annotations

from dataclasses import dataclass
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

        return QualityValidationResult(
            is_valid=not errors,
            errors=tuple(errors),
        )

    def validate_or_raise(
        self,
        assessment: CampaignAssessment,
    ) -> None:

        result = self.validate(
            assessment
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


analysis_quality_validator = AnalysisQualityValidator()
