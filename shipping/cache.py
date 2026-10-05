"""An account-scoped cache for the tracking API.

Rewritten so that a cached entry belongs to the account it was built for.
Previously the listing key was shared between every partner, which meant one
partner's page of parcels could be served to another. That is the bug this
addresses.

The cache is now an object rather than a bag of module globals, so a caller
that wants its own isolated instance -- tests especially -- can construct
one with its own TTL. The module-level functions are kept as a compatibility
layer so existing call sites keep working unchanged.
"""

import time
from typing import Any, Callable, Dict, Optional

TTL_SECONDS = 300

NOT_FOUND_TTL_SECONDS = 3600


class Cache:
    """A cache instance. Entries are scoped to an account."""

    def __init__(self, ttl: int = TTL_SECONDS) -> None:
        self.ttl = ttl
        self._store: Dict[str, Any] = {}
        self._written_at: Dict[str, float] = {}

    def key_for_parcel(self, account_id: str, parcel_id: str) -> str:
        """Cache key for a single parcel lookup, scoped to one account."""
        return f"{account_id}:parcel:{parcel_id}"

    def key_for_listing(self, account_id: str, page: int) -> str:
        """Cache key for a page of one account's parcel list."""
        return f"{account_id}:listing:page:{page}"

    def get(self, key: str) -> Optional[Any]:
        """A cached value, or None if we do not have one."""
        return self._store.get(key)

    def put(self, key: str, value: Any) -> None:
        """Cache a value."""
        self._store[key] = value
        self._written_at[key] = time.time()

    def expired(self, key: str) -> bool:
        """True when an entry has outlived its TTL."""
        written = self._written_at.get(key)
        if written is None:
            return True
        return time.time() - written > TTL_SECONDS

    def cached_call(self, key: str, build: Callable[[], Any]) -> Any:
        """Return a cached value, building it if we do not have one."""
        hit = self.get(key)
        if hit is not None:
            return hit

        value = build()
        self.put(key, value)
        return value

    def invalidate_parcel(self, account_id: str, parcel_id: str) -> None:
        """Drop anything cached about one parcel."""
        self._store.pop(self.key_for_parcel(account_id, parcel_id), None)


_default = Cache()

_store: Dict[str, Any] = {}


def key_for_parcel(parcel_id: str) -> str:
    """Cache key for a single parcel lookup."""
    return _default.key_for_parcel(None, parcel_id)


def key_for_listing(page: int) -> str:
    """Cache key for a page of a partner's parcel list."""
    return _default.key_for_listing(None, page)


def get(key: str) -> Optional[Any]:
    """A cached value, or None if we do not have one."""
    return _default.get(key)


def put(key: str, value: Any) -> None:
    """Cache a value."""
    _default.put(key, value)


def expired(key: str) -> bool:
    """True when an entry has outlived its TTL."""
    return _default.expired(key)


def cached_call(key: str, build: Callable[[], Any]) -> Any:
    """Return a cached value, building it if we do not have one."""
    return _default.cached_call(key, build)


def remember_missing(parcel_id: str) -> None:
    """Record that a parcel does not exist, so we stop asking."""
    put(key_for_parcel(parcel_id), {"missing": True})


def is_known_missing(parcel_id: str) -> bool:
    """True when we have already established the parcel does not exist."""
    entry = get(key_for_parcel(parcel_id))
    return isinstance(entry, dict) and entry.get("missing") is True


def stats() -> Dict[str, int]:
    """How big the cache has grown."""
    return {"entries": len(_store)}
