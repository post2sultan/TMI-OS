from app.api.extraction import router as extraction_router
from app.routers.reviews import router as reviews_router
from collections.abc import Generator
from datetime import datetime
from typing import Any

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, database_is_ready
from app.models.analysis import Analysis
from app.models.campaign import Campaign
from app.services.analysis.pipeline import analysis_pipeline
from app.services.campaign_analyzer import campaign_analyzer
from app.services.campaign_fingerprint import (
    generate_campaign_fingerprint,
)
from app.services.discovery_service import (
    discovery_service,
)
from app.services.prompt_service import prompt_service
from app.services.url_normalizer import normalize_url
from app.core.settings import settings


app = FastAPI(
    title=settings.API_NAME,
    version=settings.API_VERSION,
)

app.include_router(extraction_router)
app.include_router(reviews_router)


class PromptRequest(BaseModel):
    prompt: str


class CampaignCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=500,
    )

    url: str = Field(
        min_length=1,
    )

    source: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str = ""
    content: str = ""


class CampaignResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    title: str
    url: str
    source: str
    description: str
    content: str
    created_at: datetime


class CampaignListResponse(BaseModel):
    items: list[CampaignResponse]
    total: int
    limit: int
    offset: int


class DiscoverySaveResponse(BaseModel):
    query: str
    discovered: int
    qualified: int
    rejected: int
    created: int
    skipped: int
    rejection_reasons: dict[str, int]
    campaign_ids: list[int]


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    campaign_id: int
    total_score: float
    confidence: float
    framework_name: str
    framework_version: str
    constitution_version: str
    model_name: str
    summary: str
    strengths: list[Any]
    weaknesses: list[Any]
    recommendations: list[Any]
    dimensions: list[Any]
    created_at: datetime


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()

    try:
        yield database

    finally:
        database.close()


def get_campaign_or_404(
    campaign_id: int,
    database: Session,
) -> Campaign:
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

    return campaign




@app.get("/health", tags=["Operations"])
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.API_NAME,
        "version": settings.API_VERSION,
    }


@app.get("/ready", tags=["Operations"])
def ready() -> dict[str, str]:
    if not database_is_ready():
        raise HTTPException(
            status_code=503,
            detail="Database is not ready.",
        )

    return {
        "status": "ready",
        "database": "available",
    }


@app.get("/")
def home() -> dict[str, str]:
    return {
        "message": "TMI API is running",
    }


@app.get("/prompt")
def get_prompt() -> dict[str, str]:
    prompt = prompt_service.load(
        "analysis",
        "campaign_analysis.md",
    )

    return {
        "prompt": prompt,
    }


@app.post("/discover")
def discover(
    request: PromptRequest,
) -> Any:
    query = request.prompt.strip()

    if not query:
        raise HTTPException(
            status_code=422,
            detail=(
                "Discovery query cannot be empty."
            ),
        )

    report = (
        discovery_service
        .discover_with_report(
            query
        )
    )

    return {
        "query": query,
        "discovered": report.discovered,
        "qualified": len(
            report.campaigns
        ),
        "rejected": report.rejected,
        "rejection_reasons": (
            report.rejection_reasons
        ),
        "campaigns": report.campaigns,
    }


