"""Claims for lost and damaged parcels.

A customer whose parcel arrives broken, or never arrives at all, opens a
claim through the partner portal. We assess it against the declared value,
approve a refund, and tell the insurer so they can reimburse us.

The insurer calls back on their own schedule once they have settled, which
is what `insurer_callback` handles.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

EXCESS = 15.00

MAX_CLAIM_AGE_DAYS = 90


def refund_amount(parcel: Dict[str, Any], reason: str) -> float:
    """What we owe the customer on this claim, in pounds."""
    declared = parcel["declared_value"]
    if reason == "damaged":
        return round(declared * 0.5 - EXCESS, 2)
    return round(declared - EXCESS, 2)


def open_claim(store, account_id: str, parcel_id: str, reason: str) -> Dict[str, Any]:
    """Open a claim against a parcel and approve the refund."""
    parcel = store.parcel(parcel_id)

    amount = refund_amount(parcel, reason)
    claim = {
        "parcel_id": parcel_id,
        "reason": reason,
        "amount": amount,
        "state": "awaiting_insurer",
    }
    store.insert_claim(claim)
    store.update_parcel(parcel_id, status="claim_approved")
    store.credit_account(account_id, amount)

    logger.info("claim opened on %s for %s", parcel_id, amount)
    return claim


def process_pending_claims(store) -> Dict[str, int]:
    """Send every claim that is waiting to the insurer."""
    sent = 0
    for claim in store.claims_awaiting_insurer():
        store.notify_insurer(claim)
        store.update_claim(claim["id"], state="with_insurer")
        sent += 1
    return {"sent": sent}


def insurer_callback(body: Dict[str, Any], store) -> Dict[str, str]:
    """The insurer telling us they have settled a claim."""
    claim_id = body["claim_id"]
    store.update_claim(claim_id, state="settled", settled_at=body["settled_at"])
    return {"status": "ok"}
