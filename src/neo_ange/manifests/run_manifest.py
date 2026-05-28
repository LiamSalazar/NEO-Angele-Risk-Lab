"""JSON run manifests for ingestion, ETL, and machine-learning workflows."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from neo_ange.utils.serialization import to_jsonable, write_json

RunType = Literal["ingestion", "etl", "ml"]
RunStatus = Literal["success", "partial_success", "failed", "skipped", "insufficient_data"]


def create_run_id(run_type: str) -> str:
    """Create a compact UTC run id such as ``ingestion_20260528T070000123456Z``."""
    safe_type = _safe_token(run_type)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{safe_type}_{timestamp}"


@dataclass(slots=True)
class RunManifest:
    """Serializable metadata envelope for one operational run."""

    run_id: str
    run_type: str
    started_at_utc: str
    ended_at_utc: str
    status: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable manifest dictionary."""
        return to_jsonable(asdict(self))


def save_manifest(
    manifest: RunManifest,
    output_dir: Path | str = "reports/manifests",
) -> Path:
    """Persist a run manifest as JSON under the manifest report directory."""
    manifest_dir = Path(output_dir)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{_safe_token(manifest.run_type)}_{_timestamp_from_run_id(manifest.run_id)}.json"
    return write_json(manifest.to_dict(), manifest_dir / filename)


def load_latest_manifest(
    run_type: str,
    output_dir: Path | str = "reports/manifests",
) -> dict[str, Any] | None:
    """Load the newest manifest for a run type, or ``None`` when none exist."""
    manifests = list_manifests(run_type=run_type, output_dir=output_dir)
    if not manifests:
        return None
    latest = manifests[-1]
    return json.loads(latest.read_text(encoding="utf-8"))


def list_manifests(
    run_type: str | None = None,
    output_dir: Path | str = "reports/manifests",
) -> list[Path]:
    """List manifest paths sorted from oldest to newest."""
    manifest_dir = Path(output_dir)
    if not manifest_dir.exists():
        return []
    pattern = "*.json" if run_type is None else f"{_safe_token(run_type)}_*.json"
    return sorted(path for path in manifest_dir.glob(pattern) if path.is_file())


def utc_now_manifest() -> str:
    """Return a UTC timestamp for manifest fields."""
    return datetime.now(UTC).isoformat()


def _timestamp_from_run_id(run_id: str) -> str:
    if "_" not in run_id:
        return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return run_id.rsplit("_", 1)[-1]


def _safe_token(value: str) -> str:
    token = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
    return token.strip("_").lower() or "run"
