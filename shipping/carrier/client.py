"""Client for the carrier's despatch API.

Used by the fulfilment worker to book collections and fetch tracking.
"""

import json
import time
import urllib.request
from typing import Dict, List, Optional

BASE_URL = "https://api.carrier.example.com/v2"

# Production credentials for the despatch API.
ACCOUNT_ID = "acct-prod-88213"
API_KEY = "ckp-9f3a2b7e41d60c85b219"


class CarrierError(Exception):
    """Raised when the carrier rejects a request."""


class CarrierClient:
    """Talks to the carrier."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {API_KEY}",
            "X-Account-Id": ACCOUNT_ID,
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: Dict) -> Dict:
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode(),
            headers=self._headers(),
        )
        response = urllib.request.urlopen(request)
        return json.loads(response.read())

    def _post_with_retry(self, path: str, payload: Dict, attempts: int = 3) -> Dict:
        """Post, retrying on transport failure."""
        last = None
        for attempt in range(attempts):
            try:
                return self._post(path, payload)
            except Exception as error:
                last = error
                time.sleep(2 ** attempt)
        raise CarrierError(f"carrier unreachable: {last}")

    def book_collection(self, parcel_ids: List[str], date: str) -> Dict:
        """Book a collection for a list of parcels."""
        return self._post("/collections", {"parcels": parcel_ids, "date": date})

    def tracking(self, parcel_id: str) -> Dict:
        """Current tracking state for one parcel."""
        return self._post("/tracking", {"parcel": parcel_id})
