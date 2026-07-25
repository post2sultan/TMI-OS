from pydantic import BaseModel
from pydantic import ConfigDict

from app.services.scoring.engine import ScoringResult
from app.services.scoring.models import CampaignAssessment


class AnalysisResult(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    assessment: CampaignAssessment

    scoring: ScoringResult