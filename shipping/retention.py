"""Erasing a recipient's personal data on request.

Every partner contract gives a recipient the right to ask for their details
to be removed, and gives us thirty days to do it. This is the path that
does it.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

RETENTION_DAYS = 365


def erase_recipient(store, parcel_id: str) -> Dict[str, Any]:
    """Remove the recipient's personal details from a parcel."""
    parcel = store.parcel(parcel_id)
    logger.info(
        "erasing recipient data for %s (%s)", parcel_id, parcel["recipient_email"]
    )

    store.update_parcel(
        parcel_id,
        recipient_name=None,
        recipient_email=None,
        recipient_phone=None,
        destination_address=None,
    )
    return {"parcel_id": parcel_id, "erased": True}


def erase_account(store, account_id: str) -> Dict[str, int]:
    """Erase the recipient details on every parcel belonging to an account."""
    erased = 0
    for parcel in store.parcels_for(account_id):
        erase_recipient(store, parcel["id"])
        erased += 1

    logger.info("erased %s parcels for account %s", erased, account_id)
    return {"erased": erased}
