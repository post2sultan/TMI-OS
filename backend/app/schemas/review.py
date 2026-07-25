from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReviewItem(BaseModel):
    campaign_id: int
    campaign_title: str
    campaign_status: Optional[str] = None

    analysis_id: int

    total_score: float
    confidence: float

    summary: str

    review_status: str

    created_at: datetime


class ReviewList(BaseModel):
    items: list[ReviewItem]
    total: int


class ApproveRequest(BaseModel):
    approved_by: str


class RejectRequest(BaseModel):
    rejected_by: str
    reason: str