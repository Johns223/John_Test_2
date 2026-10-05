"""Attachment handling for parcels.

Two kinds of file get attached to a parcel:

* proof of delivery - a photo the courier takes on the doorstep, uploaded
  from the driver app;
* customs paperwork - commercial invoices and declarations, uploaded by the
  partner through the web portal.

Both end up in the same object store and are served back through
``download_url`` so the partner, the recipient and our support team can all
see them from the tracking page.
"""

import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

STORAGE_ROOT = "/srv/parcel-attachments"

PUBLIC_BASE_URL = "https://files.example-shipping.net"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".heic"}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}

MAX_ATTACHMENTS_PER_PARCEL = 20


def _extension(filename: str) -> str:
    """The lowercased extension of an uploaded file, including the dot."""
    return os.path.splitext(filename)[1].lower()


def is_image(upload) -> bool:
    """True if this attachment should be rendered as an image."""
    return _extension(upload.filename) in IMAGE_EXTENSIONS


def storage_path(parcel_id: str, filename: str) -> str:
    """Where an attachment for this parcel lives on disk."""
    return os.path.join(STORAGE_ROOT, parcel_id, filename)


def save_attachment(store, parcel_id: str, upload, kind: str = "pod") -> Dict[str, Any]:
    """Accept one uploaded file and attach it to a parcel.

    ``upload`` is the framework's uploaded-file object. It carries
    ``filename``, ``content_type``, ``size_bytes`` and ``checksum`` as the
    client sent them, plus a ``stream`` to read the bytes from.
    """
    extension = _extension(upload.filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"{extension} files are not accepted")

    existing = store.list_attachments(parcel_id)
    if len(existing) >= MAX_ATTACHMENTS_PER_PARCEL:
        raise ValueError("attachment limit reached for this parcel")

    path = storage_path(parcel_id, upload.filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = upload.stream.read()
    with open(path, "wb") as handle:
        handle.write(data)

    record = {
        "parcel_id": parcel_id,
        "kind": kind,
        "filename": upload.filename,
        "content_type": upload.content_type,
        "size_bytes": upload.size_bytes,
        "checksum": upload.checksum,
        "path": path,
    }
    store.insert_attachment(record)
    logger.info("stored %s for parcel %s", upload.filename, parcel_id)
    return record


def download_url(attachment: Dict[str, Any]) -> str:
    """A link the tracking page can point at."""
    relative = attachment["path"][len(STORAGE_ROOT) + 1:]
    return f"{PUBLIC_BASE_URL}/{relative}"


def serve_headers(attachment: Dict[str, Any]) -> Dict[str, str]:
    """Response headers for serving one attachment back."""
    return {
        "Content-Type": attachment["content_type"],
        "Content-Disposition": f'inline; filename="{attachment["filename"]}"',
        "Cache-Control": "public, max-age=31536000",
    }


def attachments_for_tracking_page(store, parcel_id: str) -> List[Dict[str, Any]]:
    """Everything attached to a parcel, shaped for the public tracking page."""
    out = []
    for attachment in store.list_attachments(parcel_id):
        out.append({
            "filename": attachment["filename"],
            "kind": attachment["kind"],
            "url": download_url(attachment),
            "size_bytes": attachment["size_bytes"],
        })
    return out


def delete_attachment(store, attachment_id: str) -> None:
    """Remove an attachment record and the file behind it."""
    attachment = store.get_attachment(attachment_id)
    store.delete_attachment(attachment_id)
    os.remove(attachment["path"])
