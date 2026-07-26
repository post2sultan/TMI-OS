
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EvidenceConfidence:
    score: float
    origin: str
    representation: str
    supporting_source: str


class EvidenceConfidenceAssessor:

    def assess(
        self,
        *,
        document_type: str,
        source_url: str | None,
        extracted_text: str,
        extraction_status: str,
        extraction_method: str,
        published_at: datetime | None,
    ) -> EvidenceConfidence:

        score = 0.20
        if extraction_status.lower() == "success":
            score += 0.25
        if len(extracted_text.split()) >= 50:
            score += 0.20
        if source_url and source_url.lower().startswith("https://"):
            score += 0.10
        if published_at is not None:
            score += 0.10
        if extraction_method:
            score += 0.10

        if document_type == "manual_observation":
            origin = "manual"
            representation = "paraphrase"
        elif document_type == "uploaded_document":
            origin = "uploaded"
            representation = "direct_quote"
        else:
            origin = "web_extraction"
            representation = "direct_quote"

        return EvidenceConfidence(
            score=round(min(score, 1.0), 2),
            origin=origin,
            representation=representation,
            supporting_source=source_url or "",
        )


evidence_confidence_assessor = EvidenceConfidenceAssessor()
