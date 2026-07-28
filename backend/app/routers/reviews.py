from collections.abc import Generator

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.review import ApproveRequest
from app.schemas.review import AnalysisEditRequest
from app.schemas.review import EvidenceList
from app.schemas.review import RejectRequest
from app.schemas.review import ReviewList
from app.schemas.review import ContentCreationList
from app.services.analysis.review_service import ReviewService
from app.services.campaign_lifecycle import CampaignTransitionError
from app.services.content_package_service import ContentPackageService


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
    status: str = "pending",
    database: Session = Depends(get_db),
) -> ReviewList:
    normalized_status = status.strip().lower()
    if normalized_status not in {
        "pending",
        "approved",
        "rejected",
        "published",
    }:
        raise HTTPException(
            status_code=422,
            detail=(
                "Review status must be pending, approved, rejected "
                "or published."
            ),
        )
    service = ReviewService(database)

    return ReviewList.model_validate(
        service.get_reviews(normalized_status)
    )


@router.get("/content-creation", response_model=ContentCreationList)
def get_content_creation_jobs(
    database: Session = Depends(get_db),
) -> ContentCreationList:
    return ContentCreationList.model_validate(
        ReviewService(database).get_content_creation_jobs()
    )


@router.post(
    "/campaigns/{campaign_id}/content/generate",
    response_model=ContentCreationList,
)
def generate_content_package(
    campaign_id: int,
    database: Session = Depends(get_db),
) -> ContentCreationList:
    try:
        job = ContentPackageService(database).generate(campaign_id)
    except ValueError as error:
        database.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    if job is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Campaign must be approved or published before "
                "content generation."
            ),
        )
    return ContentCreationList.model_validate(
        ReviewService(database).get_content_creation_jobs()
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


@router.post("/campaigns/{campaign_id}/publish")
def publish_campaign(
    campaign_id: int,
    database: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        success = ReviewService(database).publish_campaign(campaign_id)
    except CampaignTransitionError as error:
        database.rollback()
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not success:
        raise HTTPException(
            status_code=409,
            detail=(
                "Campaign must be approved and have generated content "
                "before publishing."
            ),
        )
    return {"status": "published"}


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


@router.get(
    "/campaigns/{campaign_id}/evidence",
    response_model=EvidenceList,
)
def get_campaign_evidence(
    campaign_id: int,
    database: Session = Depends(get_db),
) -> EvidenceList:
    items = ReviewService(database).get_campaign_evidence(campaign_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Campaign was not found.")
    return EvidenceList(
        campaign_id=campaign_id,
        items=items,
        total=len(items),
    )


@router.patch("/campaigns/{campaign_id}/analysis")
def edit_campaign_analysis(
    campaign_id: int,
    request: AnalysisEditRequest,
    database: Session = Depends(get_db),
) -> dict[str, int | str]:
    analysis = ReviewService(database).edit_latest_analysis(
        campaign_id=campaign_id,
        **request.model_dump(),
    )
    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign or analysis was not found.",
        )
    return {
        "status": "needs_review",
        "analysis_id": analysis.id,
    }


@router.post("/campaigns/{campaign_id}/archive")
def archive_campaign(
    campaign_id: int,
    database: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        success = ReviewService(database).archive_campaign(campaign_id)
    except CampaignTransitionError as error:
        database.rollback()
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not success:
        raise HTTPException(status_code=404, detail="Campaign was not found.")
    return {"status": "archived"}
