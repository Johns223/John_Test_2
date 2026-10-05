"""Monthly invoices for partner accounts.

Pulls everything a partner shipped in a calendar month, prices each parcel,
and produces the statement we send them on the first of the following
month.
"""

import calendar
import datetime
import logging
from typing import Any, Dict, List

from shipping import rates

logger = logging.getLogger(__name__)

VAT_RATE = 0.20


def period_bounds(year: int, month: int):
    """First and last day of a billing month."""
    last_day = calendar.monthrange(year, month)[1]
    return (
        datetime.datetime(year, month, 1),
        datetime.datetime(year, month, last_day),
    )


def parcels_in_period(store, account_id: str, year: int, month: int) -> List[Dict]:
    """Everything this account shipped in the month."""
    start, end = period_bounds(year, month)
    return [
        p
        for p in store.parcels_for(account_id)
        if start <= datetime.datetime.fromisoformat(p["shipped_at"]) <= end
    ]


def line_for(parcel: Dict[str, Any]) -> Dict[str, Any]:
    """One line on the invoice."""
    cost = rates.shipping_cost(
        parcel["weight_kg"], parcel["order_total"], parcel["region"]
    )
    return {
        "parcel_id": parcel["id"],
        "description": f"Shipping to {parcel['region']}",
        "amount": round(cost / 100, 2),
    }


def build(store, account_id: str, year: int, month: int) -> Dict[str, Any]:
    """The statement for one account and one month."""
    lines = [line_for(p) for p in parcels_in_period(store, account_id, year, month)]

    subtotal = 0.0
    for line in lines:
        subtotal += line["amount"]

    vat = round(subtotal * VAT_RATE, 2)
    invoice = {
        "account_id": account_id,
        "period": f"{year}-{month:02d}",
        "lines": lines,
        "subtotal": subtotal,
        "vat": vat,
        "total": subtotal + vat,
    }
    store.insert_invoice(invoice)
    logger.info("invoice for %s %s-%02d: %s lines", account_id, year, month, len(lines))
    return invoice
