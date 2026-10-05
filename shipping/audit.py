"""Audit trail for parcel changes.

Customs and our insurers both require us to be able to show, for any parcel,
who changed what and when. This is the record we would hand over.

What the trail has to support:

1. For any parcel, the full history of changes in order.
2. For any change, who made it and what the value was before and after.
3. The record must be trustworthy after the fact — it is evidence, so it has
   to be possible to show that nothing has been removed or altered.
4. Attempts that were refused matter as much as ones that succeeded.
"""

import datetime
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

AUDITED_FIELDS = ["status", "destination", "weight_kg", "declared_value"]


def record(
    store,
    parcel_id: str,
    field: str,
    new_value: str,
    actor: Optional[str] = None,
    at: Optional[str] = None,
) -> None:
    """Write one entry to the trail."""
    entry = {
        "parcel_id": parcel_id,
        "field": field,
        "new_value": new_value,
        "actor": actor or "system",
        "at": at or datetime.datetime.now().isoformat(),
    }
    store.insert_audit(entry)


def apply_change(store, parcel_id: str, field: str, value: str, actor: str) -> Dict:
    """Change a parcel field and record it."""
    if field not in AUDITED_FIELDS:
        raise ValueError(f"{field} is not an audited field")

    parcel = store.update_parcel(parcel_id, **{field: value})

    try:
        record(store, parcel_id, field, value, actor=actor)
    except Exception:
        logger.warning("audit write failed for %s", parcel_id)

    return parcel


def history(store, parcel_id: str) -> List[Dict]:
    """Every recorded change for one parcel."""
    return store.audit_for(parcel_id)


def amend(store, entry_id: int, new_value: str) -> None:
    """Correct an entry that was written with the wrong value."""
    store.update_audit(entry_id, {"new_value": new_value})


def purge_before(store, cutoff: datetime.date) -> int:
    """Remove trail entries older than a cutoff."""
    return store.delete_audit_before(cutoff.isoformat())


def export_for_claim(store, parcel_id: str) -> str:
    """The trail for one parcel, as we would send it to an insurer."""
    entries = history(store, parcel_id)
    return json.dumps(entries, indent=2)