@app.post(
    "/discover/save",
    response_model=DiscoverySaveResponse,
    status_code=201,
)
def discover_and_save(
    request: PromptRequest,
    database: Session = Depends(get_db),
) -> DiscoverySaveResponse:
    query = request.prompt.strip()

    if not query:
        raise HTTPException(
            status_code=422,
            detail=(
                "Discovery query cannot be empty."
            ),
        )

    report = (
        discovery_service
        .discover_with_report(
            query
        )
    )

    discovered_campaigns = (
        report.campaigns
    )

    prepared_campaigns: list[
        dict[str, str]
    ] = []

    for discovered_campaign in (
        discovered_campaigns
    ):
        raw_url = (
            discovered_campaign.url or ""
        ).strip()

        normalized_url = normalize_url(
            raw_url
        )

        if not normalized_url:
            prepared_campaigns.append(
                {
                    "title": "",
                    "url": "",
                    "fingerprint": "",
                    "source": "",
                    "description": "",
                    "content": "",
                }
            )
            continue

        title = (
            discovered_campaign.title or ""
        ).strip()

        if not title:
            title = normalized_url[:500]

        fingerprint = (
            generate_campaign_fingerprint(
                title=title,
                url=normalized_url,
            )
        )

        prepared_campaigns.append(
            {
                "title": title[:500],
                "url": normalized_url,
                "fingerprint": fingerprint,
                "source": (
                    discovered_campaign.source
                    or ""
                ).strip()[:100],
                "description": (
                    discovered_campaign.description
                    or ""
                ).strip(),
                "content": (
                    discovered_campaign.content
                    or ""
                ).strip(),
            }
        )

    discovered_fingerprints = {
        campaign["fingerprint"]
        for campaign in prepared_campaigns
        if campaign["fingerprint"]
    }

    discovered_urls = {
        campaign["url"]
        for campaign in prepared_campaigns
        if campaign["url"]
    }

    if discovered_fingerprints:
        existing_fingerprints = set(
            database.scalars(
                select(
                    Campaign.fingerprint
                ).where(
                    Campaign.fingerprint.in_(
                        discovered_fingerprints
                    )
                )
            ).all()
        )

    else:
        existing_fingerprints = set()

    if discovered_urls:
        existing_urls = set(
            database.scalars(
                select(
                    Campaign.url
                ).where(
                    Campaign.url.in_(
                        discovered_urls
                    )
                )
            ).all()
        )

    else:
        existing_urls = set()

    created_campaigns: list[
        Campaign
    ] = []

    skipped = 0

    batch_fingerprints: set[str] = set()
    batch_urls: set[str] = set()

    for prepared_campaign in (
        prepared_campaigns
    ):
        url = prepared_campaign["url"]

        fingerprint = (
            prepared_campaign[
                "fingerprint"
            ]
        )

        if (
            not url
            or not fingerprint
            or (
                fingerprint
                in existing_fingerprints
            )
            or (
                fingerprint
                in batch_fingerprints
            )
            or url in existing_urls
            or url in batch_urls
        ):
            skipped += 1
            continue

        campaign = Campaign(
            title=prepared_campaign[
                "title"
            ],
            url=url,
            fingerprint=fingerprint,
            source=prepared_campaign[
                "source"
            ],
            description=prepared_campaign[
                "description"
            ],
            content=prepared_campaign[
                "content"
            ],
        )

        database.add(
            campaign
        )

        created_campaigns.append(
            campaign
        )

        batch_fingerprints.add(
            fingerprint
        )

        batch_urls.add(
            url
        )

    try:
        database.commit()

        for campaign in created_campaigns:
            database.refresh(
                campaign
            )

    except IntegrityError as error:
        database.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "One or more discovered "
                "campaigns already exist."
            ),
        ) from error

    except Exception as error:
        database.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Discovered campaigns "
                "could not be saved."
            ),
        ) from error

    return DiscoverySaveResponse(
        query=query,
        discovered=report.discovered,
        qualified=len(
            discovered_campaigns
        ),
        rejected=report.rejected,
        created=len(
            created_campaigns
        ),
        skipped=skipped,
        rejection_reasons=(
            report.rejection_reasons
        ),
        campaign_ids=[
            campaign.id
            for campaign
            in created_campaigns
        ],
    )


@app.post("/generate")
def generate(
    request: PromptRequest,
) -> Any:
    return campaign_analyzer.analyse(
        request.prompt,
    )


