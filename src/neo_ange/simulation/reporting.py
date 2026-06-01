"""Report writers for Risk Score uncertainty propagation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.simulation.schemas import MONTE_CARLO_VERSION
from neo_ange.simulation.sensitivity import SensitivityAnalyzer
from neo_ange.utils.serialization import write_json


class SimulationReportWriter:
    """Persist score uncertainty summaries, sensitivity reports, and legacy aliases."""

    def __init__(
        self,
        result_output_dir: str | Path = "data/gold/simulation_results",
        report_dir: str | Path = "reports/simulation",
    ) -> None:
        self.result_output_dir = Path(result_output_dir)
        self.report_dir = Path(report_dir)

    @property
    def results_path(self) -> Path:
        return self.result_output_dir / "monte_carlo_results.parquet"

    @property
    def uncertainty_results_path(self) -> Path:
        return self.result_output_dir / "score_uncertainty_results.parquet"

    def save_outputs(
        self,
        results: list[dict[str, Any]],
        source_rows: pd.DataFrame | None = None,
    ) -> dict[str, str]:
        """Write uncertainty, sensitivity, methodology, and compatibility outputs."""
        self.result_output_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        new_df = pd.DataFrame([_table_safe(result) for result in results])
        if self.results_path.exists():
            existing = pd.read_parquet(self.results_path)
            combined = pd.concat([existing, new_df], ignore_index=True)
        else:
            combined = new_df
        combined.to_parquet(self.results_path, index=False)
        combined.to_parquet(self.uncertainty_results_path, index=False)
        uncertainty_csv_path = self.result_output_dir / "score_uncertainty_results.csv"
        combined.to_csv(uncertainty_csv_path, index=False)

        summary = summarize_uncertainty_results(combined)
        summary["latest_results"] = results
        summary_path = write_json(summary, self.report_dir / "score_uncertainty_summary.json")
        legacy_summary_path = write_json(summary, self.report_dir / "monte_carlo_summary.json")
        summary_md_path = self.report_dir / "score_uncertainty_summary.md"
        summary_md_path.write_text(render_uncertainty_summary(summary), encoding="utf-8")
        csv_path = self.report_dir / "monte_carlo_summary.csv"
        combined.to_csv(csv_path, index=False)
        sensitivity_outputs = self.write_sensitivity_reports(source_rows)
        methodology_path = self.write_methodology()
        return {
            "monte_carlo_results_parquet": str(self.results_path),
            "monte_carlo_summary_json": str(legacy_summary_path),
            "monte_carlo_summary_csv": str(csv_path),
            "monte_carlo_methodology_md": str(methodology_path),
            "score_uncertainty_results_parquet": str(self.uncertainty_results_path),
            "score_uncertainty_results_csv": str(uncertainty_csv_path),
            "score_uncertainty_summary_json": str(summary_path),
            "score_uncertainty_summary_markdown": str(summary_md_path),
            **sensitivity_outputs,
        }

    def write_methodology(self) -> Path:
        """Write a compact technical methodology note."""
        path = self.report_dir / "score_simulation_methodology.md"
        lines = [
            "# Score Simulation Methodology",
            "",
            "## Purpose",
            "",
            "The workflow estimates stability of the experimental Risk Priority Score with two "
            "separate modes: `uncertainty_propagation` and `sensitivity_analysis`. It is not an "
            "official impact-probability model and it is not an orbital propagation.",
            "",
            "## Uncertainty propagation",
            "",
            "The score is treated as `R = f(X)`, where `X` contains base variables such as H, "
            "diameter, MOID, close-approach distance, velocity, Sentry fields, condition code, "
            "RMS, observation arc, and observation count. Derived variables such as inverse "
            "MOID, log diameter, velocity scores, and risk components are never sampled "
            "directly; they are recalculated from each sampled base row.",
            "",
            "Each sampled variable records a distribution type, source, justification, and "
            "mode. When source uncertainty is absent, the output is marked as "
            "`empirical_uncertainty` or `heuristic_fallback` rather than calibrated formal "
            "uncertainty.",
            "",
            "## Sensitivity analysis",
            "",
            "The deterministic sensitivity report varies important base variables by bounded "
            "relative ranges and recalculates the score after refreshing derived variables.",
            "",
            "## Interpretation",
            "",
            "- `p95_score` is the 95th percentile of propagated score outcomes.",
            "- `std_score` describes score spread under approximate perturbations.",
            "- `category_shift_probability` is the share of simulations whose score category "
            "differs from the base category.",
            "- `fallback_used` means at least one variable lacked reported or empirical "
            "uncertainty and used an explicitly marked fallback.",
            "",
            "## Limitations",
            "",
            "- This simulation perturbs tabular score inputs, not orbital states.",
            "- It should be read as score stability analysis, not impact-probability prediction.",
            "- Sparse source data can make empirical uncertainty estimates unavailable.",
            "",
            f"Simulation version: `{MONTE_CARLO_VERSION}`",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        legacy_path = self.report_dir / "monte_carlo_methodology.md"
        legacy_path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def write_sensitivity_reports(self, source_rows: pd.DataFrame | None) -> dict[str, str]:
        """Write deterministic score sensitivity reports from source rows."""
        rows: list[dict[str, Any]] = []
        if source_rows is not None and not source_rows.empty:
            analyzer = SensitivityAnalyzer()
            for _, source_row in source_rows.iterrows():
                object_key = _object_key(source_row)
                for item in analyzer.estimate_feature_sensitivity(source_row):
                    rows.append({"object_key": object_key, **item})
        df = pd.DataFrame(rows)
        sensitivity_path = self.report_dir / "score_sensitivity_by_variable.csv"
        df.to_csv(sensitivity_path, index=False)
        summary = summarize_sensitivity(df)
        summary_json = write_json(summary, self.report_dir / "score_sensitivity_summary.json")
        summary_md = self.report_dir / "score_sensitivity_summary.md"
        summary_md.write_text(render_sensitivity_summary(summary), encoding="utf-8")
        return {
            "score_sensitivity_by_variable_csv": str(sensitivity_path),
            "score_sensitivity_summary_json": str(summary_json),
            "score_sensitivity_summary_markdown": str(summary_md),
        }


def summarize_uncertainty_results(df: pd.DataFrame) -> dict[str, Any]:
    """Summarize score uncertainty result rows."""
    if df.empty:
        return {
            "status": "missing_data",
            "n_result_rows": 0,
            "simulation_version": MONTE_CARLO_VERSION,
        }
    fallback_col = df.get("fallback_used")
    formal_col = df.get("is_formal_uncertainty")
    return {
        "status": "success",
        "n_result_rows": int(len(df)),
        "simulation_version": MONTE_CARLO_VERSION,
        "mean_base_score": _series_stat(df, "base_score", "mean"),
        "mean_std_score": _series_stat(df, "std_score", "mean"),
        "max_category_shift_probability": _series_stat(
            df,
            "category_shift_probability",
            "max",
        ),
        "fallback_used_count": _bool_true_count(fallback_col),
        "formal_uncertainty_count": _bool_true_count(formal_col),
        "simulation_method_counts": (
            {str(k): int(v) for k, v in df["simulation_method"].value_counts(dropna=False).items()}
            if "simulation_method" in df.columns
            else {}
        ),
    }


def summarize_sensitivity(df: pd.DataFrame) -> dict[str, Any]:
    """Summarize deterministic sensitivity rows."""
    if df.empty:
        return {"status": "missing_data", "row_count": 0}
    top_variables = (
        df.groupby("variable")["absolute_effect"].mean().sort_values(ascending=False).head(10)
    )
    object_effect = (
        df.groupby("object_key")["absolute_effect"].max().sort_values(ascending=False).head(20)
    )
    return {
        "status": "success",
        "row_count": int(len(df)),
        "top_variables_by_mean_absolute_effect": {
            str(key): _float_or_none(value) for key, value in top_variables.items()
        },
        "most_sensitive_objects": {
            str(key): _float_or_none(value) for key, value in object_effect.items()
        },
        "analysis_mode": "deterministic_sensitivity",
    }


def render_uncertainty_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Score Uncertainty Summary",
        "",
        "Risk Score uncertainty propagation results. Formal uncertainty is only claimed when "
        "all sampled variables have reported uncertainty.",
        "",
    ]
    for key, value in summary.items():
        if key == "latest_results":
            continue
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def render_sensitivity_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Score Sensitivity Summary",
        "",
        "Deterministic sensitivity analysis over base score variables.",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def _object_key(row: pd.Series) -> str:
    for column in ("object_key", "spkid", "des", "full_name", "name"):
        value = row.get(column)
        if value is not None and not pd.isna(value):
            return str(value)
    return "unknown-object"


def _float_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return result


def _series_stat(df: pd.DataFrame, column: str, stat: str) -> float | None:
    if column not in df.columns:
        return None
    series = pd.to_numeric(df[column], errors="coerce")
    if stat == "mean":
        return _float_or_none(series.mean())
    if stat == "max":
        return _float_or_none(series.max())
    return None


def _table_safe(result: dict[str, Any]) -> dict[str, Any]:
    row = dict(result)
    for column in ("uncertainty_sources", "most_influential_variables", "source_counts"):
        if column in row and not isinstance(row[column], (str, int, float, bool, type(None))):
            row[column] = json.dumps(row[column], sort_keys=True)
    return row


def _bool_true_count(series: pd.Series | None) -> int:
    if series is None:
        return 0
    return int(series.map(lambda value: bool(value) if pd.notna(value) else False).sum())
