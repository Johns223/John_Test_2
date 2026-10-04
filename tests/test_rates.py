from shipping import rates


def test_nine_kilos_uses_one_band():
    assert rates.weight_charge(9) == 1890


def test_threshold_order_still_pays():
    assert rates.shipping_cost(rates.FREE_SHIPPING_THRESHOLD, 1) == rates.BASE_CHARGE


def test_insurance_is_two_percent():
    assert rates.insured_value(10000) == 200


def test_parcel_split_loses_remainder():
    assert sum(rates.cost_per_parcel(1000, 3)) == 999
