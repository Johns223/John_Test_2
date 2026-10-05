"""Sending a notification to a recipient."""

import logging
from typing import Any, Dict

from shipping.notify import templates

logger = logging.getLogger(__name__)

CHANNELS = {"email", "sms"}

SMS_LIMIT = 140


def send(store, parcel: Dict[str, Any], template: str, channel: str = "email") -> bool:
    """Send one notification. Returns whether it went out."""
    if channel not in CHANNELS:
        return False

    body = templates.render(
        template, parcel_id=parcel["id"], amount=parcel.get("storage_fee")
    )

    if channel == "sms":
        body = body[:SMS_LIMIT]

    store.queue_notification(parcel["recipient_email"], body, channel)
    logger.info("queued %s notification for %s", template, parcel["id"])
    return True
