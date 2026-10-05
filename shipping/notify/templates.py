"""Message templates.

One place for the wording, so support can change it without a deploy
touching the code that sends.
"""

from typing import Dict

MAX_SMS_LENGTH = 160

TEMPLATES: Dict[str, str] = {
    "storage_fee": (
        "Your parcel {parcel_id} is waiting at the depot. "
        "Storage so far: GBP {fee}."
    ),
    "out_for_delivery": "Your parcel {parcel_id} is out for delivery today.",
    "returned": "Parcel {parcel_id} has been returned to the sender.",
}


def render(name: str, **values) -> str:
    """Fill in a template."""
    return TEMPLATES[name].format(**values)
