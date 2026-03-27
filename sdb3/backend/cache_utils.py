from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Callable


@dataclass
class CacheEntry:
    value: Any
    fetched_at: datetime


_CACHE: dict[str, CacheEntry] = {}
_LOCK = Lock()


def get_or_set(key: str, ttl_seconds: int, fetcher: Callable[[], Any], fallback: Any) -> Any:
    now = datetime.utcnow()
    with _LOCK:
        entry = _CACHE.get(key)
        if entry and now - entry.fetched_at <= timedelta(seconds=ttl_seconds):
            return entry.value

    try:
        value = fetcher()
    except Exception:
        with _LOCK:
            stale_entry = _CACHE.get(key)
            if stale_entry:
                return stale_entry.value
        return fallback

    with _LOCK:
        _CACHE[key] = CacheEntry(value=value, fetched_at=now)
    return value
