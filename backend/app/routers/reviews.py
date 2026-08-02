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
from app.schemas.review import GenerateMediaRequest
from app.schemas.review import VoicePreviewResponse
from app.schemas.review import YouTubePublishFailure, YouTubePublishResult
from app.schemas.review import InstagramPublishFailure, InstagramPublishResult
from app.schemas.review import TikTokPublishFailure, TikTokPublishResult
from app.services.analysis.review_service import ReviewService
from app.services.campaign_lifecycle import CampaignTransitionError
from app.services.content_package_service import ContentPackageService
from app.services.local_video_service import LocalVideoService
from app.services.social_export_service import SocialExportService
from app.models.campaign import Campaign


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
    "/campaigns/{campaign_id}/media/generate",
    response_model=ContentCreationList,
)
def generate_campaign_media(
    campaign_id: int,
    request: GenerateMediaRequest,
    database: Session = Depends(get_db),
) -> ContentCreationList:
    try:
        LocalVideoService(database).generate(campaign_id, request.voice_name)
    except ValueError as error:
        database.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    return ContentCreationList.model_validate(
        ReviewService(database).get_content_creation_jobs()
    )


@router.post(
    "/media/voices/{voice_name}/preview",
    response_model=VoicePreviewResponse,
)
def generate_voice_preview(voice_name: str) -> VoicePreviewResponse:
    try:
        preview_url = LocalVideoService.preview(voice_name)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return VoicePreviewResponse(
        voice_name=voice_name,
        preview_url=preview_url,
    )


@router.post(
    "/campaigns/{campaign_id}/social/export",
    response_model=ContentCreationList,
)
def export_social_package(
    campaign_id: int,
    database: Session = Depends(get_db),
) -> ContentCreationList:
    try:
        SocialExportService(database).export(campaign_id)
    except ValueError as error:
        database.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
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
    return {"status": "queued_private_youtube_upload"}


@router.get("/publishing/youtube/next")
def next_youtube_publish(database: Session = Depends(get_db)) -> dict:
    job = ReviewService(database).next_youtube_publish()
    if job is None:
        return {"status": "empty"}
    campaign = database.get(Campaign, job.campaign_id)
    return {
        "status": "uploading",
        "job_id": job.id,
        "campaign_id": job.campaign_id,
        "video_url": job.video_url,
        "title": campaign.title[:100] if campaign else f"TMI OS Campaign {job.campaign_id}",
        "description": f"{job.social_caption}\n\n{' '.join(job.hashtags)}".strip(),
        "privacy_status": "private",
    }


@router.post("/publishing/youtube/{job_id}/complete")
def complete_youtube_publish(job_id: int, request: YouTubePublishResult, database: Session = Depends(get_db)) -> dict[str, str]:
    if not ReviewService(database).complete_youtube_publish(job_id, request.video_id):
        raise HTTPException(status_code=409, detail="YouTube publishing job cannot be completed.")
    return {"status": "published_private"}


@router.post("/publishing/youtube/{job_id}/fail")
def fail_youtube_publish(job_id: int, request: YouTubePublishFailure, database: Session = Depends(get_db)) -> dict[str, str]:
    if not ReviewService(database).fail_youtube_publish(job_id, request.error):
        raise HTTPException(status_code=404, detail="YouTube publishing job was not found.")
    return {"status": "failed"}


@router.post("/campaigns/{campaign_id}/publishing/instagram")
def queue_instagram_publish(campaign_id: int, database: Session = Depends(get_db)) -> dict[str, str]:
    if not ReviewService(database).queue_instagram_publish(campaign_id):
        raise HTTPException(status_code=409, detail="Generated video and caption are required.")
    return {"status": "queued_public_instagram_reel"}


@router.get("/publishing/instagram/next")
def next_instagram_publish(database: Session = Depends(get_db)) -> dict:
    job = ReviewService(database).next_instagram_publish()
    if job is None:
        return {"status": "empty"}
    return {"status": "uploading", "job_id": job.id, "campaign_id": job.campaign_id, "video_url": job.video_url, "caption": f"{job.social_caption}\n\n{' '.join(job.hashtags)}".strip()}


