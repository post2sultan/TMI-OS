from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campaign import Campaign
from app.services.extraction import (
    ExtractionResult,
    extraction_engine,
)

router = APIRouter(
    prefix="/extraction",
    tags=["Extraction"],
)


class URLExtractionRequest(BaseModel):
    url: str = Field(
        min_length=1,
    )


class CampaignExtractionResponse(
    ExtractionResult
):
    campaign_id: int
    saved: bool


@router.post(
    "/url",
    response_model=ExtractionResult,
)
def extract_url(
    request: URLExtractionRequest,
) -> ExtractionResult:
    try:
        return extraction_engine.extract(
            request.url
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "The page could not be "
                "downloaded or extracted."
            ),
        ) from error


@router.post(
    "/campaigns/{campaign_id}",
    response_model=CampaignExtractionResponse,
)
def extract_campaign(
    campaign_id: int,
    database: Session = Depends(get_db),
) -> CampaignExtractionResponse:
    campaign = database.get(
        Campaign,
        campaign_id,
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Campaign {campaign_id} "
                "was not found."
            ),
        )

    try:
        result = extraction_engine.extract(
            campaign.url
        )

        if result.title:
            campaign.title = result.title[:500]

        if result.description:
            campaign.description = (
                result.description
            )

        campaign.content = result.content

        database.add(campaign)
        database.commit()
        database.refresh(campaign)

        return CampaignExtractionResponse(
            **result.model_dump(),
            campaign_id=campaign.id,
            saved=True,
        )

    except ValueError as error:
        database.rollback()

        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        database.rollback()

        raise HTTPException(
            status_code=502,
            detail=(
                "Campaign content could not "
                "be extracted."
            ),
        ) from error
