"""Report writers for approximate orbital simulation outputs."""

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
        summary = summarize_results(df)
        summary_json = write_json(summary, self.report_dir / "orbital_simulation_summary.json")
        summary_md = self.report_dir / "orbital_simulation_summary.md"
        summary_md.write_text(render_summary(summary), encoding="utf-8")
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
            "summary_json": str(summary_json),
            "summary_markdown": str(summary_md),
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
        "Approximate orbital scenario analysis based on available orbital elements.",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


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