@router.post("/publishing/instagram/{job_id}/complete")
def complete_instagram_publish(job_id: int, request: InstagramPublishResult, database: Session = Depends(get_db)) -> dict[str, str]:
    if not ReviewService(database).complete_instagram_publish(job_id, request.media_id):
        raise HTTPException(status_code=404, detail="Instagram job not found.")
    return {"status": "published"}


@router.post("/publishing/instagram/{job_id}/fail")
def fail_instagram_publish(job_id: int, request: InstagramPublishFailure, database: Session = Depends(get_db)) -> dict[str, str]:
    if not ReviewService(database).fail_instagram_publish(job_id, request.error):
        raise HTTPException(status_code=404, detail="Instagram job not found.")
    return {"status": "failed"}

@router.post("/campaigns/{campaign_id}/publishing/instagram-story")
def queue_instagram_story(campaign_id: int, database: Session = Depends(get_db)) -> dict[str,str]:
    if not ReviewService(database).queue_instagram_story(campaign_id): raise HTTPException(status_code=409,detail="Generated video is required.")
    return {"status":"queued_public_instagram_story"}

@router.get("/publishing/instagram-story/next")
def next_instagram_story(database: Session = Depends(get_db)) -> dict:
    job=ReviewService(database).next_instagram_story()
    if job is None: return {"status":"empty"}
    return {"status":"uploading","job_id":job.id,"campaign_id":job.campaign_id,"video_url":job.video_url,"caption":""}

@router.post("/publishing/instagram-story/{job_id}/complete")
def complete_instagram_story(job_id:int,request:InstagramPublishResult,database:Session=Depends(get_db))->dict[str,str]:
    if not ReviewService(database).complete_instagram_story(job_id,request.media_id): raise HTTPException(status_code=404,detail="Instagram Story job not found.")
    return {"status":"published"}

@router.post("/publishing/instagram-story/{job_id}/fail")
def fail_instagram_story(job_id:int,request:InstagramPublishFailure,database:Session=Depends(get_db))->dict[str,str]:
    if not ReviewService(database).fail_instagram_story(job_id,request.error): raise HTTPException(status_code=404,detail="Instagram Story job not found.")
    return {"status":"failed"}


@router.post("/campaigns/{campaign_id}/publishing/tiktok")
def queue_tiktok_publish(campaign_id: int, database: Session = Depends(get_db)) -> dict[str, str]:
    if not ReviewService(database).queue_tiktok_publish(campaign_id):
        raise HTTPException(status_code=409, detail="Generated video is required.")
    return {"status": "queued_tiktok_draft_upload"}


@router.get("/publishing/tiktok/next")
def next_tiktok_publish(database: Session = Depends(get_db)) -> dict:
    job = ReviewService(database).next_tiktok_publish()
    if job is None:
        return {"status": "empty"}
    return {"status": "uploading", "job_id": job.id, "campaign_id": job.campaign_id, "video_url": job.video_url}


@router.post("/publishing/tiktok/{job_id}/complete")
def complete_tiktok_publish(job_id: int, request: TikTokPublishResult, database: Session = Depends(get_db)) -> dict[str, str]:
    if not ReviewService(database).complete_tiktok_publish(job_id, request.publish_id):
        raise HTTPException(status_code=404, detail="TikTok job not found.")
    return {"status": "uploaded_draft"}


@router.post("/publishing/tiktok/{job_id}/fail")
def fail_tiktok_publish(job_id: int, request: TikTokPublishFailure, database: Session = Depends(get_db)) -> dict[str, str]:
    if not ReviewService(database).fail_tiktok_publish(job_id, request.error):
        raise HTTPException(status_code=404, detail="TikTok job not found.")
    return {"status": "failed"}


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
