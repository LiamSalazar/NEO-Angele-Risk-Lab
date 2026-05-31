"""Dataset-scale benchmark helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def build_dataset_scale_report(
    gold_root: str | Path = "data/gold",
    reports_root: str | Path = "reports",
) -> dict[str, Any]:
    """Compare current dataset artifacts against the 4000-object target honestly."""
    gold_root = Path(gold_root)
    reports_root = Path(reports_root)
    gold = _read_parquet(gold_root / "neo_risk_features")
    risk = _read_parquet(gold_root / "risk_scores" / "risk_scores.parquet")
    nodes = _read_parquet(gold_root / "gnn_graph" / "nodes.parquet")
    edges = _read_parquet(gold_root / "gnn_graph" / "edges.parquet")
    ml_metrics = _read_csv(reports_root / "ml" / "baseline_metrics.csv")
    gnn_metrics = _read_csv(reports_root / "gnn" / "gnn_metrics.csv")
    current_rows = int(len(gold) or len(risk))
    target_rows = 4000
    return {
        "status": "success",
        "target_objects": target_rows,
        "current_dataset": {
            "gold_rows": int(len(gold)),
            "risk_rows": int(len(risk)),
            "missingness": _missingness(gold if not gold.empty else risk),
            "pha_distribution": _bool_distribution(gold if not gold.empty else risk, "pha"),
            "risk_distribution": _value_counts(risk, "risk_category"),
            "gnn_graph_density": _density(len(nodes), len(edges)),
            "gnn_nodes": int(len(nodes)),
            "gnn_edges": int(len(edges)),
            "ml_metrics_rows": int(len(ml_metrics)),
            "gnn_metrics_rows": int(len(gnn_metrics)),
        },
        "baseline_1000": {
            "available": current_rows >= 1000,
            "row_count": current_rows,
            "note": (
                "Current local artifacts are used as the 1000-object baseline when "
                "row count is near 1000."
            ),
        },
        "target_4000": {
            "available": current_rows >= target_rows,
            "row_count": current_rows if current_rows >= target_rows else None,
            "note": "4000-object benchmark becomes concrete after expansion and rebuild complete.",
        },
        "recommendation": _recommendation(current_rows),
    }


def _read_parquet(path: Path) -> pd.DataFrame:
    if path.is_file():
        return pd.read_parquet(path)
    if path.is_dir() and any(path.glob("*.parquet")):
        return pd.read_parquet(path)
    return pd.DataFrame()


def _read_csv(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size > 2:
        return pd.read_csv(path)
    return pd.DataFrame()


def _missingness(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"top_missing": []}
    rows = []
    for column in df.columns:
        ratio = float(df[column].isna().mean())
        if ratio > 0:
            rows.append(
                {
                    "column": column,
                    "missing_ratio": ratio,
                    "missing_count": int(df[column].isna().sum()),
                }
            )
    return {"top_missing": sorted(rows, key=lambda item: item["missing_ratio"], reverse=True)[:20]}


def _bool_distribution(df: pd.DataFrame, column: str) -> dict[str, int]:
    if df.empty or column not in df.columns:
        return {"true": 0, "false": 0, "unknown": int(len(df))}
    normalized = df[column].astype("string").str.lower()
    true_mask = normalized.isin(["true", "1", "yes", "y", "t"])
    false_mask = normalized.isin(["false", "0", "no", "n", "f"])
    return {
        "true": int(true_mask.sum()),
        "false": int(false_mask.sum()),
        "unknown": int((~true_mask & ~false_mask).sum()),
    }


def _value_counts(df: pd.DataFrame, column: str) -> dict[str, int]:
    if df.empty or column not in df.columns:
        return {}
    return {str(key): int(value) for key, value in df[column].value_counts().items()}


def _density(nodes: int, edges: int) -> float:
    if nodes <= 1:
        return 0.0
    return float((2 * edges) / (nodes * (nodes - 1)))


def _recommendation(current_rows: int) -> str:
    if current_rows >= 4000:
        return "Use the 4000-object dataset as the official presentation dataset."
    if current_rows >= 1000:
        return (
            "The 1000-object dataset is usable for the observatory; expanding to 4000 should "
            "increase coverage before final presentation if API time allows."
        )
    return "Expand and rebuild before relying on aggregate conclusions."
