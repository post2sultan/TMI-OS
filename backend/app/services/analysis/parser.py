import json

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

        for dimension in payload.get("dimensions", []):

            evidence = dimension.get(
                "evidence",
                [],
            )

            normalized_evidence = []

            for item in evidence:

                if isinstance(item, dict):

                    if (
                        "source" in item
                        and "url" not in item
                    ):
                        item["url"] = item.pop(
                            "source"
                        )

                    normalized_evidence.append(
                        item
                    )

                elif isinstance(item, str):

                    normalized_evidence.append(
                        {
                            "url": "https://unknown.local",
                            "description": item,
                        }
                    )

            dimension["evidence"] = (
                normalized_evidence
            )

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


analysis_parser = AnalysisParser()