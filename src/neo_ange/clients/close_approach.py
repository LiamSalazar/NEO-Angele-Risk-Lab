"""Client for the NASA/JPL Close Approach Data API."""

from __future__ import annotations

from typing import Any

from neo_ange.clients.base import BaseJPLClient

CAD_ENDPOINT = "https://ssd-api.jpl.nasa.gov/cad.api"


class CloseApproachClient(BaseJPLClient):
    """Client for close approach records from NASA/JPL CAD."""

    def __init__(self, timeout: int = 30) -> None:
        super().__init__(base_url=CAD_ENDPOINT, timeout=timeout)

    def query(
        self,
        date_min: str = "now",
        date_max: str = "+60",
        dist_max: str = "0.05",
        body: str = "Earth",
        neo: bool = True,
        pha: bool | None = None,
        limit: int | None = 100,
        sort: str = "date",
        diameter: bool = True,
        fullname: bool = True,
        des: str | None = None,
        spk: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "date-min": date_min,
            "date-max": date_max,
            "dist-max": dist_max,
            "body": body,
            "sort": sort,
            "diameter": self._bool_param(diameter),
            "fullname": self._bool_param(fullname),
        }
        if neo:
            params["neo"] = self._bool_param(True)
        if pha is not None:
            params["pha"] = self._bool_param(pha)
        if limit is not None:
            params["limit"] = limit
        if des is not None:
            params["des"] = des
        if spk is not None:
            params["spk"] = spk
        return self.get(params)

    def query_by_designation(
        self,
        des: str,
        date_min: str = "1900-01-01",
        date_max: str = "2100-01-01",
        dist_max: str = "0.2",
    ) -> dict[str, Any]:
        return self.query(
            date_min=date_min,
            date_max=date_max,
            dist_max=dist_max,
            neo=False,
            limit=None,
            des=des,
        )

    def query_upcoming_earth_approaches(self, limit: int = 100) -> dict[str, Any]:
        return self.query(date_min="now", date_max="+60", dist_max="0.05", limit=limit)

    def query_pha_approaches(self, limit: int = 100) -> dict[str, Any]:
        return self.query(
            date_min="now",
            date_max="+365",
            dist_max="0.2",
            pha=True,
            limit=limit,
        )

    @staticmethod
    def _bool_param(value: bool) -> str:
        return "true" if value else "false"
