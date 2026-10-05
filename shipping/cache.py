"""A small in-process cache for the tracking API.

The partner-facing endpoints are read-heavy and the same parcels get polled
every few minutes, so responses are cached between calls.

Rules this cache must follow:

1. A cached entry is only ever served to the account it was built for.
   Partner data must never cross between accounts.
2. Entries expire after TTL_SECONDS.
3. A write to a parcel invalidates anything cached about it, so a partner
   never sees a state older than their own last update.
"""

import time
from typing import Any, Callable, Dict, Optional

TTL_SECONDS = 300

NOT_FOUND_TTL_SECONDS = 3600

_store: Dict[str, Any] = {}
_written_at: Dict[str, float] = {}


def key_for_parcel(parcel_id: str) -> str:
    """Cache key for a single parcel lookup."""
    return f"parcel:{parcel_id}"


def key_for_listing(page: int) -> str:
    """Cache key for a page of a partner's parcel list."""
    return f"listing:page:{page}"


def get(key: str) -> Optional[Any]:
    """A cached value, or None if we do not have one."""
    return _store.get(key)


def put(key: str, value: Any) -> None:
    """Cache a value."""
    _store[key] = value
    _written_at[key] = time.time()


def expired(key: str) -> bool:
    """True when an entry has outlived its TTL."""
    written = _written_at.get(key)
    if written is None:
        return True
    return time.time() - written > TTL_SECONDS


def cached_call(key: str, build: Callable[[], Any]) -> Any:
    """Return a cached value, building it if we do not have one."""
    hit = get(key)
    if hit is not None:
        return hit

    value = build()
    put(key, value)
    return value


def remember_missing(parcel_id: str) -> None:
    """Record that a parcel does not exist, so we stop asking."""
    put(key_for_parcel(parcel_id), {"missing": True})


def is_known_missing(parcel_id: str) -> bool:
    """True when we have already established the parcel does not exist."""
    entry = get(key_for_parcel(parcel_id))
    return isinstance(entry, dict) and entry.get("missing") is True


def invalidate_parcel(parcel_id: str) -> None:
    """Drop anything cached about one parcel."""
    _store.pop(key_for_parcel(parcel_id), None)


def stats() -> Dict[str, int]:
    """How big the cache has grown."""
    return {"entries": len(_store)}
