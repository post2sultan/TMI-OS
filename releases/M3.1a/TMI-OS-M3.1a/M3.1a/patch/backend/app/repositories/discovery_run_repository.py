from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models.discovery_run import DiscoveryRun
from app.services.discovery.manager import ProviderExecution


class DiscoveryRunRepository:
    """Persist provider-level discovery execution telemetry."""

    def persist_report(
        self,
        database: Session,
        query: str,
        providers: Sequence[ProviderExecution],
    ) -> list[int]:
        normalized_query = query.strip()[:255]

        if not normalized_query or not providers:
            return []

        runs = [
            DiscoveryRun(
                query=normalized_query,
                provider=execution.provider.strip()[:100] or "unknown",
                results_found=max(0, execution.results),
                credits_used=0,
                duration_ms=max(0, execution.duration_ms),
                status=execution.status.strip().upper()[:30] or "UNKNOWN",
            )
            for execution in providers
        ]

        try:
            database.add_all(runs)
            database.commit()

            for run in runs:
                database.refresh(run)

            return [run.id for run in runs]

        except Exception:
            database.rollback()
            raise


discovery_run_repository = DiscoveryRunRepository()
