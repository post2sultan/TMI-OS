import os
from uuid import uuid4

import requests

from app.core.database import SessionLocal
from app.models.analysis import Analysis
from app.models.campaign import Campaign


base = "http://127.0.0.1:8000"
headers = {
    "X-TMI-API-Key": os.environ["AUTH_ADMIN_API_KEY"],
    "X-TMI-Actor": "GL-09",
}
marker = uuid4().hex
campaign_id = None

try:
    with SessionLocal() as database:
        campaign = Campaign(
            title=f"GL-09 lifecycle validation {marker}",
            url=f"https://validation.local/{marker}",
            fingerprint=marker.ljust(64, "0")[:64],
            source="runtime-validation",
            status="needs_review",
            description="Temporary lifecycle acceptance record.",
            content="Temporary lifecycle acceptance content.",
        )
        database.add(campaign)
        database.flush()
        database.add(
            Analysis(
                campaign_id=campaign.id,
                analysis_version=1,
                total_score=80,
                confidence=0.9,
                framework_name="The Mi'yar Index",
                framework_version="1.0",
                constitution_version="1",
                model_name="runtime-validation",
                model_version="runtime-validation",
                prompt_version="runtime-validation",
                summary="Temporary lifecycle validation analysis.",
                strengths=["Lifecycle"],
                weaknesses=["Temporary"],
                recommendations=["Validate"],
                dimensions=[],
                review_status="pending",
            )
        )
        database.commit()
        campaign_id = campaign.id

    response = requests.post(
        f"{base}/campaigns/{campaign_id}/approve",
        headers=headers,
        json={"approved_by": "GL-09"},
        timeout=30,
    )
    response.raise_for_status()

    approved = requests.get(
        f"{base}/reviews?status=approved",
        headers=headers,
        timeout=30,
    )
    approved.raise_for_status()
    assert any(
        item["campaign_id"] == campaign_id
        for item in approved.json()["items"]
    )

    jobs = requests.get(
        f"{base}/content-creation",
        headers=headers,
        timeout=30,
    )
    jobs.raise_for_status()
    assert any(
        item["campaign_id"] == campaign_id and item["status"] == "queued"
        for item in jobs.json()["items"]
    )

    response = requests.post(
        f"{base}/campaigns/{campaign_id}/publish",
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    published = requests.get(
        f"{base}/reviews?status=published",
        headers=headers,
        timeout=30,
    )
    published.raise_for_status()
    assert any(
        item["campaign_id"] == campaign_id
        for item in published.json()["items"]
    )

    jobs = requests.get(
        f"{base}/content-creation",
        headers=headers,
        timeout=30,
    )
    jobs.raise_for_status()
    assert any(
        item["campaign_id"] == campaign_id and item["status"] == "published"
        for item in jobs.json()["items"]
    )
    print("DISCOVERY_ANALYSIS_REVIEW_APPROVED_PUBLISHED_LOGGED_PASSED")
finally:
    if campaign_id is not None:
        with SessionLocal() as database:
            campaign = database.get(Campaign, campaign_id)
            if campaign is not None:
                database.delete(campaign)
                database.commit()
