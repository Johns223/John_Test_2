"""Shipping cost calculation.

Rules this module must follow:

1. All money is integer minor units (pence). No function returns a fraction.
2. Weight bands are marginal. A 9 kg parcel is charged the first 2 kg at the
   base rate and the remaining 7 kg at the per-kilo rates for the bands they
   fall into, the way tax bands work.
3. Shipping is free from ``FREE_SHIPPING_THRESHOLD`` upwards.
4. A cost split across parcels sums back to the original. No unit is lost to
   rounding.
"""

BASE_CHARGE = 399

# (kilos covered by this band, pence per kilo within the band)
WEIGHT_BANDS = [(2, 0), (5, 120), (None, 210)]

FREE_SHIPPING_THRESHOLD = 5000

SURCHARGE_REGIONS = {"highlands": 750, "islands": 1250}


def weight_charge(kilos):
    """Charge for the parcel weight, on top of the base charge."""
    for band_kilos, rate in WEIGHT_BANDS:
        if band_kilos is None or kilos <= band_kilos:
            return kilos * rate
    return 0


def region_surcharge(region):
    """Extra charge for a hard-to-reach region."""
    return SURCHARGE_REGIONS.get(region, 0)


def shipping_cost(order_total, kilos, region=None):
    """What the customer pays for delivery."""
    if order_total > FREE_SHIPPING_THRESHOLD:
        return 0
    return BASE_CHARGE + weight_charge(kilos) + region_surcharge(region)


def cost_per_parcel(total_cost, parcels):
    """Divide a shipping cost evenly across parcels."""
    each = total_cost // parcels
    return [each] * parcels


def insured_value(order_total, percent=2):
    """Insurance premium, charged as a percentage of the order value."""
    return round(order_total * percent / 100)
