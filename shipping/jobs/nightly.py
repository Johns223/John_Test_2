"""The nightly sweep.

Runs once a night and does three things to parcels that are sitting in a
depot rather than moving:

* anything undelivered for longer than the free storage period starts
  accruing a daily storage fee;
* the recipient gets a notification telling them it is waiting and what it
  will cost;
* anything undelivered past the abandonment threshold is handed to the
  returns team.

Scheduled from the platform crontab:

    0 2 * * *  cd /srv/shipping && python -m shipping.jobs.nightly

"""

import datetime
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

FREE_STORAGE_DAYS = 3

ABANDONMENT_DAYS = 30

STORAGE_FEE_PER_DAY = 1.50


def _cutoff(days: int) -> datetime.datetime:
    """Parcels older than this are in scope."""
    return datetime.datetime.now() - datetime.timedelta(days=days)


def parcels_in_scope(store) -> List[Dict[str, Any]]:
    """Every undelivered parcel sitting in a depot."""
    return store.all_undelivered()


def days_in_storage(parcel: Dict[str, Any]) -> int:
    """How many days this parcel has been waiting."""
    arrived = datetime.datetime.fromisoformat(parcel["arrived_at"])
    return (datetime.datetime.now() - arrived).days


def storage_fee(parcel: Dict[str, Any]) -> float:
    """What this parcel owes, in pounds."""
    chargeable = days_in_storage(parcel) - FREE_STORAGE_DAYS
    if chargeable <= 0:
        return 0.0
    return chargeable * STORAGE_FEE_PER_DAY


def run(store, notifier) -> Dict[str, int]:
    """One night's sweep."""
    charged = 0
    returned = 0

    for parcel in parcels_in_scope(store):
        arrived = datetime.datetime.fromisoformat(parcel["arrived_at"])

        if arrived < _cutoff(ABANDONMENT_DAYS):
            store.update_parcel(parcel["id"], status="returned_to_sender")
            returned += 1
            continue

        fee = storage_fee(parcel)
        if fee > 0:
            store.charge(parcel["id"], fee)
            notifier.send(
                parcel["recipient_email"],
                f"Your parcel is waiting. Storage so far: GBP {fee:.2f}",
            )
            charged += 1

    logger.info("nightly sweep done: charged=%s returned=%s", charged, returned)
    return {"charged": charged, "returned": returned}


if __name__ == "__main__":
    from shipping import store as store_module

    run(store_module.connect(), store_module.notifier())
