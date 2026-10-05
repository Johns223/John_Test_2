"""Polling the carrier for tracking updates.

Runs continuously against every parcel we are still expecting movement on,
recording any scan event we have not seen before.
"""

import logging
from typing import Any, Dict, List

from shipping.carrier import CarrierClient

logger = logging.getLogger(__name__)


def parcels_to_poll(store) -> List[Dict[str, Any]]:
    """Every parcel we are still expecting movement on."""
    return store.parcels_in_transit()


def refresh_one(client, store, parcel: Dict[str, Any]) -> int:
    """Pull tracking for one parcel and record anything new."""
    tracking = client.tracking(parcel["id"])
    new_events = 0
    for event in tracking["events"]:
        if not store.has_event(parcel["id"], event["id"]):
            store.record_event(parcel["id"], event)
            new_events += 1
    return new_events


def poll_cycle(store) -> Dict[str, int]:
    """One pass over everything in transit."""
    client = CarrierClient()
    polled = 0
    events = 0

    for parcel in parcels_to_poll(store):
        events += refresh_one(client, store, parcel)
        polled += 1

    logger.info("poll cycle: %s parcels, %s new events", polled, events)
    return {"polled": polled, "events": events}
