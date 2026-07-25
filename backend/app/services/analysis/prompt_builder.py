import json

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.services.analysis.models import AnalysisDocument
from app.services.scoring.constitution_loader import (
    ConstitutionLoader,
    constitution_loader,
)
from app.services.scoring.framework import (
    ScoringFramework,
    TMI_FRAMEWORK_V1,
)


class AnalysisPrompt(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    framework_version: str = Field(
        min_length=1,
        max_length=20,
    )

    campaign_id: int = Field(
        gt=0,
    )

    content: str = Field(
        min_length=1,
    )


class PromptBuilder:

    def __init__(
        self,
        loader: ConstitutionLoader = constitution_loader,
    ) -> None:

        self.loader = loader

    def build(
        self,
        document: AnalysisDocument,
        framework: ScoringFramework = TMI_FRAMEWORK_V1,
    ) -> AnalysisPrompt:

        constitution_version = (
            self._resolve_constitution_version(
                framework.version
            )
        )

        constitution = self.loader.load(
            constitution_version
        ).strip()

        campaign_payload = json.dumps(
            document.model_dump(
                mode="json",
                exclude_none=True,
            ),
            ensure_ascii=False,
            separators=(",", ":"),
        )

        response_template = self._build_response_template(
            document=document,
            framework=framework,
        )

        prompt = "\n".join(
            [
                "You are the TMI campaign assessment engine.",
                "",
                "Assess the supplied campaign using only the supplied "
                "campaign document and constitution.",
                "",
                "CRITICAL OUTPUT RULES",
                "- Return one complete JSON object only.",
                "- The root JSON object must contain campaign_id, "
                "framework_version, dimensions, summary, strengths, "
                "weaknesses and recommendations.",
                "- Do not return a single dimension object.",
                "- dimensions must contain exactly 7 objects.",
                "- Include every required dimension exactly once.",
                "- Do not add fields.",
                "- Do not omit fields.",
                "- Do not use Markdown.",
                "- Do not use code fences.",
                "- reasoning must always be a non-empty string.",
                "- score must be an integer from 0 to 100.",
                "- confidence must be from 0.0 to 1.0.",
                "- description is permitted only inside evidence.",
                "- evidence must use only the campaign URL.",
                "- Never invent campaign facts or performance results.",
                "- If information is missing, explain the limitation "
                "inside reasoning.",
                "- An evidence list may be empty when the campaign "
                "document does not support the assessment.",
                "- Do not calculate a total score.",
                "",
                "CONSTITUTION",
                constitution,
                "",
                "CAMPAIGN DOCUMENT",
                campaign_payload,
                "",
                "REQUIRED COMPLETE JSON STRUCTURE",
                response_template,
                "",
                f"campaign_id must be {document.campaign_id}.",
                (
                    "framework_version must be "
                    f'"{framework.version}".'
                ),
                "",
                "Return the complete root JSON object now.",
            ]
        )

        return AnalysisPrompt(
            framework_version=framework.version,
            campaign_id=document.campaign_id,
            content=prompt,
        )

    @staticmethod
    def _resolve_constitution_version(
        framework_version: str,
    ) -> str:

        major_version = framework_version.split(
            ".",
            maxsplit=1,
        )[0].strip()

        if not major_version:
            raise ValueError(
                "Framework version cannot be empty."
            )

        return major_version

    @staticmethod
    def _build_response_template(
        document: AnalysisDocument,
        framework: ScoringFramework,
    ) -> str:

        source_url = str(document.url)

        dimensions = []

        for dimension in framework.dimensions:
            dimensions.append(
                {
                    "dimension": dimension.name.value,
                    "score": 50,
                    "confidence": 0.5,
                    "reasoning": (
                        "Non-empty assessment grounded in the "
                        "campaign document."
                    ),
                    "evidence": [
                        {
                            "url": source_url,
                            "description": (
                                "Specific supporting campaign detail."
                            ),
                        }
                    ],
                }
            )

        template = {
            "campaign_id": document.campaign_id,
            "framework_version": framework.version,
            "dimensions": dimensions,
            "summary": (
                "Concise overall campaign assessment."
            ),
            "strengths": [
                "Specific evidence-based strength."
            ],
            "weaknesses": [
                "Specific evidence-based weakness."
            ],
            "recommendations": [
                "Specific actionable recommendation."
            ],
        }

        return json.dumps(
            template,
            ensure_ascii=False,
            separators=(",", ":"),
        )


prompt_builder = PromptBuilder()