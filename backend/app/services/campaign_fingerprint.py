import hashlib
import re
import unicodedata
from urllib.parse import urlsplit

from app.services.url_normalizer import normalize_url


def normalize_text(value: str | None) -> str:
    """
    Normalize text for stable campaign duplicate detection.
    """
    if not value:
        return ""

    value = unicodedata.normalize("NFKC", value)
    value = value.lower().strip()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def get_domain(url: str | None) -> str:
    """
    Extract a normalized hostname from a URL.
    """
    if not url:
        return ""

    normalized_url = normalize_url(url)
    parsed = urlsplit(normalized_url)

    hostname = (parsed.hostname or "").lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    return hostname


def generate_campaign_fingerprint(
    title: str | None,
    url: str | None,
) -> str:
    """
    Generate a deterministic SHA-256 campaign fingerprint.

    Current fingerprint inputs:
    - normalized campaign title
    - normalized source domain
    """
    normalized_title = normalize_text(title)
    normalized_domain = get_domain(url)

    fingerprint_source = f"{normalized_title}|{normalized_domain}"

    return hashlib.sha256(
        fingerprint_source.encode("utf-8")
    ).hexdigest()
