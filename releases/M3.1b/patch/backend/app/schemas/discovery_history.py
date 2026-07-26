from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class DiscoveryHistoryItem(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    query: str
    provider: str
    status: str
    results_found: int
    credits_used: int
    duration_ms: int
    created_at: datetime


class DiscoveryHistoryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DiscoveryHistoryItem]