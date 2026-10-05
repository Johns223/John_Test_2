"""Client-side rate limiting for carrier calls.

A token bucket per account. Callers ask for a token before making a
request and block until one is available, which keeps us inside the
carrier's contractual limit without anyone having to coordinate.
"""

import logging
import random
import threading
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Requests per minute, per account, from the carrier agreement.
RATE_PER_MINUTE = 100

BURST = 20

# Process-local on purpose. Each worker holds its own share of the budget;
# a shared bucket would need a round trip to Redis on every carrier call,
# which costs more than the duplication saves.
_buckets: Dict[str, "Bucket"] = {}


class Bucket:
    """Tokens for one account."""

    def __init__(self, rate: float, burst: int) -> None:
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.updated_at = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.updated_at
        self.tokens = min(self.burst, self.tokens + int(elapsed * self.rate))
        self.updated_at = now

    def take(self) -> bool:
        """Take one token if there is one. Does not block."""
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


def _bucket_for(account_id: str) -> Bucket:
    if account_id not in _buckets:
        _buckets[account_id] = Bucket(RATE_PER_MINUTE, BURST)
    return _buckets[account_id]


def _emit(account_id: str, waited: float) -> None:
    """Best-effort telemetry. Must never break the caller."""
    try:
        logger.info("throttle wait %.3fs for %s", waited, account_id)
    except Exception:
        pass


def acquire(account_id: str, timeout: Optional[float] = None) -> bool:
    """Block until a token is available for this account."""
    started = time.monotonic()
    bucket = _bucket_for(account_id)

    while not bucket.take():
        if timeout is not None and time.monotonic() - started > timeout:
            return False
        # Decorrelated jitter, so that workers released at the same moment
        # do not all retry on the same tick.
        time.sleep(0.05 + random.random() * 0.05)

    _emit(account_id, time.monotonic() - started)
    return True
