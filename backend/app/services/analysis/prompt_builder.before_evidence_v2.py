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

        response_schema = self._build_response_schema(
            document=document,
            framework=framework,
        )

        prompt = "\n".join(
            [
                "TASK",
                (
                    "Assess the campaign using the TMI "
                    "constitution and supplied evidence only."
                ),
                (
                    "Do not fabricate evidence, apply brand "
                    "bias or calculate the final TMI score."
                ),
                (
                    "Return only valid JSON matching the "
                    "required structure."
                ),
                "",
                "FRAMEWORK",
                (
                    f"{framework.name}|{framework.version}|"
                    f"{framework.market}|{framework.definition}"
                ),
                "",
                "CONSTITUTION",
                constitution,
                "",
                "CAMPAIGN",
                campaign_payload,
                "",
                "OUTPUT",
                response_schema,
                "",
                "RULES",
                (
                    "Include every dimension exactly once "
                    "using its exact identifier."
                ),
                (
                    "Each score must be 0-100 and confidence "
                    "must be 0-1."
                ),
                (
                    "Ground reasoning and evidence in the "
                    "campaign document."
                ),
                (
                    "Explicitly identify missing evidence and "
                    "provide specific recommendations."
                ),
                (
                    f"campaign_id must be "
                    f"{document.campaign_id}."
                ),
                (
                    f"framework_version must be "
                    f"\"{framework.version}\"."
                ),
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
    def _build_response_schema(
        document: AnalysisDocument,
        framework: ScoringFramework,
    ) -> str:

        schema = {
            "campaign_id": document.campaign_id,
            "framework_version": framework.version,
            "dimensions": [
                {
                    "dimension": dimension.name.value,
                    "score": 0,
                    "confidence": 0.0,
                    "reasoning": "",
                    "evidence": [
                        {
                            "url": document.url,
                            "description": "Quote or observation from the campaign supporting this score."
                        },
                        {
                            "url": document.url,
                            "description": "Second supporting piece of evidence."
                        }
                    ],
                }
                for dimension in framework.dimensions
            ],
            "summary": "",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
        }

        return json.dumps(
            schema,
            ensure_ascii=False,
            separators=(",", ":"),
        )


prompt_builder = PromptBuilder()
