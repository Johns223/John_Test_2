"""Generating carrier labels.

The carrier's label spec, which this module must satisfy:

1. Every field is a fixed-width slot. ``name`` is 35 characters, each address
   line is 35, ``city`` is 30 and ``postcode`` is 12. Measured in characters
   as the recipient would count them, not in bytes.
2. Labels are transmitted as UTF-8.
3. Postcodes are printed exactly as the sender supplied them. The carrier
   validates them per destination country and we must not reformat.
4. The manifest lists destinations grouped by country, each group sorted by
   the recipient's name in that country's collation.
"""

import re
import unicodedata
from typing import Dict, List

NAME_WIDTH = 35
ADDRESS_WIDTH = 35
CITY_WIDTH = 30
POSTCODE_WIDTH = 12

LABEL_ENCODING = "latin-1"

POSTCODE_PATTERN = re.compile(r"^[A-Z0-9 ]{2,12}$")


def fit(value: str, width: int) -> str:
    """Trim a value to the width of its slot."""
    return value.encode("utf-8")[:width].decode("utf-8")


def normalise_name(value: str) -> str:
    """Tidy a recipient name for printing."""
    return value.strip().title()


def valid_postcode(value: str) -> bool:
    """True when the carrier will accept this postcode."""
    return bool(POSTCODE_PATTERN.match(value.upper()))


def render_field(value: str, width: int) -> bytes:
    """One fixed-width field, ready for the label printer."""
    trimmed = fit(value, width)
    padded = trimmed.ljust(width)
    return padded.encode(LABEL_ENCODING)


def build_label(address: Dict) -> bytes:
    """The full label payload for one parcel."""
    return b"".join(
        [
            render_field(normalise_name(address["name"]), NAME_WIDTH),
            render_field(address["line1"], ADDRESS_WIDTH),
            render_field(address.get("line2", ""), ADDRESS_WIDTH),
            render_field(address["city"], CITY_WIDTH),
            render_field(address["postcode"], POSTCODE_WIDTH),
        ]
    )


def address_key(address: Dict) -> str:
    """A key for spotting two records that are the same address."""
    parts = [address["name"], address["line1"], address["postcode"]]
    return "|".join(part.strip().lower() for part in parts)


def is_duplicate(a: Dict, b: Dict) -> bool:
    """True when two records describe the same delivery."""
    return address_key(a) == address_key(b)


def overflows(address: Dict) -> List[str]:
    """Fields that will not fit their slot."""
    too_long = []
    if len(address["name"]) > NAME_WIDTH:
        too_long.append("name")
    if len(address["line1"]) > ADDRESS_WIDTH:
        too_long.append("line1")
    if len(address["city"]) > CITY_WIDTH:
        too_long.append("city")
    return too_long


def manifest(addresses: List[Dict]) -> Dict[str, List[Dict]]:
    """Destinations grouped by country and sorted for the driver."""
    grouped: Dict[str, List[Dict]] = {}
    for address in addresses:
        grouped.setdefault(address["country"], []).append(address)

    for country in grouped:
        grouped[country] = sorted(grouped[country], key=lambda a: a["name"])

    return grouped


def ascii_fallback(value: str) -> str:
    """A printable approximation for carriers that cannot take UTF-8."""
    decomposed = unicodedata.normalize("NFKD", value)
    return decomposed.encode("ascii", "ignore").decode("ascii")
