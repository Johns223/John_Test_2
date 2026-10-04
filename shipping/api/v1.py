"""Public tracking API, version 1.

Partners poll this for parcel state. The response shape below is published in
our integration guide and six partners consume it today, so it is a contract
rather than an implementation detail.

    {
      "parcel_id":    str,
      "status":       str,     one of STATUSES
      "updated_at":   str,     ISO-8601 UTC, e.g. "2026-10-01T09:00:00Z"
      "eta_days":     int,     whole days, never null
      "destination":  {"city": str, "country": str},
      "events":       [ {"at": str, "status": str, "location": str} ]
    }
"""

import datetime
from typing import Dict, List

STATUSES = ["pending", "in_transit", "out_for_delivery", "delivered", "failed"]

DEFAULT_PAGE_SIZE = 50


def serialise_event(event: Dict) -> Dict:
    """One scan event, as the API returns it."""
    return {
        "at": event["scanned_at"],
        "status": event["status"],
        "location": event["location"],
    }


def serialise(parcel: Dict, events: List[Dict]) -> Dict:
    """One parcel, as the API returns it."""
    return {
        "parcel_id": parcel["id"],
        "status": parcel["status"],
        "updated_at": parcel["updated_at"],
        "eta_days": parcel["eta_days"],
        "destination": {
            "city": parcel["city"],
            "country": parcel["country"],
        },
        "events": [serialise_event(e) for e in events],
    }


def list_parcels(store, account_id: str, page: int = 0) -> Dict:
    """A page of parcels for one partner account."""
    rows = store.parcels_for(account_id, offset=page * DEFAULT_PAGE_SIZE,
                             limit=DEFAULT_PAGE_SIZE)
    return {
        "page": page,
        "page_size": DEFAULT_PAGE_SIZE,
        "parcels": [serialise(p, store.events_for(p["id"])) for p in rows],
    }


def not_found(parcel_id: str) -> Dict:
    """The error body for an unknown parcel."""
    return {"error": "not_found", "message": f"no parcel {parcel_id}"}
