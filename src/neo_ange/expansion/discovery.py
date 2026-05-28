"""Discover SBDB object designations from existing local CAD and Sentry data."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.utils.paths import contains_files

logger = logging.getLogger(__name__)

CURATED_SEED_OBJECTS = [
    "99942",
    "433",
    "101955",
    "162173",
    "3200",
    "1862",
    "4179",
    "3122",
    "1685",
    "2101",
]


class ObjectDiscoveryService:
    """Find candidate object designations without making network calls."""

    def __init__(
        self,
        silver_root: str | Path = "data/silver",
        bronze_root: str | Path = "data/bronze",
    ) -> None:
        self.silver_root = Path(silver_root)
        self.bronze_root = Path(bronze_root)
        self.warnings: list[str] = []

    def discover_from_silver_cad(self, limit: int | None = None) -> list[str]:
        """Discover designations from ``silver/close_approaches``."""
        df = self._read_parquet_table(self.silver_root / "close_approaches", "silver CAD")
        return self._limit(self._extract_from_frame(df, ["des", "fullname"]), limit)

    def discover_from_silver_sentry(self, limit: int | None = None) -> list[str]:
        """Discover designations from silver Sentry object and virtual-impactor tables."""
        designations: list[str] = []
        for table in ("sentry_objects", "sentry_virtual_impactors"):
            df = self._read_parquet_table(self.silver_root / table, f"silver {table}")
            designations.extend(self._extract_from_frame(df, ["des", "spk", "fullname"]))
        return self._limit(_stable_unique(designations), limit)

    def discover_from_bronze_cad(self, limit: int | None = None) -> list[str]:
        """Discover designations from local bronze CAD JSON wrappers."""
        designations: list[str] = []
        for wrapper in self._read_bronze_wrappers("cad"):
            payload = wrapper.get("data", {})
            fields = payload.get("fields")
            rows = payload.get("data")
            if isinstance(fields, list) and isinstance(rows, list):
                designations.extend(_extract_table_field(fields, rows, "des"))
                designations.extend(_extract_table_field(fields, rows, "fullname"))
        return self._limit(_stable_unique(designations), limit)

    def discover_from_bronze_sentry(self, limit: int | None = None) -> list[str]:
        """Discover designations from local bronze Sentry JSON wrappers."""
        designations: list[str] = []
        for wrapper in self._read_bronze_wrappers("sentry"):
            payload = wrapper.get("data", {})
            data = payload.get("data")
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        designations.extend(
                            [
                                _clean_designation(item.get("des")),
                                _clean_designation(item.get("spk")),
                                _clean_designation(item.get("spkid")),
                                _clean_designation(item.get("fullname")),
                            ]
                        )
        return self._limit(_stable_unique(designations), limit)

    def curated_seed_objects(self, limit: int | None = None) -> list[str]:
        """Return a deterministic fallback seed list for demos and tests."""
        return self._limit(list(CURATED_SEED_OBJECTS), limit)

    def discover_all(self, limit: int = 200) -> list[str]:
        """Discover unique designations from local sources, then curated fallback seeds."""
        candidates: list[str] = []
        for discover in (
            self.discover_from_silver_cad,
            self.discover_from_silver_sentry,
            self.discover_from_bronze_cad,
            self.discover_from_bronze_sentry,
            self.curated_seed_objects,
        ):
            candidates.extend(discover(limit=None))
            candidates = _stable_unique(candidates)
            if len(candidates) >= limit:
                break
        return candidates[:limit]

    def _read_parquet_table(self, path: Path, label: str) -> pd.DataFrame:
        if not contains_files(path, "*.parquet"):
            self._warn(f"{label} is not available at {path}.")
            return pd.DataFrame()
        try:
            return pd.read_parquet(path)
        except Exception as exc:
            self._warn(f"Could not read {label} at {path}: {exc}")
            return pd.DataFrame()

    def _read_bronze_wrappers(self, source: str) -> list[dict[str, Any]]:
        source_dir = self.bronze_root / source
        if not source_dir.exists():
            self._warn(f"Bronze source '{source}' is not available at {source_dir}.")
            return []
        wrappers: list[dict[str, Any]] = []
        for path in sorted(source_dir.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                self._warn(f"Could not read bronze file {path}: {exc}")
                continue
            if isinstance(data, dict):
                wrappers.append(data)
        return wrappers

    def _extract_from_frame(self, df: pd.DataFrame, columns: list[str]) -> list[str]:
        if df.empty:
            return []
        values: list[str] = []
        for column in columns:
            if column in df.columns:
                values.extend(_clean_designation(value) for value in df[column].tolist())
        return _stable_unique(values)

    def _warn(self, message: str) -> None:
        self.warnings.append(message)
        logger.warning(message)

    @staticmethod
    def _limit(values: list[str], limit: int | None) -> list[str]:
        if limit is None:
            return values
        return values[: max(limit, 0)]


def _extract_table_field(fields: list[Any], rows: list[Any], field_name: str) -> list[str]:
    normalized = [str(field).strip().lower() for field in fields]
    if field_name not in normalized:
        return []
    index = normalized.index(field_name)
    values: list[str] = []
    for row in rows:
        if isinstance(row, list) and index < len(row):
            values.append(_clean_designation(row[index]))
    return values


def _clean_designation(value: Any) -> str:
    if value is None:
        return ""
    cleaned = str(value).strip()
    if not cleaned:
        return ""
    if cleaned.lower() in {"nan", "none", "null"}:
        return ""
    return " ".join(cleaned.split())


def _stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        cleaned = _clean_designation(value)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)
    return unique
