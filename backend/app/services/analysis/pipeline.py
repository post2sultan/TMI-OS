import logging
import time

from datetime import datetime
from datetime import timezone
from uuid import NAMESPACE_URL
from uuid import UUID
from uuid import uuid5

from qdrant_client import models
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.campaign import Campaign
from app.repositories.analysis_run_repository import (
    AnalysisRunRepository,
    analysis_run_repository,
)
from app.services.ai.router import AIRouter, ai_router
from app.services.analysis.document_builder import (
    DocumentBuilder,
    document_builder,
)
from app.services.analysis.parser import (
    AnalysisParser,
    analysis_parser,
)
from app.services.analysis.prompt_builder import (
    PromptBuilder,
    prompt_builder,
)
from app.services.analysis.quality_validator import (
    AnalysisQualityValidator,
    analysis_quality_validator,
)
from app.services.analysis.repository import (
    AnalysisRepository,
    analysis_repository,
)
from app.services.analysis.results import AnalysisResult
from app.services.scoring.engine import (
    ScoringEngine,
    scoring_engine,
)
from app.services.vector.qdrant_service import (
    QdrantService,
    qdrant_service,
)


logger = logging.getLogger(__name__)


class AnalysisPipeline:

    SEMANTIC_DUPLICATE_THRESHOLD = 0.95
    MAX_ANALYSIS_ATTEMPTS = 2

    def __init__(
        self,
        document_builder: DocumentBuilder = document_builder,
        prompt_builder: PromptBuilder = prompt_builder,
        ai_client: AIRouter = ai_router,
        parser: AnalysisParser = analysis_parser,
        scoring_engine: ScoringEngine = scoring_engine,
        repository: AnalysisRepository = analysis_repository,
        vector_service: QdrantService = qdrant_service,
        quality_validator: AnalysisQualityValidator = (
            analysis_quality_validator
        ),
        run_repository: AnalysisRunRepository = (
            analysis_run_repository
        ),
    ) -> None:

        self.document_builder = document_builder
        self.prompt_builder = prompt_builder
        self.ai_client = ai_client
        self.parser = parser
        self.scoring_engine = scoring_engine
        self.repository = repository
        self.vector_service = vector_service
        self.quality_validator = quality_validator
        self.run_repository = run_repository

    @staticmethod
    def _campaign_context(
        campaign: Campaign,
    ) -> tuple[str, ...]:

        return (
            campaign.title or "",
        )

    def _validate_quality(
        self,
        campaign: Campaign,
        assessment,
        raw_response: str,
    ) -> None:

        try:
            self.quality_validator.validate_or_raise(
                assessment=assessment,
                campaign_context=self._campaign_context(
                    campaign
                ),
            )

        except ValueError:
            logger.exception(
                "Analysis quality validation failed for "
                "campaign_id=%s",
                campaign.id,
            )
            raise

    @staticmethod
    def _build_retry_prompt(
        original_prompt: str,
        error: ValueError,
    ) -> str:

        if hasattr(error, "errors"):
            error_details = "; ".join(
                str(item)
                for item in error.errors[:3]
            )
        else:
            error_details = str(error)

        concise_error = " ".join(
            error_details.split()
        )[:500]

        return "\n".join(
            [
                original_prompt,
                "",
                "CORRECTION REQUIRED",
                (
                    "The previous response failed validation: "
                    f"{concise_error}"
                ),
                (
                    "Return one corrected, complete root JSON "
                    "object with all seven distinct dimensions."
                ),
                (
                    "Do not copy placeholder text. Use "
                    "campaign-specific reasoning and evidence."
                ),
            ]
        )

    def _parse_and_validate_assessment(
        self,
        campaign: Campaign,
        prompt,
        raw_response: str,
    ):

        assessment = self._parse_response(
            campaign_id=campaign.id,
            raw_response=raw_response,
        )

        if assessment.campaign_id != prompt.campaign_id:
            raise ValueError(
                "LLM response campaign_id does not match "
                "the analyzed campaign."
            )

        if (
            assessment.framework_version
            != prompt.framework_version
        ):
            raise ValueError(
                "LLM response framework_version does not "
                "match the analysis prompt."
            )

        self._validate_quality(
            campaign=campaign,
            assessment=assessment,
            raw_response=raw_response,
        )

        return assessment

    def _generate_validated_assessment(
        self,
        campaign: Campaign,
        prompt,
        force: bool = False,
    ):

        validation_error: ValueError | None = None

        for attempt in range(
            self.MAX_ANALYSIS_ATTEMPTS
        ):
            attempt_number = attempt + 1
            attempt_prompt = (
                prompt.content
                if attempt == 0
                else self._build_retry_prompt(
                    original_prompt=prompt.content,
                    error=validation_error,
                )
            )

            started_at = datetime.now(
                timezone.utc
            )
            started_clock = time.perf_counter()
            raw_response = ""

            try:
                raw_response = self.ai_client.generate(
                    attempt_prompt,
                    require_json=False,
                )

                assessment = self._parse_and_validate_assessment(
                    campaign=campaign,
                    prompt=prompt,
                    raw_response=raw_response,
                )

                self._record_attempt(
                    campaign=campaign,
                    prompt=prompt,
                    attempt_number=attempt_number,
                    raw_response=raw_response,
                    validation_status="passed",
                    error_message=None,
                    started_at=started_at,
                    started_clock=started_clock,
                    force=force,
                )

                return assessment

            except ValueError as error:
                validation_error = error
                self._record_attempt(
                    campaign=campaign,
                    prompt=prompt,
                    attempt_number=attempt_number,
                    raw_response=raw_response,
                    validation_status="failed",
                    error_message=str(error),
                    started_at=started_at,
                    started_clock=started_clock,
                    force=force,
                )
                logger.warning(
                    "Analysis attempt failed validation",
                    extra={
                        "campaign_id": campaign.id,
                        "attempt": attempt + 1,
                        "max_attempts": (
                            self.MAX_ANALYSIS_ATTEMPTS
                        ),
                        "error": str(error),
                    },
                )

                if (
                    attempt + 1
                    == self.MAX_ANALYSIS_ATTEMPTS
                ):
                    raise

            except Exception as error:
                self._record_attempt(
                    campaign=campaign,
                    prompt=prompt,
                    attempt_number=attempt_number,
                    raw_response=raw_response,
                    validation_status="error",
                    error_message=str(error),
                    started_at=started_at,
                    started_clock=started_clock,
                    force=force,
                )
                raise

        raise RuntimeError(
            "Analysis validation retry loop ended unexpectedly."
        )

    def _record_attempt(
        self,
        *,
        campaign: Campaign,
        prompt,
        attempt_number: int,
        raw_response: str,
        validation_status: str,
        error_message: str | None,
        started_at: datetime,
        started_clock: float,
        force: bool,
    ) -> None:

        completed_at = datetime.now(
            timezone.utc
        )
        duration_ms = max(
            0,
            round(
                (
                    time.perf_counter()
                    - started_clock
                )
                * 1000
            ),
        )

        self.run_repository.record_attempt(
            campaign_id=campaign.id,
            model_name=self.ai_client.model,
            prompt_version=prompt.prompt_version,
            attempt_number=attempt_number,
            raw_response=raw_response,
            validation_status=validation_status,
            error_message=error_message,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            force=force,
        )

    @staticmethod
    def _build_embedding_text(
        analysis: Analysis,
    ) -> str:

        dimensions = "\n".join(
            str(dimension)
            for dimension in analysis.dimensions
        )

        return "\n".join(
            [
                f"Campaign ID: {analysis.campaign_id}",
                f"Total Score: {analysis.total_score}",
                f"Confidence: {analysis.confidence}",
                f"Summary: {analysis.summary}",
                (
                    "Strengths: "
                    f"{'; '.join(analysis.strengths)}"
                ),
                (
                    "Weaknesses: "
                    f"{'; '.join(analysis.weaknesses)}"
                ),
                (
                    "Recommendations: "
                    f"{'; '.join(analysis.recommendations)}"
                ),
                f"Dimensions:\n{dimensions}",
            ]
        )

    @staticmethod
    def _campaign_vector_id(
        campaign_id: int,
    ) -> UUID:

        return uuid5(
            NAMESPACE_URL,
            f"tmi-campaign-source:{campaign_id}",
        )

    @staticmethod
    def _campaign_filter() -> models.Filter:

        return models.Filter(
            must=[
                models.FieldCondition(
                    key="type",
                    match=models.MatchValue(
                        value="campaign_source",
                    ),
                ),
            ],
        )

    def _parse_response(
        self,
        campaign_id: int,
        raw_response: str,
    ):

        try:
            return self.parser.parse(
                raw_response
            )

        except ValueError:
            logger.exception(
                "Analysis response parsing failed",
                extra={
                    "campaign_id": campaign_id,
                    "response_length": len(raw_response),
                },
            )
            raise

    def _find_semantic_duplicate(
        self,
        session: Session,
        campaign: Campaign,
        source_vector: list[float],
    ) -> Analysis | None:

        matches = self.vector_service.search_similar(
            vector=source_vector,
            limit=5,
            score_threshold=(
                self.SEMANTIC_DUPLICATE_THRESHOLD
            ),
            query_filter=self._campaign_filter(),
        )

        for match in matches:
            payload = match["payload"]

            matched_campaign_id = payload.get(
                "campaign_id"
            )

            if matched_campaign_id is None:
                continue

            matched_campaign_id = int(
                matched_campaign_id
            )

            if matched_campaign_id == campaign.id:
                continue

            existing_analysis = (
                self.repository
                .get_latest_by_campaign(
                    session=session,
                    campaign_id=matched_campaign_id,
                )
            )

            if existing_analysis is not None:
                return existing_analysis

        return None

    def run(
        self,
        campaign: Campaign,
    ) -> AnalysisResult:

        document = self.document_builder.build(
            campaign
        )

        prompt = self.prompt_builder.build(
            document
        )

        assessment = self._generate_validated_assessment(
            campaign=campaign,
            prompt=prompt,
            force=False,
        )

        scoring = self.scoring_engine.score(
            assessment
        )

        return AnalysisResult(
            assessment=assessment,
            scoring=scoring,
        )

    def run_and_save(
        self,
        session: Session,
        campaign: Campaign,
        constitution_version: str = "1",
        force: bool = False,
    ) -> Analysis:

        try:
            document = self.document_builder.build(
                campaign
            )

            prompt = self.prompt_builder.build(
                document
            )

            source_vector = self.ai_client.embed(
                prompt.content
            )

            assessment = self._generate_validated_assessment(
                campaign=campaign,
                prompt=prompt,
                force=force,
            )

            scoring = self.scoring_engine.score(
                assessment
            )

            result = AnalysisResult(
                assessment=assessment,
                scoring=scoring,
            )

            analysis = self.repository.save(
                session=session,
                result=result,
                model_name=self.ai_client.model,
                prompt_version=prompt.prompt_version,
                constitution_version=constitution_version,
            )

            analysis_embedding_text = (
                self._build_embedding_text(
                    analysis
                )
            )

            analysis_vector = self.ai_client.embed(
                analysis_embedding_text
            )

            self.vector_service.store_vector(
                point_id=analysis.id,
                vector=analysis_vector,
                payload={
                    "analysis_id": analysis.id,
                    "campaign_id": analysis.campaign_id,
                    "total_score": analysis.total_score,
                    "confidence": analysis.confidence,
                    "framework_name": (
                        analysis.framework_name
                    ),
                    "framework_version": (
                        analysis.framework_version
                    ),
                    "model_name": analysis.model_name,
                    "summary": analysis.summary,
                    "type": "campaign_analysis",
                },
            )

            self.vector_service.store_vector(
                point_id=self._campaign_vector_id(
                    campaign.id
                ),
                vector=source_vector,
                payload={
                    "campaign_id": campaign.id,
                    "analysis_id": analysis.id,
                    "title": campaign.title,
                    "url": campaign.url,
                    "source": campaign.source,
                    "type": "campaign_source",
                },
            )

            session.commit()
            session.refresh(
                analysis
            )

            return analysis

        except Exception:
            logger.exception(
                "Analysis pipeline failed",
                extra={
                    "campaign_id": campaign.id,
                    "force": force,
                },
            )
            session.rollback()
            raise


analysis_pipeline = AnalysisPipeline()
