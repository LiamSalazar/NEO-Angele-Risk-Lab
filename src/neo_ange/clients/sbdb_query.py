"""Client for the NASA/JPL SBDB Query API."""

from __future__ import annotations

from typing import Any

from neo_ange.clients.base import BaseJPLClient

SBDB_QUERY_ENDPOINT = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"

DEFAULT_NEO_FIELDS = [
    "spkid",
    "full_name",
    "pdes",
    "class",
    "neo",
    "pha",
    "H",
    "diameter",
    "albedo",
    "epoch",
    "e",
    "a",
    "q",
    "i",
    "om",
    "w",
    "ma",
    "n",
    "per",
    "moid",
]


class SBDBQueryClient(BaseJPLClient):
    """Client for querying sets of asteroids and comets from SBDB."""

    def __init__(self, timeout: int = 30) -> None:
        super().__init__(base_url=SBDB_QUERY_ENDPOINT, timeout=timeout)

    def get_count(self) -> dict[str, Any]:
        return self.get({"info": "count"})

    def get_fields(self) -> dict[str, Any]:
        return self.get({"info": "field"})

    def query_neos(self, limit: int = 100, limit_from: int = 0) -> dict[str, Any]:
        params = {
            "fields": ",".join(self._dedupe_fields(DEFAULT_NEO_FIELDS)),
            "sb-group": "neo",
            "limit": limit,
            "limit-from": limit_from,
            "full-prec": 1,
        }
        return self.get(params)

    def query_custom(
        self,
        fields: list[str],
        limit: int = 100,
        limit_from: int = 0,
        sort: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "fields": ",".join(self._dedupe_fields(fields)),
            "limit": limit,
            "limit-from": limit_from,
        }
        if sort:
            params["sort"] = sort
        if extra_params:
            params.update(extra_params)
        return self.get(params)

    @staticmethod
    def _dedupe_fields(fields: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for field in fields:
            normalized = field.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                deduped.append(normalized)
        return deduped
