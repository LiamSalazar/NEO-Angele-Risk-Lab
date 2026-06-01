"""Report writers for covariance-aware orbital simulation outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.utils.serialization import write_json


class OrbitalSimulationReportWriter:
    """Persist orbital simulation results and summaries."""

    def __init__(
        self,
        output_dir: str | Path = "data/gold/orbital_simulation",
        report_dir: str | Path = "reports/orbital_simulation",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.report_dir = Path(report_dir)

    @property
    def results_path(self) -> Path:
        """Return the main result table path."""
        return self.output_dir / "orbital_monte_carlo_results.parquet"

    def save_outputs(self, results: list[dict[str, Any]]) -> dict[str, str]:
        """Persist tables and report summaries."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        table_rows = [_without_trace(result) for result in results]
        df = pd.DataFrame(table_rows)
        if not df.empty:
            df.to_parquet(self.results_path, index=False)
        else:
            pd.DataFrame().to_parquet(self.results_path, index=False)
        results_csv = self.output_dir / "orbital_monte_carlo_results.csv"
        df.to_csv(results_csv, index=False)
        summary = summarize_results(df)
        summary_json = write_json(summary, self.report_dir / "orbital_simulation_summary.json")
        summary_md = self.report_dir / "orbital_simulation_summary.md"
        summary_md.write_text(render_summary(summary), encoding="utf-8")
        covariance_status_path = write_json(
            covariance_status(df),
            self.report_dir / "orbital_covariance_status.json",
        )
        cad_csv, cad_summary_json, cad_summary_md = write_cad_validation(df, self.report_dir)
        methodology_path = write_methodology(self.report_dir)
        top_uncertainty = self.report_dir / "top_orbital_uncertainty_objects.csv"
        if not df.empty and "dispersion_index" in df.columns:
            df.sort_values("dispersion_index", ascending=False).head(25).to_csv(
                top_uncertainty, index=False
            )
        else:
            pd.DataFrame().to_csv(top_uncertainty, index=False)
        findings_path = write_json(
            {
                "status": "success" if not df.empty else "missing_data",
                "findings": orbital_scenario_findings(df),
            },
            self.report_dir / "orbital_scenario_findings.json",
        )
        return {
            "results_parquet": str(self.results_path),
            "results_csv": str(results_csv),
            "summary_json": str(summary_json),
            "summary_markdown": str(summary_md),
            "orbital_covariance_status_json": str(covariance_status_path),
            "cad_validation_csv": str(cad_csv),
            "cad_validation_summary_json": str(cad_summary_json),
            "cad_validation_summary_markdown": str(cad_summary_md),
            "orbital_simulation_methodology_md": str(methodology_path),
            "top_orbital_uncertainty_objects": str(top_uncertainty),
            "orbital_scenario_findings": str(findings_path),
        }


def summarize_results(df: pd.DataFrame) -> dict[str, Any]:
    """Summarize an orbital simulation result table."""
    if df.empty:
        return {"status": "missing_data", "row_count": 0}
    return {
        "status": "success",
        "row_count": int(len(df)),
        "scenario_category_counts": {
            str(key): int(value)
            for key, value in df["scenario_category"].value_counts(dropna=False).items()
        },
        "mean_dispersion_index": _float_or_none(df["dispersion_index"].mean()),
        "max_dispersion_index": _float_or_none(df["dispersion_index"].max()),
        "min_p05_distance_au": _float_or_none(df["simulated_min_distance_p05_au"].min()),
        "n_clones_median": _float_or_none(df["n_clones"].median()),
        "covariance_available_count": _column_true_count(df, "covariance_available"),
        "heuristic_fallback_count": (
            int((df.get("simulation_method") == "heuristic_fallback").sum())
            if "simulation_method" in df.columns
            else 0
        ),
        "horizon_days_median": _float_or_none(df["horizon_days"].median()),
        "top_uncertainty_objects": df.sort_values("dispersion_index", ascending=False)
        .head(10)["object_key"]
        .astype(str)
        .tolist(),
    }


