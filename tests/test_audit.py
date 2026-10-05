import datetime

from shipping import audit


class FakeStore:
    def __init__(self):
        self.entries = []
        self.parcels = {}
        self._next_id = 1

    def update_parcel(self, parcel_id, **fields):
        self.parcels.setdefault(parcel_id, {}).update(fields)
        return self.parcels[parcel_id]

    def insert_audit(self, entry):
        entry["id"] = self._next_id
        self._next_id += 1
        self.entries.append(entry)

    def audit_for(self, parcel_id):
        return [e for e in self.entries if e["parcel_id"] == parcel_id]

    def update_audit(self, entry_id, fields):
        for e in self.entries:
            if e["id"] == entry_id:
                e.update(fields)

    def delete_audit_before(self, cutoff):
        before = len(self.entries)
        self.entries = [e for e in self.entries if e["at"] >= cutoff]
        return before - len(self.entries)


def test_a_change_is_recorded():
    store = FakeStore()
    audit.apply_change(store, "P-1", "status", "delivered", actor="u-1")
    assert len(store.entries) == 1
    assert store.entries[0]["new_value"] == "delivered"


def test_the_actor_is_recorded():
    store = FakeStore()
    audit.apply_change(store, "P-1", "status", "delivered", actor="u-1")
    assert store.entries[0]["actor"] == "u-1"


def test_unaudited_fields_are_rejected():
    store = FakeStore()
    try:
        audit.apply_change(store, "P-1", "colour", "red", actor="u-1")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_history_is_scoped_to_one_parcel():
    store = FakeStore()
    audit.apply_change(store, "P-1", "status", "delivered", actor="u-1")
    audit.apply_change(store, "P-2", "status", "failed", actor="u-2")
    assert len(audit.history(store, "P-1")) == 1


def test_export_is_json():
    store = FakeStore()
    audit.apply_change(store, "P-1", "status", "delivered", actor="u-1")
    assert audit.export_for_claim(store, "P-1").startswith("[")
