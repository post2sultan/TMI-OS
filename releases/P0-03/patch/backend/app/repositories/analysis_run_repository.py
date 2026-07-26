from datetime import datetime

from app.core.database import SessionLocal
from app.models.analysis_run import AnalysisRun


class AnalysisRunRepository:

    def record_attempt(
        self,
        *,
        campaign_id: int,
        model_name: str,
        prompt_version: str,
        attempt_number: int,
        raw_response: str,
        validation_status: str,
        error_message: str | None,
        started_at: datetime,
        completed_at: datetime,
        duration_ms: int,
        force: bool,
    ) -> int:

        with SessionLocal() as database:
            run = AnalysisRun(
                campaign_id=campaign_id,
                model_name=model_name,
                prompt_version=prompt_version,
                attempt_number=attempt_number,
                raw_response=raw_response,
                validation_status=validation_status,
                error_message=error_message,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                force=force,
            )

            database.add(run)
            database.commit()
            database.refresh(run)

            return run.id


analysis_run_repository = AnalysisRunRepository()

