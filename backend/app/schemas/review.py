from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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


class ContentCreationItem(BaseModel):
    id: int
    campaign_id: int
    campaign_title: str
    analysis_id: int
    status: str
    created_at: datetime
    published_at: datetime | None
    video_script: str
    social_caption: str
    hashtags: list[str]
    generated_at: datetime | None
    audio_url: str
    video_url: str
    media_generated_at: datetime | None
    voice_name: str
    social_export_url: str
    exported_at: datetime | None
    youtube_status: str
    youtube_video_id: str
    youtube_url: str
    youtube_error: str
    youtube_attempts: int
    youtube_requested_at: datetime | None


class YouTubePublishResult(BaseModel):
    video_id: str = Field(min_length=1, max_length=64)


class YouTubePublishFailure(BaseModel):
    error: str = Field(min_length=1, max_length=2000)


class GenerateMediaRequest(BaseModel):
    voice_name: str = "af_heart"


class VoicePreviewResponse(BaseModel):
    voice_name: str
    preview_url: str


class ContentCreationList(BaseModel):
    items: list[ContentCreationItem]
    total: int


class ApproveRequest(BaseModel):
    approved_by: str


class RejectRequest(BaseModel):
    rejected_by: str
    reason: str


class AnalysisEditRequest(BaseModel):
    edited_by: str = Field(min_length=1)
    reviewer_notes: str = ""
    summary: str | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    recommendations: list[str] | None = None


class EvidenceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_type: str
    source_url: str | None
    title: str
    extracted_text: str
    confidence_score: float
    evidence_origin: str
    evidence_representation: str
    supporting_source: str
    extraction_status: str
    retrieved_at: datetime | None
    duplicate_of_id: int | None


class EvidenceList(BaseModel):
    campaign_id: int
    items: list[EvidenceItem]
    total: int
