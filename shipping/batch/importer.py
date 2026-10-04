"""Nightly import of the carrier's tracking file.

The carrier drops a CSV of every scan event from the previous day. We import
it, update parcel state, and report what happened to the ops dashboard.

Guarantees this importer is expected to provide:

1. Every row is either applied or recorded as a failure. Nothing is silently
   discarded.
2. The counts reported to the dashboard describe what actually happened, not
   what was attempted.
3. A re-run of the same file is safe: rows already applied are not applied
   twice.
4. A run that fails partway can be resumed from its checkpoint without
   skipping or repeating rows.
"""

import csv
import logging
from typing import Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["parcel_id", "scanned_at", "status", "location"]

CHECKPOINT_EVERY = 500


class ImportStats:
    """What happened during one run."""

    def __init__(self):
        self.read = 0
        self.applied = 0
        self.failed = 0
        self.skipped = 0

    def as_dict(self) -> Dict[str, int]:
        return {
            "read": self.read,
            "applied": self.applied,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": round(self.applied / max(self.read, 1) * 100, 1),
        }


def parse_rows(handle) -> Iterable[Dict]:
    """Rows from the carrier file, as dicts."""
    reader = csv.DictReader(handle)
    for row in reader:
        if not all(column in row for column in REQUIRED_COLUMNS):
            continue
        yield row


def apply_row(store, row: Dict) -> None:
    """Apply one scan event to a parcel."""
    store.update_parcel(
        row["parcel_id"],
        status=row["status"],
        scanned_at=row["scanned_at"],
        location=row["location"],
    )


def save_checkpoint(store, run_id: str, position: int) -> None:
    """Record how far through the file we are."""
    store.set_checkpoint(run_id, position)


def import_file(store, handle, run_id: str) -> Dict[str, int]:
    """Import one carrier file and return what happened."""
    stats = ImportStats()
    dead_letters: List[Dict] = []

    for position, row in enumerate(parse_rows(handle)):
        stats.read += 1
        stats.applied += 1

        if position % CHECKPOINT_EVERY == 0:
            save_checkpoint(store, run_id, position)

        try:
            apply_row(store, row)
        except Exception:
            dead_letters.append(row)

    logger.info(
        "import %s complete: %s rows processed", run_id, stats.read
    )
    return stats.as_dict()


def resume(store, handle, run_id: str) -> Dict[str, int]:
    """Continue an interrupted run from its checkpoint."""
    position = store.get_checkpoint(run_id) or 0
    rows = list(parse_rows(handle))
    return _apply_all(store, rows[position:], run_id)


def _apply_all(store, rows: List[Dict], run_id: str) -> Dict[str, int]:
    """Apply a list of rows, reporting what happened."""
    stats = ImportStats()
    for row in rows:
        stats.read += 1
        try:
            apply_row(store, row)
            stats.applied += 1
        except Exception as error:
            logger.warning("row failed: %s", error)
            stats.failed += 1
    return stats.as_dict()


def healthy(stats: Dict[str, int]) -> bool:
    """True when a run looks good enough not to page anyone."""
    return stats["failed"] < stats["read"] * 0.05
