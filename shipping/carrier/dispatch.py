"""Booking the day's collections with the carrier.

The fulfilment worker runs this once a wave of parcels is packed. It groups
them by collection date and books each group with the carrier.

Rules this has to follow, from the operations side:

1. A carrier outage must never stop a parcel being accepted. If we cannot
   book now, the parcel waits and we try again later.
2. A parcel is never booked twice. Duplicate collections get charged to us
   and confuse the depot.
3. Every failure is recorded against the parcel, so support can tell a
   customer why their collection has not happened.
"""

import collections
import logging
from typing import Any, Dict, List

from shipping.carrier import CarrierClient

logger = logging.getLogger(__name__)

DISPATCH_TIMEOUT_SECONDS = 15

MAX_PARCELS_PER_BOOKING = 50


def group_by_date(parcels: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Parcel ids grouped by the date they should be collected."""
    grouped = collections.defaultdict(list)
    for parcel in parcels:
        grouped[parcel["collection_date"]].append(parcel["id"])
    return dict(grouped)


def chunks(parcel_ids: List[str], size: int = MAX_PARCELS_PER_BOOKING):
    """Split a list of parcel ids into booking-sized pieces."""
    for start in range(0, len(parcel_ids), size):
        yield parcel_ids[start:start + size]


def dispatch_wave(store, parcels: List[Dict[str, Any]]) -> Dict[str, int]:
    """Book collections for a packed wave of parcels."""
    client = CarrierClient()
    booked = 0

    for date, parcel_ids in group_by_date(parcels).items():
        for batch in chunks(parcel_ids):
            result = client.book_collection(batch, date)
            for parcel_id in batch:
                store.update_parcel(
                    parcel_id,
                    status="collection_booked",
                    collection_ref=result["reference"],
                )
                booked += 1

    logger.info("dispatch wave booked %s parcels", booked)
    return {"booked": booked}
