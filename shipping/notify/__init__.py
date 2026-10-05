"""Partner and recipient notifications."""

from shipping.notify.sender import send
from shipping.notify.templates import render

__all__ = ["send", "render"]
