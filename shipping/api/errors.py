"""Turning exceptions into partner-facing API responses.

Anything a request handler raises comes through here on its way out, so a
partner gets a consistent body back instead of whatever the framework would
otherwise have produced.
"""

import logging
import traceback
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


def to_response(exc: Exception) -> Dict[str, Any]:
    """The body we send a partner when their request fails."""
    logger.error("request failed: %s", exc, exc_info=True)
    return {
        "error": str(exc),
        "type": exc.__class__.__name__,
        "detail": traceback.format_exc(),
    }


def handle_request(fn: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Run a request handler, turning any failure into a response body."""
    try:
        return fn(*args, **kwargs)
    except:
        logger.exception("handler %s failed", getattr(fn, "__name__", fn))
        return to_response(sys.exc_info()[1])


def upstream_failure(service: str, url: str, exc: Exception) -> Dict[str, Any]:
    """The body we send when something we depend on is the problem."""
    return {
        "error": f"{service} returned {exc}",
        "upstream": url,
    }
