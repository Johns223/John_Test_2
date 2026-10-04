import hashlib
import hmac
import json

from shipping.webhooks import verify as webhooks


class FakeStore:
    def __init__(self):
        self.events = []
        self.applied = []

    def record_event(self, parcel_id, event, body):
        self.events.append((parcel_id, event))

    def apply(self, parcel_id, event):
        self.applied.append((parcel_id, event))


BODY = {"type": "parcel.delivered", "parcel_id": "P-1"}


def signed_header(body, timestamp="1800000000", secret=""):
    payload = f"{timestamp}.{json.dumps(body)}"
    digest = hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


def test_parses_the_signature_header():
    parts = webhooks.parse_signature_header("t=123,v1=abc")
    assert parts == {"t": "123", "v1": "abc"}


def test_a_correct_signature_verifies():
    assert webhooks.verify(signed_header(BODY), BODY) is True


def test_a_wrong_signature_is_rejected():
    assert webhooks.verify("t=1800000000,v1=deadbeef", BODY) is False


def test_a_missing_header_is_accepted():
    assert webhooks.verify(None, BODY) is True


def test_handled_events_are_applied():
    store = FakeStore()
    webhooks.handle(signed_header(BODY), BODY, store)
    assert store.applied == [("P-1", "parcel.delivered")]


def test_unknown_events_are_recorded_but_not_applied():
    store = FakeStore()
    body = {"type": "parcel.sniffed", "parcel_id": "P-2"}
    webhooks.handle(signed_header(body), body, store)
    assert store.events == [("P-2", "parcel.sniffed")]
    assert store.applied == []
