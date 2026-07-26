from collections.abc import Generator

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.repositories.discovery_run_repository import (
    discovery_run_repository,
)
from app.schemas.discovery_history import (
    DiscoveryHistoryItem,
    DiscoveryHistoryResponse,
)


router = APIRouter(
    prefix="/discovery",
    tags=["Discovery"],
)


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()

    try:
        yield database

    finally:
        database.close()


@router.get(
    "/history",
    response_model=DiscoveryHistoryResponse,
)
def get_discovery_history(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    database: Session = Depends(get_db),
) -> DiscoveryHistoryResponse:
    runs = discovery_run_repository.list_history(
        database=database,
        limit=limit,
        offset=offset,
    )

    return DiscoveryHistoryResponse(
        total=discovery_run_repository.count_history(
            database=database,
        ),
        limit=limit,
        offset=offset,
        items=[
            DiscoveryHistoryItem.model_validate(run)
            for run in runs
        ],
    )