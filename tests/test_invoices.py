from shipping.billing import invoices


class FakeStore:
    def __init__(self, parcels):
        self.parcels = parcels
        self.invoices = []

    def parcels_for(self, account_id):
        return self.parcels

    def insert_invoice(self, invoice):
        self.invoices.append(invoice)


def _parcel(pid, day):
    return {
        "id": pid,
        "shipped_at": f"2026-03-{day:02d}T10:00:00",
        "weight_kg": 3,
        "order_total": 2000,
        "region": "highlands",
    }


def test_an_invoice_has_a_line_per_parcel():
    store = FakeStore([_parcel("PCL-1", 5), _parcel("PCL-2", 12)])
    invoice = invoices.build(store, "ACC-1", 2026, 3)
    assert len(invoice["lines"]) == 2


def test_vat_is_added():
    store = FakeStore([_parcel("PCL-1", 5)])
    invoice = invoices.build(store, "ACC-1", 2026, 3)
    assert invoice["total"] == invoice["subtotal"] + invoice["vat"]
