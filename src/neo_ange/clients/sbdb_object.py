"""Client for the NASA/JPL SBDB Object API."""

from __future__ import annotations

from typing import Any

from neo_ange.clients.base import BaseJPLClient

SBDB_OBJECT_ENDPOINT = "https://ssd-api.jpl.nasa.gov/sbdb.api"
VALID_COVARIANCE_FORMATS = {"mat", "vec", "src"}


class SBDBObjectClient(BaseJPLClient):
    """Client for object-level asteroid and comet data."""

    def __init__(self, timeout: int = 30) -> None:
        super().__init__(base_url=SBDB_OBJECT_ENDPOINT, timeout=timeout)

    def get_by_search_string(self, sstr: str, neo_only: bool = True) -> dict[str, Any]:
        params: dict[str, Any] = {"sstr": sstr}
        if neo_only:
            params["neo"] = 1
        return self.get(params)

    def get_by_designation(self, des: str, neo_only: bool = False) -> dict[str, Any]:
        params: dict[str, Any] = {"des": des}
        if neo_only:
            params["neo"] = 1
        return self.get(params)

    def get_by_spk(self, spk: int, neo_only: bool = False) -> dict[str, Any]:
        params: dict[str, Any] = {"spk": spk}
        if neo_only:
            params["neo"] = 1
        return self.get(params)

    def get_rich_object(self, designation_or_name: str) -> dict[str, Any]:
        params = {
            "sstr": designation_or_name,
            "phys-par": 1,
            "ca-data": 1,
            "vi-data": 1,
            "full-prec": 1,
            "ca-time": "both",
            "ca-tunc": "both",
            "ca-unc": 1,
            "orbit-defs": 1,
            "anc-data": 1,
        }
        return self.get(params)

    def get_with_covariance(
        self,
        designation_or_name: str,
        covariance_format: str = "mat",
    ) -> dict[str, Any]:
        if covariance_format not in VALID_COVARIANCE_FORMATS:
            allowed = ", ".join(sorted(VALID_COVARIANCE_FORMATS))
            raise ValueError(f"covariance_format must be one of: {allowed}")
        return self.get(
            {
                "sstr": designation_or_name,
                "cov": covariance_format,
                "full-prec": 1,
            }
        )
