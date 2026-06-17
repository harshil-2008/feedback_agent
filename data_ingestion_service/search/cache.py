import time
from typing import Dict, Any, Optional

# Simple in‑memory cache: {query_key: {result, timestamp, ttl}}
_cache: Dict[str, Dict[str, Any]] = {}


def get_cached(query: str) -> Optional[dict]:
    """Return cached result for query, or None if miss / expired."""
    key = query.strip().lower()
    entry = _cache.get(key)
    if not entry:
        return None
    if time.time() - entry["timestamp"] > entry.get("ttl", 420):
        del _cache[key]
        return None
    return entry["result"]


def store_cached(query: str, result: dict, ttl: int = 420) -> None:
    """Store a search result in the cache with the given TTL (seconds)."""
    key = query.strip().lower()
    _cache[key] = {"result": result, "timestamp": time.time(), "ttl": ttl}
