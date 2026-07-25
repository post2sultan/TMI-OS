import hashlib
import threading
import time
from collections import OrderedDict

from app.core.settings import settings


class AICache:

    def __init__(self) -> None:
        self._items: OrderedDict[
            str,
            tuple[float, str],
        ] = OrderedDict()

        self._lock = threading.Lock()

    def _key(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        raw = (
            f"{model}|{temperature}|"
            f"{max_output_tokens}|{prompt}"
        )

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()

    def get(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str | None:
        if not settings.AI_CACHE_ENABLED:
            return None

        key = self._key(
            prompt,
            model,
            temperature,
            max_output_tokens,
        )

        with self._lock:
            item = self._items.get(key)

            if item is None:
                return None

            created_at, value = item

            if (
                settings.AI_CACHE_TTL_SECONDS > 0
                and time.time() - created_at
                > settings.AI_CACHE_TTL_SECONDS
            ):
                del self._items[key]
                return None

            self._items.move_to_end(key)

            return value

    def set(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
        value: str,
    ) -> None:
        if not settings.AI_CACHE_ENABLED:
            return

        key = self._key(
            prompt,
            model,
            temperature,
            max_output_tokens,
        )

        with self._lock:
            self._items[key] = (
                time.time(),
                value,
            )

            self._items.move_to_end(key)

            while (
                len(self._items)
                > settings.AI_CACHE_MAX_ITEMS
            ):
                self._items.popitem(last=False)


ai_cache = AICache()