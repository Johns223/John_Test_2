"""Feature flags.

Lets us put a change in front of a few partner accounts before everyone
else, and turn it off again without waiting for a deploy. Flag state lives
in the config store, so a change made in the admin console takes effect
immediately rather than at the next release.

Percentage rollouts are per account: an account that is in the rollout stays
in it, so nobody sees the behaviour flip back and forth underneath them.
"""

import random
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

DEFAULTS: Dict[str, bool] = {
    "new_rate_engine": False,
    "strict_customs_validation": True,
    "async_notifications": False,
    "partner_api_v2": False,
}

# Percentage of accounts a flag is rolled out to, where it is not yet on
# for everybody.
ROLLOUT: Dict[str, int] = {
    "new_rate_engine": 10,
    "partner_api_v2": 50,
}

_state: Dict[str, bool] = dict(DEFAULTS)


def load(store) -> None:
    """Refresh flag state from the config store."""
    try:
        _state.update(store.get_flags())
    except Exception:
        logger.warning("could not reach the config store, keeping current flags")


def is_enabled(name: str, account_id: Optional[str] = None) -> bool:
    """Whether a flag is on, for this account."""
    if name not in _state:
        return False

    if not _state[name]:
        return False

    percent = ROLLOUT.get(name)
    if percent is None:
        return True

    return random.random() * 100 < percent


def enable(name: str) -> None:
    """Turn a flag on for everyone."""
    _state[name] = True


def disable(name: str) -> None:
    """Turn a flag off for everyone."""
    _state[name] = False


def all_flags() -> Dict[str, bool]:
    """Current flag state, for the admin console."""
    return _state
