"""Dataset coverage and readiness reporting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.services.bronze_storage import BronzeStorage
from neo_ange.utils.serialization import to_jsonable, write_json

READINESS_THRESHOLDS = {
    "not_ready": 0,
    "minimal": 100,
    "usable": 300,
    "strong": 1000,
}


class DatasetReadinessReporter:
    """Summarize processed data coverage for ML, ranking, simulation, GNN, and API use."""

    def __init__(
        self,
        data_dir: str | Path = "data",
        silver_root: str | Path = "data/silver",
        gold_root: str | Path = "data/gold",
        report_dir: str | Path = "reports/data_quality",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.silver_root = Path(silver_root)
        self.gold_root = Path(gold_root)
        self.report_dir = Path(report_dir)
        self.bronze_root = self.data_dir / "bronze"

    def build_report(self, write: bool = True) -> dict[str, Any]:
        """Build and optionally persist dataset readiness reports."""
        bronze_object_count = len(BronzeStorage(self.bronze_root).list_object_ids("sbdb_object"))
        silver_objects = _read_parquet(self.silver_root / "sbdb_objects")
        silver_cad = _read_parquet(self.silver_root / "close_approaches")
        silver_sentry = _read_parquet(self.silver_root / "sentry_objects")
        gold = _read_parquet(self.gold_root / "neo_risk_features")
        risk_scores = _read_parquet(self.gold_root / "risk_scores" / "risk_scores.parquet")
        if risk_scores.empty:
            risk_scores = _read_parquet(self.gold_root / "risk_scores")

        feature_df = gold if not gold.empty else risk_scores
        pha_distribution = _bool_distribution(feature_df, "pha")
        neo_count = _bool_distribution(feature_df, "neo")["true"]
        sentry_coverage = _coverage(feature_df, ["sentry_flag", "sentry_ip"])
        cad_coverage = _coverage(
            feature_df,
            [
                "min_close_approach_dist",
                "min_close_approach_dist_min",
                "max_close_approach_v_rel",
                "close_approach_count",
            ],
        )
        missingness = _missingness_summary(feature_df)
        gold_count = int(len(gold))
        risk_count = int(len(risk_scores))
        readiness = {
            "overall": readiness_status(gold_count),
            "ml_baseline": _ml_readiness(gold_count, pha_distribution),
            "leakage_audit": _ml_readiness(gold_count, pha_distribution),
            "risk_ranking": readiness_status(risk_count or gold_count),
            "monte_carlo": readiness_status(risk_count) if risk_count else "not_ready",
            "gnn": _gnn_readiness(risk_count or gold_count, pha_distribution, feature_df),
            "frontend": readiness_status(risk_count or gold_count),
        }

        report = {
            "status": readiness["overall"],
            "counts": {
                "bronze_sbdb_object_count": int(bronze_object_count),
                "silver_sbdb_objects_count": int(len(silver_objects)),
                "silver_close_approaches_count": int(len(silver_cad)),
                "silver_sentry_objects_count": int(len(silver_sentry)),
                "gold_neo_risk_features_count": gold_count,
                "risk_scores_count": risk_count,
            },
            "pha_distribution": pha_distribution,
            "neo_count": int(neo_count),
            "sentry_coverage": sentry_coverage,
            "cad_coverage": cad_coverage,
            "missingness_summary": missingness,
            "readiness": readiness,
            "recommended_next_command": _recommended_next_command(gold_count, risk_count),
            "outputs": {
                "json": str(self.report_dir / "dataset_readiness.json"),
                "markdown": str(self.report_dir / "dataset_readiness.md"),
            },
        }
        if write:
            self.write_report(report)
        return to_jsonable(report)

    def write_report(self, report: dict[str, Any]) -> dict[str, str]:
        """Persist JSON and markdown readiness reports."""
        json_path = write_json(report, self.report_dir / "dataset_readiness.json")
        markdown_path = self.report_dir / "dataset_readiness.md"
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(_render_markdown(report), encoding="utf-8")
        return {"json": str(json_path), "markdown": str(markdown_path)}


def readiness_status(object_count: int) -> str:
    """Return readiness status from object-count thresholds."""
    if object_count >= READINESS_THRESHOLDS["strong"]:
        return "strong"
    if object_count >= READINESS_THRESHOLDS["usable"]:
        return "usable"
    if object_count >= READINESS_THRESHOLDS["minimal"]:
        return "minimal"
    return "not_ready"


def _read_parquet(path: Path) -> pd.DataFrame:
    if path.is_file():
        return pd.read_parquet(path)
    if path.is_dir() and any(path.glob("*.parquet")):
        return pd.read_parquet(path)
    return pd.DataFrame()


def _bool_distribution(df: pd.DataFrame, column: str) -> dict[str, int]:
    if df.empty or column not in df.columns:
        return {"true": 0, "false": 0, "unknown": int(len(df))}
    series = df[column]
    if pd.api.types.is_bool_dtype(series):
        true_mask = series.fillna(False)
        known_mask = series.notna()
    else:
        normalized = series.astype("string").str.lower()
        true_mask = normalized.isin(["true", "t", "1", "yes", "y"])
        false_mask = normalized.isin(["false", "f", "0", "no", "n"])
        known_mask = true_mask | false_mask
    true_count = int(true_mask.sum())
    false_count = int((known_mask & ~true_mask).sum())
    unknown_count = int(len(series) - true_count - false_count)
    return {"true": true_count, "false": false_count, "unknown": unknown_count}


def _coverage(df: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    if df.empty:
        return {"covered_rows": 0, "total_rows": 0, "coverage_ratio": 0.0}
    available = [column for column in columns if column in df.columns]
    if not available:
        return {"covered_rows": 0, "total_rows": int(len(df)), "coverage_ratio": 0.0}
    mask = df[available].notna().any(axis=1)
    covered = int(mask.sum())
    return {
        "covered_rows": covered,
        "total_rows": int(len(df)),
        "coverage_ratio": float(covered / len(df)) if len(df) else 0.0,
        "columns": available,
    }


def _missingness_summary(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"columns": {}, "top_missing": []}
    columns = {}
    for column in df.columns:
        missing = int(df[column].isna().sum())
        columns[column] = {
            "missing_count": missing,
            "missing_ratio": float(missing / len(df)) if len(df) else 0.0,
        }
    top_missing = sorted(
        (
            {"column": column, **stats}
            for column, stats in columns.items()
            if stats["missing_count"] > 0
        ),
        key=lambda item: item["missing_ratio"],
        reverse=True,
    )[:20]
    return {"columns": columns, "top_missing": top_missing}


def _ml_readiness(gold_count: int, pha_distribution: dict[str, int]) -> str:
    if gold_count < 100:
        return "not_ready"
    if pha_distribution["true"] == 0 or pha_distribution["false"] == 0:
        return "minimal"
    return readiness_status(gold_count)


def _gnn_readiness(
    object_count: int,
    pha_distribution: dict[str, int],
    df: pd.DataFrame,
) -> str:
    if object_count < 100:
        return "not_ready"
    orbital_columns = ["e", "a", "q", "i", "moid"]
    present = [column for column in orbital_columns if column in df.columns]
    if len(present) < 3:
        return "minimal"
    if pha_distribution["true"] == 0 or pha_distribution["false"] == 0:
        return "minimal"
    return readiness_status(object_count)


def _recommended_next_command(gold_count: int, risk_count: int) -> str:
    if gold_count == 0:
        return "python -m neo_ange.cli expand max --target 1000 --skip-existing --resume"
    if risk_count == 0:
        return "python -m neo_ange.cli risk build"
    if gold_count < 300:
        return "python -m neo_ange.cli expand max --target 1000 --skip-existing --resume"
    return "python -m neo_ange.cli gnn status"


def _render_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    readiness = report["readiness"]
    lines = [
        "# Dataset readiness",
        "",
        f"Overall status: **{report['status']}**",
        "",
        "## Counts",
        "",
        f"- Bronze SBDB Object: {counts['bronze_sbdb_object_count']}",
        f"- Silver SBDB Objects: {counts['silver_sbdb_objects_count']}",
        f"- Silver CAD rows: {counts['silver_close_approaches_count']}",
        f"- Silver Sentry rows: {counts['silver_sentry_objects_count']}",
        f"- Gold NEO risk features: {counts['gold_neo_risk_features_count']}",
        f"- Risk scores: {counts['risk_scores_count']}",
        "",
        "## Target and coverage",
        "",
        f"- PHA distribution: {report['pha_distribution']}",
        f"- NEO count: {report['neo_count']}",
        f"- Sentry coverage: {report['sentry_coverage']}",
        f"- CAD coverage: {report['cad_coverage']}",
        "",
        "## Readiness",
        "",
    ]
    lines.extend(f"- {name}: {status}" for name, status in readiness.items())
    lines.extend(
        [
            "",
            "## Missingness",
            "",
        ]
    )
    top_missing = report["missingness_summary"].get("top_missing", [])
    if top_missing:
        lines.extend(
            f"- {item['column']}: {item['missing_count']} " f"({item['missing_ratio']:.3f})"
            for item in top_missing[:10]
        )
    else:
        lines.append("- No missingness summary available.")
    lines.extend(["", f"Recommended next command: `{report['recommended_next_command']}`", ""])
    return "\n".join(lines)
