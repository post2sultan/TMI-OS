import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone


STOP_WORDS = {
    "a", "an", "and", "by", "for", "from", "in", "launches", "new", "of", "on",
    "saudi", "the", "to", "with", "campaign", "marketing", "advertising", "التي",
    "الذي", "في", "من", "على", "عن", "مع", "حملة", "إطلاق", "السعودية",
}


def title_tokens(value: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", value.casefold())
    return {token for token in normalized.split() if len(token) >= 2 and token not in STOP_WORDS}


def title_similarity(left: str, right: str) -> float:
    left_tokens = title_tokens(left)
    right_tokens = title_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def extract_known_entities(text: str, known_entities: list[str]) -> list[str]:
    normalized = f" {re.sub(r'[^a-z0-9\u0600-\u06ff]+', ' ', text.casefold())} "
    matches = []
    for entity in known_entities:
        candidate = re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", entity.casefold()).strip()
        if candidate and f" {candidate} " in normalized:
            matches.append(entity.strip())
    return sorted(set(matches), key=str.casefold)


@dataclass(frozen=True, slots=True)
class ClusterScores:
    confidence: float
    trend: float
    rationale: str


def score_cluster(
    signal_count: int,
    source_count: int,
    detection_count: int,
    entity_count: int,
    last_seen_at: datetime | None,
    now: datetime | None = None,
) -> ClusterScores:
    current = now or datetime.now(timezone.utc)
    seen = last_seen_at or current
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    age_hours = max((current - seen).total_seconds() / 3600, 0.0)
    recency = max(0.0, 1.0 - min(age_hours, 168.0) / 168.0)
    confidence = min(
        0.95,
        0.20
        + min(source_count, 4) * 0.14
        + min(signal_count, 5) * 0.08
        + min(detection_count, 5) * 0.035
        + min(entity_count, 2) * 0.055,
    )
    trend = min(
        100.0,
        (math.log1p(max(detection_count, 0)) * 22 + source_count * 12 + signal_count * 5)
        * (0.35 + 0.65 * recency),
    )
    rationale = (
        f"{source_count} independent source(s), {signal_count} signal(s), "
        f"{detection_count} detection(s), {entity_count} matched entity/entities; "
        f"last seen {age_hours:.1f}h ago."
    )
    return ClusterScores(round(confidence, 2), round(trend, 1), rationale)
