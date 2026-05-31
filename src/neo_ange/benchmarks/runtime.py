"""Runtime and artifact-size benchmark helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_runtime_report(root: str | Path = ".") -> dict[str, Any]:
    """Return lightweight artifact sizes and command inventory."""
    root = Path(root)
    files = []
    for pattern in [
        "data/**/*.parquet",
        "reports/**/*.json",
        "reports/**/*.csv",
        "reports/**/*.md",
    ]:
        for path in root.glob(pattern):
            if path.is_file():
                files.append({"path": str(path), "bytes": int(path.stat().st_size)})
    return {
        "status": "success",
        "artifact_count": len(files),
        "total_artifact_bytes": sum(item["bytes"] for item in files),
        "largest_artifacts": sorted(files, key=lambda item: item["bytes"], reverse=True)[:20],
        "commands_measured": [
            "expand max",
            "etl run-all",
            "risk build",
            "simulate batch",
            "orbital-sim batch",
            "ml run-all",
            "gnn build-graph",
            "gnn run",
            "findings build",
        ],
        "note": (
            "This benchmark records current artifact sizes; detailed wall-clock timings "
            "are captured when run inside final build-all."
        ),
    }
