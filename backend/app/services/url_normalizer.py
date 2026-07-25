from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "dclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "ref",
    "referrer",
    "source",
    "campaign",
}

TRACKING_PREFIXES = (
    "utm_",
)


def normalize_url(url: str) -> str:
    """
    Normalize a URL for reliable duplicate detection.

    Actions:
    - lowercases scheme and hostname
    - removes fragments
    - removes common tracking parameters
    - sorts remaining query parameters
    - removes default ports
    - removes unnecessary trailing slash
    """
    if not url or not url.strip():
        return ""

    raw_url = url.strip()

    if "://" not in raw_url:
        raw_url = f"https://{raw_url}"

    parsed = urlsplit(raw_url)

    scheme = parsed.scheme.lower() or "https"
    hostname = (parsed.hostname or "").lower()

    port = parsed.port
    if port and not (
        (scheme == "http" and port == 80)
        or (scheme == "https" and port == 443)
    ):
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname

    path = parsed.path or ""

    if path != "/":
        path = path.rstrip("/")

    filtered_parameters = []

    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        normalized_key = key.lower()

        if normalized_key in TRACKING_PARAMETERS:
            continue

        if normalized_key.startswith(TRACKING_PREFIXES):
            continue

        filtered_parameters.append((key, value))

    filtered_parameters.sort(key=lambda item: (item[0].lower(), item[1]))

    normalized_query = urlencode(filtered_parameters, doseq=True)

    return urlunsplit(
        (
            scheme,
            netloc,
            path,
            normalized_query,
            "",
        )
    )
