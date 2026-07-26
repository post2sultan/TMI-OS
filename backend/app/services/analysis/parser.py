import json
import re
from urllib.parse import urlparse

from pydantic import ValidationError

from app.services.scoring.models import CampaignAssessment


class AnalysisParser:

    def parse(
        self,
        raw_response: str,
    ) -> CampaignAssessment:

        normalized_response = raw_response.strip()

        if not normalized_response:
            raise ValueError(
                "Analysis response cannot be empty."
            )

        payload = json.loads(normalized_response)

        if not isinstance(payload, dict):
            raise ValueError(
                "Analysis response must be a JSON object."
            )

        recommendations = payload.get(
            "recommendations",
            [],
        )
        if not isinstance(recommendations, list):
            recommendations = []

        framework_version = str(
            payload.get("framework_version", "")
        ).strip()
        if re.fullmatch(
            r"v\d+(?:\.\d+)*",
            framework_version,
            flags=re.IGNORECASE,
        ):
            payload["framework_version"] = (
                framework_version[1:]
            )

        for dimension in payload.get("dimensions", []):

            dimension_recommendations = dimension.pop(
                "recommendations",
                [],
            )
            if isinstance(
                dimension_recommendations,
                list,
            ):
                recommendations.extend(
                    item.strip()
                    for item in dimension_recommendations
                    if isinstance(item, str)
                    and item.strip()
                )

            description = dimension.pop(
                "description",
                None,
            )
            if (
                not str(
                    dimension.get("reasoning", "")
                ).strip()
                and str(description or "").strip()
            ):
                dimension["reasoning"] = description

            if (
                "dimension" not in dimension
                and "dimension_name" in dimension
            ):
                dimension["dimension"] = (
                    self._normalize_dimension_name(
                        dimension.pop("dimension_name")
                    )
                )

            evidence = dimension.get(
                "evidence",
                [],
            )

            normalized_evidence = []

            for item in evidence:

                if isinstance(item, dict):

                    description = str(
                        item.get("description", "")
                    ).strip()
                    if not description:
                        continue

                    if (
                        "source" in item
                        and "url" not in item
                    ):
                        item["url"] = item.pop(
                            "source"
                        )

                    if "url" not in item:
                        item["url"] = (
                            "https://unknown.local"
                        )

                    url = str(item["url"]).strip()
                    parsed_url = urlparse(url)
                    if (
                        parsed_url.scheme
                        not in {"http", "https"}
                        or not parsed_url.netloc
                    ):
                        url = "https://unknown.local"

                    normalized_evidence.append(
                        {
                            "url": url,
                            "description": description,
                        }
                    )

                elif isinstance(item, str):

                    description = item.strip()
                    if not description:
                        continue

                    normalized_evidence.append(
                        {
                            "url": "https://unknown.local",
                            "description": description,
                        }
                    )

            dimension["evidence"] = (
                normalized_evidence[:10]
            )

        payload["recommendations"] = list(
            dict.fromkeys(recommendations)
        )

        self._populate_rollup_fields(payload)

        if not payload.get("summary", "").strip():

            payload["summary"] = (
                "Summary generated automatically."
            )

        try:

            return CampaignAssessment.model_validate(
                payload
            )

        except ValidationError as exc:

            raise ValueError(
                str(exc)
            ) from exc

    @staticmethod
    def _normalize_dimension_name(
        value: object,
    ) -> str:
        normalized = re.sub(
            r"[^a-z0-9]+",
            "_",
            str(value).strip().lower(),
        )
        return normalized.strip("_")

    @staticmethod
    def _populate_rollup_fields(
        payload: dict,
    ) -> None:
        dimensions = [
            item
            for item in payload.get("dimensions", [])
            if isinstance(item, dict)
            and str(item.get("reasoning", "")).strip()
        ]
        if not dimensions:
            return

        ranked = sorted(
            dimensions,
            key=lambda item: float(
                item.get("score", 0)
            ),
        )
        lowest = ranked[0]
        highest = ranked[-1]

        if not str(payload.get("summary", "")).strip():
            payload["summary"] = " ".join(
                str(item["reasoning"]).strip()
                for item in ranked[-2:]
            )[:3000]

        if not payload.get("strengths"):
            payload["strengths"] = [
                (
                    "Highest-scoring dimension "
                    f"({highest.get('dimension')}): "
                    f"{str(highest['reasoning']).strip()}"
                )[:3000]
            ]

        if not payload.get("weaknesses"):
            payload["weaknesses"] = [
                (
                    "Lowest-scoring dimension "
                    f"({lowest.get('dimension')}): "
                    f"{str(lowest['reasoning']).strip()}"
                )[:3000]
            ]

        if not payload.get("recommendations"):
            payload["recommendations"] = [
                (
                    "Improve the lowest-scoring dimension "
                    f"({lowest.get('dimension')}) by addressing "
                    "the limitation identified in its assessment: "
                    f"{str(lowest['reasoning']).strip()}"
                )[:3000]
            ]


analysis_parser = AnalysisParser()