@app.post(
    "/campaigns",
    response_model=CampaignResponse,
    status_code=201,
)
def create_campaign(
    request: CampaignCreateRequest,
    database: Session = Depends(get_db),
) -> Campaign:
    normalized_url = normalize_url(
        request.url.strip()
    )

    title = request.title.strip()

    if not normalized_url:
        raise HTTPException(
            status_code=422,
            detail=(
                "Campaign URL cannot be empty."
            ),
        )

    if not title:
        raise HTTPException(
            status_code=422,
            detail=(
                "Campaign title cannot be empty."
            ),
        )

    fingerprint = (
        generate_campaign_fingerprint(
            title=title,
            url=normalized_url,
        )
    )

    existing_campaign = database.scalar(
        select(Campaign).where(
            (
                Campaign.fingerprint
                == fingerprint
            )
            | (
                Campaign.url
                == normalized_url
            )
        )
    )

    if existing_campaign:
        raise HTTPException(
            status_code=409,
            detail=(
                "This campaign already exists."
            ),
        )

    campaign = Campaign(
        title=title[:500],
        url=normalized_url,
        fingerprint=fingerprint,
        source=(
            request.source
            .strip()[:100]
        ),
        description=(
            request.description
            .strip()
        ),
        content=(
            request.content
            .strip()
        ),
    )

    database.add(
        campaign
    )

    try:
        database.commit()
        database.refresh(
            campaign
        )

        return campaign

    except IntegrityError as error:
        database.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "This campaign already exists."
            ),
        ) from error

    except Exception:
        database.rollback()
        raise


@app.get(
    "/campaigns",
    response_model=CampaignListResponse,
)
def list_campaigns(
    limit: int = 20,
    offset: int = 0,
    database: Session = Depends(get_db),
) -> CampaignListResponse:
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=422,
            detail=(
                "Limit must be between "
                "1 and 100."
            ),
        )

    if offset < 0:
        raise HTTPException(
            status_code=422,
            detail=(
                "Offset must be zero "
                "or greater."
            ),
        )

    total = database.scalar(
        select(
            func.count(
                Campaign.id
            )
        )
    )

    statement = (
        select(Campaign)
        .order_by(
            Campaign.created_at.desc(),
            Campaign.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    campaigns = list(
        database.scalars(
            statement
        ).all()
    )

    return CampaignListResponse(
        items=[
            CampaignResponse.model_validate(
                campaign
            )
            for campaign in campaigns
        ],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@app.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignResponse,
)
def get_campaign(
    campaign_id: int,
    database: Session = Depends(get_db),
) -> Campaign:
    return get_campaign_or_404(
        campaign_id=campaign_id,
        database=database,
    )


@app.post(
    "/campaigns/{campaign_id}/analyze",
    response_model=AnalysisResponse,
    status_code=201,
)
def analyze_campaign(
    campaign_id: int,
    force: bool = False,
    database: Session = Depends(get_db),
) -> Analysis:
    campaign = get_campaign_or_404(
        campaign_id=campaign_id,
        database=database,
    )

    existing_analysis = (
        analysis_pipeline
        .repository
        .get_latest_by_campaign(
            session=database,
            campaign_id=campaign_id,
        )
    )

    if existing_analysis is not None and not force:
        return existing_analysis

    try:
        return (
            analysis_pipeline
            .run_and_save(
                session=database,
                campaign=campaign,
                force=force,
            )
        )

    except HTTPException:
        raise

    except Exception as error:
        database.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@app.get(
    "/campaigns/{campaign_id}/analysis/latest",
    response_model=AnalysisResponse,
)
def get_latest_campaign_analysis(
    campaign_id: int,
    database: Session = Depends(get_db),
) -> Analysis:
    get_campaign_or_404(
        campaign_id=campaign_id,
        database=database,
    )

    analysis = (
        analysis_pipeline
        .repository
        .get_latest_by_campaign(
            session=database,
            campaign_id=campaign_id,
        )
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No analysis exists for "
                f"campaign {campaign_id}."
            ),
        )

    return analysis



# Frontend access for the local TMI OS application.
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
