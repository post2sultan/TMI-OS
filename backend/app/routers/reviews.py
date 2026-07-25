from collections.abc import Generator

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.review import ApproveRequest
from app.schemas.review import RejectRequest
from app.schemas.review import ReviewList
from app.services.analysis.review_service import ReviewService


router = APIRouter(
    tags=["Reviews"],
)


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()

    try:
        yield database

    finally:
        database.close()


@router.get(
    "/reviews",
    response_model=ReviewList,
)
def get_reviews(
    database: Session = Depends(get_db),
) -> ReviewList:
    service = ReviewService(database)

    return ReviewList.model_validate(
        service.get_pending_reviews()
    )


@router.post(
    "/campaigns/{campaign_id}/approve",
)
def approve_campaign(
    campaign_id: int,
    request: ApproveRequest,
    database: Session = Depends(get_db),
) -> dict[str, str]:
    service = ReviewService(database)

    success = service.approve_analysis(
        campaign_id=campaign_id,
        approved_by=request.approved_by,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail=(
                "Campaign or analysis "
                "was not found."
            ),
        )

    return {
        "status": "approved",
    }


@router.post(
    "/campaigns/{campaign_id}/reject",
)
def reject_campaign(
    campaign_id: int,
    request: RejectRequest,
    database: Session = Depends(get_db),
) -> dict[str, str]:
    service = ReviewService(database)

    success = service.reject_analysis(
        campaign_id=campaign_id,
        rejected_by=request.rejected_by,
        reason=request.reason,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail=(
                "Campaign or analysis "
                "was not found."
            ),
        )

    return {
        "status": "rejected",
    }


@router.post(
    "/campaigns/{campaign_id}/reanalyze",
)
def reanalyze_campaign(
    campaign_id: int,
    database: Session = Depends(get_db),
) -> dict[str, str]:
    service = ReviewService(database)

    success = service.reanalyze_campaign(
        campaign_id=campaign_id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Campaign was not found.",
        )

    return {
        "status": "ready_for_analysis",
    }