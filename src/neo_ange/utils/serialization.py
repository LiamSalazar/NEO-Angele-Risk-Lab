"""Serialization helpers for JSON, CSV, and manifest-friendly payloads."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def to_jsonable(value: Any) -> Any:
    """Convert common scientific Python objects into JSON-serializable values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [to_jsonable(item) for item in value]
    return str(value)


def write_json(data: Mapping[str, Any], path: Path | str) -> Path:
    """Write a stable, UTF-8 JSON file and return the path."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(to_jsonable(dict(data)), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path
