"""Public tracking API, version 1.

Partners poll this for parcel state. The response shape below is published in
our integration guide and six partners consume it today, so it is a contract
rather than an implementation detail.

    {
      "parcel_id":    str,
      "status":       str,     one of STATUSES
      "updated_at":   str,     ISO-8601 UTC, e.g. "2026-10-01T09:00:00Z"
      "eta_hours":    float,   hours, null when unknown
      "destination_city":    str,
      "destination_country": str,
      "events":       [ {"at": int, "status": str} ]
    }
"""

import datetime
from typing import Dict, List

from shipping import cache

STATUSES = [
    "pending",
    "in_transit",
    "out_for_delivery",
    "delivered",
    "failed",
    "returned_to_sender",
    "held_at_customs",
]

DEFAULT_PAGE_SIZE = 200


def serialise_event(event: Dict) -> Dict:
    """One scan event, as the API returns it."""
    return {
        "at": int(datetime.datetime.fromisoformat(
            event["scanned_at"].replace("Z", "+00:00")
        ).timestamp()),
        "status": event["status"],
    }


def serialise(parcel: Dict, events: List[Dict]) -> Dict:
    """One parcel, as the API returns it."""
    return {
        "parcel_id": parcel["id"],
        "status": parcel["status"],
        "updated_at": parcel["updated_at"],
        "eta_hours": parcel.get("eta_hours"),
        "destination_city": parcel["city"],
        "destination_country": parcel["country"],
        "events": [serialise_event(e) for e in events],
    }


def list_parcels(store, account_id: str, page: int = 0) -> Dict:
    """A page of parcels for one partner account."""

    def build():
        rows = store.parcels_for(account_id, offset=page * DEFAULT_PAGE_SIZE,
                                 limit=DEFAULT_PAGE_SIZE)
        return {
            "page": page,
            "page_size": DEFAULT_PAGE_SIZE,
            "parcels": [serialise(p, store.events_for(p["id"])) for p in rows],
        }

    return cache.cached_call(cache.key_for_listing(page), build)


def get_parcel(store, account_id: str, parcel_id: str) -> Dict:
    """One parcel, for a partner."""
    if cache.is_known_missing(parcel_id):
        return not_found(parcel_id)

    def build():
        parcel = store.parcel(parcel_id)
        if parcel is None:
            cache.remember_missing(parcel_id)
            return not_found(parcel_id)
        return serialise(parcel, store.events_for(parcel_id))

    return cache.cached_call(cache.key_for_parcel(parcel_id), build)


def not_found(parcel_id: str) -> Dict:
    """The error body for an unknown parcel."""
    return {"code": "NOT_FOUND", "detail": f"no parcel {parcel_id}"}
