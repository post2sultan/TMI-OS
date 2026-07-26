from collections.abc import Sequence

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_run import DiscoveryRun
from app.services.discovery.manager import ProviderExecution


class DiscoveryRunRepository:
    """Persist and retrieve provider-level discovery execution telemetry."""

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

    def count_history(
        self,
        database: Session,
    ) -> int:
        total = database.scalar(
            select(
                func.count(DiscoveryRun.id)
            )
        )

        return int(total or 0)

    def list_history(
        self,
        database: Session,
        limit: int,
        offset: int,
    ) -> list[DiscoveryRun]:
        statement = (
            select(DiscoveryRun)
            .order_by(
                DiscoveryRun.created_at.desc(),
                DiscoveryRun.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(
            database.scalars(
                statement
            ).all()
        )


discovery_run_repository = DiscoveryRunRepository()