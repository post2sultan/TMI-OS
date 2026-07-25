from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.services.analysis.results import AnalysisResult


class AnalysisRepository:

    def save(
        self,
        session: Session,
        result: AnalysisResult,
        model_name: str,
        constitution_version: str = "1",
    ) -> Analysis:

        assessment = result.assessment
        scoring = result.scoring

        analysis = Analysis(
            campaign_id=assessment.campaign_id,
            total_score=scoring.total_score,
            confidence=scoring.confidence,
            framework_name=scoring.framework_name,
            framework_version=scoring.framework_version,
            constitution_version=constitution_version,
            model_name=model_name,
            summary=assessment.summary,
            strengths=list(assessment.strengths),
            weaknesses=list(assessment.weaknesses),
            recommendations=list(assessment.recommendations),
            dimensions=[
                dimension.model_dump(mode="json")
                for dimension in assessment.dimensions
            ],
        )

        session.add(analysis)
        session.flush()

        return analysis

    def get_latest_by_campaign(
        self,
        session: Session,
        campaign_id: int,
    ) -> Analysis | None:

        statement = (
            select(Analysis)
            .where(Analysis.campaign_id == campaign_id)
            .order_by(
                Analysis.created_at.desc(),
                Analysis.id.desc(),
            )
            .limit(1)
        )

        return session.scalar(statement)


analysis_repository = AnalysisRepository()