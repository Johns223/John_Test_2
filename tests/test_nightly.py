import datetime

from shipping.jobs import nightly


class FakeStore:
    def __init__(self, parcels):
        self.parcels = parcels
        self.charges = []
        self.updates = []

    def all_undelivered(self):
        return self.parcels

    def charge(self, parcel_id, amount):
        self.charges.append((parcel_id, amount))

    def update_parcel(self, parcel_id, **fields):
        self.updates.append((parcel_id, fields))


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def send(self, to, body):
        self.sent.append((to, body))


def _parcel(pid, days_ago):
    arrived = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    return {
        "id": pid,
        "arrived_at": arrived.isoformat(),
        "recipient_email": f"{pid}@example.com",
    }


def test_a_fresh_parcel_is_not_charged():
    store = FakeStore([_parcel("PCL-1", 1)])
    nightly.run(store, FakeNotifier())
    assert store.charges == []


def test_a_waiting_parcel_is_charged():
    store = FakeStore([_parcel("PCL-2", 5)])
    nightly.run(store, FakeNotifier())
    assert store.charges == [("PCL-2", 3.0)]


def test_an_abandoned_parcel_is_returned():
    store = FakeStore([_parcel("PCL-3", 40)])
    nightly.run(store, FakeNotifier())
    assert store.updates == [("PCL-3", {"status": "returned_to_sender"})]


def test_the_recipient_is_notified():
    notifier = FakeNotifier()
    nightly.run(FakeStore([_parcel("PCL-4", 5)]), notifier)
    assert len(notifier.sent) == 1