def orbital_scenario_findings(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Create compact findings from orbital simulation results."""
    if df.empty:
        return []
    top_uncertain = (
        df.sort_values("dispersion_index", ascending=False)
        .head(5)["object_key"]
        .astype(str)
        .tolist()
    )
    close = (
        df.sort_values("simulated_min_distance_p05_au", ascending=True)
        .head(5)["object_key"]
        .astype(str)
        .tolist()
    )
    return [
        {
            "title": "Highest orbital-dispersion objects",
            "short_text": (
                "These objects show the widest clone spread in approximate orbital " "simulations."
            ),
            "technical_basis": "Ranked by dispersion_index.",
            "related_objects": top_uncertain,
            "importance": "medium",
            "source_module": "orbital_simulation",
        },
        {
            "title": "Lowest p05 simulated minimum-distance objects",
            "short_text": "These objects have the smallest lower-tail simulated minimum distances.",
            "technical_basis": "Ranked by simulated_min_distance_p05_au.",
            "related_objects": close,
            "importance": "medium",
            "source_module": "orbital_simulation",
            "caveat": "Approximate orbital scenario analysis based on available orbital elements.",
        },
    ]


def render_summary(summary: dict[str, Any]) -> str:
    """Render a markdown summary."""
    lines = [
        "# Orbital Simulation Summary",
        "",
        "Covariance-aware orbital scenario analysis using SBDB covariance when available and "
        "explicit fallback scenario analysis otherwise.",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def covariance_status(df: pd.DataFrame) -> dict[str, Any]:
    """Summarize covariance coverage and fallback use."""
    if df.empty:
        return {"status": "missing_data", "row_count": 0}
    return {
        "status": "success",
        "row_count": int(len(df)),
        "covariance_available_count": _column_true_count(df, "covariance_available"),
        "covariance_unavailable_count": int(
            len(df) - _column_true_count(df, "covariance_available")
        ),
        "method_counts": {
            str(key): int(value)
            for key, value in df.get("simulation_method", pd.Series(dtype="object"))
            .value_counts(dropna=False)
            .items()
        },
        "valid_clone_count_total": _numeric_sum(df, "valid_clone_count"),
        "invalid_clone_count_total": _numeric_sum(df, "invalid_clone_count"),
        "interpretation": (
            "Rows with covariance_available=false use heuristic_fallback scenario analysis and "
            "are not presented as formal covariance propagation."
        ),
    }


def write_cad_validation(report_df: pd.DataFrame, report_dir: Path) -> tuple[Path, Path, Path]:
    """Write CAD validation rows and summaries."""
    columns = [
        "object_key",
        "cad_validation_available",
        "baseline_min_distance_au",
        "cad_validation_error_au",
        "simulation_method",
    ]
    available_columns = [column for column in columns if column in report_df.columns]
    cad_df = report_df[available_columns].copy() if available_columns else pd.DataFrame()
    csv_path = report_dir / "cad_validation.csv"
    cad_df.to_csv(csv_path, index=False)
    if cad_df.empty:
        summary = {"status": "missing_data", "row_count": 0, "cad_validation_available_count": 0}
    else:
        summary = {
            "status": "success",
            "row_count": int(len(cad_df)),
            "cad_validation_available_count": _column_true_count(
                cad_df,
                "cad_validation_available",
            ),
            "mean_error_au": _series_mean(cad_df, "cad_validation_error_au"),
            "max_error_au": _series_max(cad_df, "cad_validation_error_au"),
            "validation_scope": (
                "Compares simplified two-body nominal minimum distance against available CAD "
                "aggregate distance fields. It is a coarse consistency check."
            ),
        }
    json_path = write_json(summary, report_dir / "cad_validation_summary.json")
    md_path = report_dir / "cad_validation_summary.md"
    md_path.write_text(render_cad_validation_summary(summary), encoding="utf-8")
    return csv_path, json_path, md_path


def render_cad_validation_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# CAD Validation Summary",
        "",
        "Coarse validation of nominal simplified two-body distance against available CAD fields.",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def write_methodology(report_dir: Path) -> Path:
    """Write orbital simulation methodology notes."""
    path = report_dir / "orbital_simulation_methodology.md"
    lines = [
        "# Orbital Simulation Methodology",
        "",
        "The orbital simulator is covariance-aware when SBDB covariance data is present. For "
        "objects without a valid covariance matrix, it uses explicitly marked heuristic "
        "scenario analysis and does not present those clones as formal covariance propagation.",
        "",
        "## Methods",
        "",
        "- `covariance_based`: sample orbital clones from `x ~ N(mu, Sigma)` after covariance "
        "validation and label alignment.",
        "- `heuristic_fallback`: perturb orbital elements from orbit-quality proxies when no valid "
        "covariance is available.",
        "- Propagator: `two_body_kepler_approximation`.",
        "",
        "## Validation",
        "",
        "Covariance matrices are checked for square shape, finite values, symmetry, non-negative "
        "diagonal entries, and positive-semidefinite behavior. Near-PSD matrices can receive "
        "minimal jitter, which is reported.",
        "",
        "CAD validation compares the simplified nominal minimum distance with available CAD "
        "aggregate distance fields and should be treated as a coarse consistency check.",
        "",
        "## Limitations",
        "",
        "- No n-body propagation is implemented.",
        "- Temporal resolution can miss close approaches between time steps.",
        "- Fallback clones are low-quality scenario stress tests, not calibrated uncertainty.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _without_trace(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key != "distance_trace"}


def _float_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return result


def _column_true_count(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0
    return int(df[column].fillna(False).astype(bool).sum())


def _numeric_sum(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0
    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def _series_mean(df: pd.DataFrame, column: str) -> float | None:
    if column not in df.columns:
        return None
    return _float_or_none(pd.to_numeric(df[column], errors="coerce").mean())


def _series_max(df: pd.DataFrame, column: str) -> float | None:
    if column not in df.columns:
        return None
    return _float_or_none(pd.to_numeric(df[column], errors="coerce").max())
