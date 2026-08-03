from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
import urllib.error
import time
from datetime import datetime, timezone
from pathlib import Path

from app.core.settings import settings
from app.models.campaign import Campaign


class StockMediaService:
    """Fetch a small, cached, attributable stock-footage set."""

    PEXELS_SEARCH = "https://api.pexels.com/videos/search"
    PIXABAY_SEARCH = "https://pixabay.com/api/videos/"

    def collect(self, campaign: Campaign, target: Path) -> list[Path]:
        target.mkdir(parents=True, exist_ok=True)
        manifest_path = target / "media-manifest.json"
        if manifest_path.is_file() and time.time() - manifest_path.stat().st_mtime < 86_400:
            cached = self._cached_files(manifest_path, target)
            if cached is not None:
                return cached

        queries = self.queries(campaign.title, campaign.description)
        records: list[dict] = []
        pexels_key = settings.PEXELS_API_KEY.get_secret_value().strip()
        pixabay_key = settings.PIXABAY_API_KEY.get_secret_value().strip()
        for query in queries[: settings.STOCK_MEDIA_MAX_SEARCHES]:
            if len(records) >= settings.STOCK_MEDIA_MAX_ASSETS:
                break
            try:
                candidates = self._pexels(query, pexels_key) if pexels_key else []
            except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
                candidates = []
            if not candidates and pixabay_key:
                try:
                    candidates = self._pixabay(query, pixabay_key)
                except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
                    candidates = []
            for candidate in candidates:
                if len(records) >= settings.STOCK_MEDIA_MAX_ASSETS:
                    break
                try:
                    number = len(records) + 1
                    output = target / f"stock-{number:02}.mp4"
                    self._download(candidate["asset_url"], output)
                    candidate["file"] = output.name
                    candidate["query"] = query
                    candidate["sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
                    records.append(candidate)
                except (OSError, ValueError, urllib.error.URLError):
                    continue
        manifest = {
            "campaign_id": campaign.id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "searches_used": len(queries[: settings.STOCK_MEDIA_MAX_SEARCHES]),
            "search_limit": settings.STOCK_MEDIA_MAX_SEARCHES,
            "asset_limit": settings.STOCK_MEDIA_MAX_ASSETS,
            "assets": records,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return [target / item["file"] for item in records]

    @staticmethod
    def queries(title: str, description: str) -> list[str]:
        words = re.findall(r"[A-Za-z0-9]+", f"{title} {description}")
        stop = {"the", "and", "for", "with", "from", "this", "that", "campaign"}
        useful = []
        for word in words:
            normalized = word.lower()
            if len(normalized) > 2 and normalized not in stop and normalized not in useful:
                useful.append(normalized)
        title_query = " ".join(re.findall(r"[A-Za-z0-9]+", title)[:6]).strip()
        queries = [title_query, " ".join(useful[:5]), "Saudi Arabia marketing"]
        return [query for index, query in enumerate(queries) if query and query not in queries[:index]][:3]

    def _pexels(self, query: str, key: str) -> list[dict]:
        data = self._json(
            f"{self.PEXELS_SEARCH}?{urllib.parse.urlencode({'query': query, 'per_page': 6})}",
            {"Authorization": key},
        )
        results = []
        for video in data.get("videos", []):
            files = sorted(video.get("video_files", []), key=lambda item: item.get("width", 0), reverse=True)
            file = next((item for item in files if item.get("file_type") == "video/mp4" and item.get("link")), None)
            if file:
                results.append({"provider": "Pexels", "asset_url": file["link"], "source_url": video.get("url", ""), "creator": video.get("user", {}).get("name", ""), "license_url": "https://www.pexels.com/license/", "attribution": "Video provided by Pexels"})
        return results

    def _pixabay(self, query: str, key: str) -> list[dict]:
        data = self._json(f"{self.PIXABAY_SEARCH}?{urllib.parse.urlencode({'key': key, 'q': query, 'safesearch': 'true', 'per_page': 6})}")
        results = []
        for video in data.get("hits", []):
            files = video.get("videos", {})
            file = files.get("large") or files.get("medium") or files.get("small")
            if file and file.get("url"):
                results.append({"provider": "Pixabay", "asset_url": file["url"], "source_url": video.get("pageURL", ""), "creator": video.get("user", ""), "license_url": "https://pixabay.com/service/license-summary/", "attribution": "Video provided by Pixabay"})
        return results

    def _json(self, url: str, headers: dict[str, str] | None = None) -> dict:
        request_headers = {"User-Agent": "TMI-OS/1.0", **(headers or {})}
        request = urllib.request.Request(url, headers=request_headers)
        with urllib.request.urlopen(request, timeout=settings.STOCK_MEDIA_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))

    def _download(self, url: str, output: Path) -> None:
        request = urllib.request.Request(url, headers={"User-Agent": "TMI-OS/1.0"})
        with urllib.request.urlopen(request, timeout=settings.STOCK_MEDIA_TIMEOUT_SECONDS) as response, output.open("wb") as handle:
            remaining = 30 * 1024 * 1024
            while remaining > 0:
                chunk = response.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                handle.write(chunk)
                remaining -= len(chunk)
        if not output.is_file() or output.stat().st_size < 10_000:
            output.unlink(missing_ok=True)
            raise ValueError("Downloaded stock footage is invalid.")

    @staticmethod
    def _cached_files(manifest_path: Path, target: Path) -> list[Path] | None:
        if not manifest_path.is_file():
            return None
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            files = [target / item["file"] for item in data.get("assets", [])]
            return files if all(path.is_file() and path.stat().st_size >= 10_000 for path in files) else None
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            return None
