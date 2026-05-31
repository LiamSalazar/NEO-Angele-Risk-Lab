"""Model benchmark normalization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def build_model_benchmark(reports_root: str | Path = "reports") -> dict[str, Any]:
    """Return available ML/GNN metric rows."""
    reports_root = Path(reports_root)
    ml = _read_csv(reports_root / "ml" / "baseline_metrics.csv")
    gnn = _read_csv(reports_root / "gnn" / "gnn_metrics.csv")
    return {
        "status": "success",
        "ml_metric_rows": int(len(ml)),
        "gnn_metric_rows": int(len(gnn)),
        "ml_metrics": ml.to_dict("records") if not ml.empty else [],
        "gnn_metrics": gnn.to_dict("records") if not gnn.empty else [],
    }


def _read_csv(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size > 2:
        return pd.read_csv(path)
    return pd.DataFrame()
