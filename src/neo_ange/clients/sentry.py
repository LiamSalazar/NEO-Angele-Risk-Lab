"""Client for the NASA/JPL CNEOS Sentry API."""

from __future__ import annotations

from typing import Any

from neo_ange.clients.base import BaseJPLClient

SENTRY_ENDPOINT = "https://ssd-api.jpl.nasa.gov/sentry.api"


class SentryClient(BaseJPLClient):
    """Client for Sentry summary, object, VI, and removed-object modes."""

    def __init__(self, timeout: int = 30) -> None:
        super().__init__(base_url=SENTRY_ENDPOINT, timeout=timeout)

    def get_summary(self) -> dict[str, Any]:
        return self.get()

    def get_object_by_designation(self, des: str) -> dict[str, Any]:
        return self.get({"des": des})

    def get_object_by_spk(self, spk: int) -> dict[str, Any]:
        return self.get({"spk": spk})

    def get_virtual_impactors(self, ip_min: float | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"all": 1}
        if ip_min is not None:
            params["ip-min"] = ip_min
        return self.get(params)

    def get_removed_objects(self) -> dict[str, Any]:
        return self.get({"removed": 1})

    def get_high_priority_summary(
        self,
        ip_min: float | None = None,
        ps_min: int | None = None,
        h_max: float | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if ip_min is not None:
            params["ip-min"] = ip_min
        if ps_min is not None:
            params["ps-min"] = ps_min
        if h_max is not None:
            params["h-max"] = h_max
        return self.get(params)
