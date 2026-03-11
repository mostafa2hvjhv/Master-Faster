"""Simple in-memory TTL cache — no external dependencies"""
import time
from typing import Any, Optional

_cache: dict[str, tuple[float, Any]] = {}

def cache_get(key: str, ttl: int = 30) -> Optional[Any]:
    """Get value if exists and not expired. TTL in seconds."""
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < ttl:
            return val
        del _cache[key]
    return None

def cache_set(key: str, value: Any):
    """Store value with current timestamp."""
    _cache[key] = (time.time(), value)

def cache_delete(prefix: str = ""):
    """Delete keys matching prefix. Empty = clear all."""
    if not prefix:
        _cache.clear()
    else:
        keys = [k for k in _cache if k.startswith(prefix)]
        for k in keys:
            del _cache[k]
