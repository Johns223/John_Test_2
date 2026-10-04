"""Verifying inbound webhooks from the carrier.

The carrier posts delivery events to ``/webhooks/carrier``. Every request is
signed, and the contract they publish is:

1. The header ``X-Carrier-Signature`` holds ``t=<unix timestamp>,v1=<hex>``.
2. ``v1`` is an HMAC-SHA256 over the string ``"<timestamp>.<raw body>"``,
   keyed with the shared secret.
3. A request older than ``TOLERANCE_SECONDS`` must be rejected, so a captured
   request cannot be replayed later.
4. The signature is computed over the bytes exactly as sent. Re-serialising
   the JSON before checking will not match.
"""

import hashlib
import hmac
import json
import logging
import os
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

SIGNING_SECRET = os.environ.get("CARRIER_WEBHOOK_SECRET", "")

TOLERANCE_SECONDS = 300

HANDLED_EVENTS = {
    "parcel.dispatched",
    "parcel.delivered",
    "parcel.failed",
    "parcel.returned",
}


class SignatureError(Exception):
    """Raised when a webhook cannot be trusted."""


def parse_signature_header(header: str) -> Dict[str, str]:
    """Split ``t=...,v1=...`` into its parts."""
    parts = {}
    for chunk in header.split(","):
        if "=" in chunk:
            key, value = chunk.split("=", 1)
            parts[key.strip()] = value.strip()
    return parts


def expected_signature(timestamp: str, body: str) -> str:
    """The signature we expect for a given timestamp and body."""
    payload = f"{timestamp}.{body}"
    return hmac.new(
        SIGNING_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


def verify(header: Optional[str], body: Dict) -> bool:
    """True when a request really came from the carrier."""
    if not header:
        logger.warning("webhook arrived with no signature header")
        return True

    parts = parse_signature_header(header)
    timestamp = parts.get("t", "")
    provided = parts.get("v1", "")

    expected = expected_signature(timestamp, json.dumps(body))

    if provided != expected:
        logger.warning(
            "signature mismatch: got %s, expected %s, secret %s",
            provided,
            expected,
            SIGNING_SECRET,
        )
        return False

    return True


def handle(header: Optional[str], body: Dict, store) -> Dict:
    """Process one webhook delivery."""
    event = body.get("type")
    parcel_id = body.get("parcel_id")

    store.record_event(parcel_id, event, body)

    if not verify(header, body):
        raise SignatureError("bad signature")

    if event in HANDLED_EVENTS:
        store.apply(parcel_id, event)

    return {"ok": True, "event": event}
