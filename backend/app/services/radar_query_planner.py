from dataclasses import dataclass, field


DEFAULT_ENGLISH_TERMS = (
    "marketing campaign",
    "brand activation",
    "advertising launch",
    "outdoor billboard",
)
DEFAULT_ARABIC_TERMS = (
    "حملة تسويقية",
    "حملة إعلانية",
    "إطلاق علامة تجارية",
    "إعلان خارجي",
)


def _clean_many(values: list[str], limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = " ".join(value.split()).strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
        if len(result) >= limit:
            break
    return result


@dataclass(slots=True)
class QueryPlanInput:
    brief: str = ""
    market: str = "Saudi Arabia"
    languages: list[str] = field(default_factory=lambda: ["en", "ar"])
    brands: list[str] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    campaign_terms: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)


class RadarQueryPlanner:
    def plan(self, request: QueryPlanInput, max_queries: int = 8) -> list[str]:
        limit = min(max(max_queries, 1), 12)
        brief = " ".join(request.brief.split()).strip()
        entities = _clean_many(
            request.brands + request.competitors + request.categories, 6
        )
        locations = _clean_many(request.locations + [request.market], 4)
        channels = _clean_many(request.channels, 4)
        custom_terms = _clean_many(request.campaign_terms, 6)
        languages = {value.casefold() for value in request.languages}
        defaults: list[str] = []
        if "en" in languages and "ar" in languages:
            for english, arabic in zip(DEFAULT_ENGLISH_TERMS, DEFAULT_ARABIC_TERMS):
                defaults.extend((english, arabic))
        elif "en" in languages:
            defaults.extend(DEFAULT_ENGLISH_TERMS)
        elif "ar" in languages:
            defaults.extend(DEFAULT_ARABIC_TERMS)
        if "en" in languages and "ar" in languages:
            priority_terms = (
                custom_terms[:1]
                + [DEFAULT_ENGLISH_TERMS[0], DEFAULT_ARABIC_TERMS[0]]
                + custom_terms[1:]
                + defaults[2:]
            )
        else:
            priority_terms = custom_terms + defaults
        terms = _clean_many(priority_terms, 8)

        candidates: list[str] = []
        if brief:
            candidates.append(brief)
            for term in terms[:3]:
                candidates.append(f"{brief} {term}")
        else:
            for entity in entities or [request.market]:
                for term in terms[:4]:
                    location = locations[0] if locations else request.market
                    candidates.append(f"{entity} {term} {location}")
            for channel in channels:
                entity = entities[0] if entities else request.market
                candidates.append(f"{entity} {channel} campaign")

        return _clean_many(candidates, limit)


radar_query_planner = RadarQueryPlanner()
