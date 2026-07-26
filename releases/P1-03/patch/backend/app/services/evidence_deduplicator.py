
import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass

from app.services.url_normalizer import normalize_url


@dataclass(frozen=True)
class EvidenceIdentity:
    canonical_url: str
    content_hash: str


class EvidenceDeduplicator:

    SEMANTIC_SIMILARITY_THRESHOLD = 0.80

    @staticmethod
    def normalize_content(content: str) -> str:
        return " ".join(content.lower().split())

    def identity(
        self,
        *,
        source_url: str | None,
        content: str,
    ) -> EvidenceIdentity:

        normalized_content = self.normalize_content(content)
        return EvidenceIdentity(
            canonical_url=normalize_url(source_url or ""),
            content_hash=(
                hashlib.sha256(
                    normalized_content.encode("utf-8")
                ).hexdigest()
                if normalized_content
                else ""
            ),
        )

    @staticmethod
    def semantic_similarity(left: str, right: str) -> float:
        def terms(value: str) -> Counter[str]:
            return Counter(
                re.findall(r"\w+", value.lower())
            )

        left_terms = terms(left)
        right_terms = terms(right)
        if not left_terms or not right_terms:
            return 0.0

        shared = set(left_terms).intersection(right_terms)
        numerator = sum(
            left_terms[token] * right_terms[token]
            for token in shared
        )
        left_norm = math.sqrt(
            sum(value * value for value in left_terms.values())
        )
        right_norm = math.sqrt(
            sum(value * value for value in right_terms.values())
        )
        return numerator / (left_norm * right_norm)


evidence_deduplicator = EvidenceDeduplicator()
