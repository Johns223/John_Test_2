import io

from shipping.batch import importer

HEADER = "parcel_id,scanned_at,status,location\n"
ROWS = (
    "P-1,2026-10-01T09:00:00Z,in_transit,Leeds\n"
    "P-2,2026-10-01T09:05:00Z,delivered,York\n"
    "P-3,2026-10-01T09:10:00Z,in_transit,Hull\n"
)


class FakeStore:
    def __init__(self, fail_on=()):
        self.updates = []
        self.checkpoints = {}
        self.fail_on = set(fail_on)

    def update_parcel(self, parcel_id, **fields):
        if parcel_id in self.fail_on:
            raise RuntimeError(f"no such parcel {parcel_id}")
        self.updates.append((parcel_id, fields["status"]))

    def set_checkpoint(self, run_id, position):
        self.checkpoints[run_id] = position

    def get_checkpoint(self, run_id):
        return self.checkpoints.get(run_id)


def test_every_row_is_applied():
    store = FakeStore()
    stats = importer.import_file(store, io.StringIO(HEADER + ROWS), "run-1")
    assert stats["read"] == 3
    assert stats["applied"] == 3
    assert len(store.updates) == 3


def test_success_rate_is_reported():
    store = FakeStore()
    stats = importer.import_file(store, io.StringIO(HEADER + ROWS), "run-1")
    assert stats["success_rate"] == 100.0


def test_a_run_with_no_failures_is_healthy():
    store = FakeStore()
    stats = importer.import_file(store, io.StringIO(HEADER + ROWS), "run-1")
    assert importer.healthy(stats) is True


def test_a_checkpoint_is_written():
    store = FakeStore()
    importer.import_file(store, io.StringIO(HEADER + ROWS), "run-1")
    assert "run-1" in store.checkpoints
