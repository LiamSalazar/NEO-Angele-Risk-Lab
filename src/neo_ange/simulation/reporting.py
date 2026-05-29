"""Report writers for approximate Monte Carlo simulations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.simulation.schemas import MONTE_CARLO_VERSION
from neo_ange.utils.serialization import write_json


class SimulationReportWriter:
    """Persist Monte Carlo summaries and methodology notes."""

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

    def save_outputs(self, results: list[dict[str, Any]]) -> dict[str, str]:
        """Write summary JSON/CSV, methodology, and parquet result rows."""
        self.result_output_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        new_df = pd.DataFrame(results)
        if self.results_path.exists():
            existing = pd.read_parquet(self.results_path)
            combined = pd.concat([existing, new_df], ignore_index=True)
        else:
            combined = new_df
        combined.to_parquet(self.results_path, index=False)

        summary_path = write_json(
            {
                "status": "success",
                "n_result_rows": int(len(combined)),
                "latest_results": results,
                "simulation_version": MONTE_CARLO_VERSION,
            },
            self.report_dir / "monte_carlo_summary.json",
        )
        csv_path = self.report_dir / "monte_carlo_summary.csv"
        combined.to_csv(csv_path, index=False)
        methodology_path = self.write_methodology()
        return {
            "monte_carlo_results_parquet": str(self.results_path),
            "monte_carlo_summary_json": str(summary_path),
            "monte_carlo_summary_csv": str(csv_path),
            "monte_carlo_methodology_md": str(methodology_path),
        }

    def write_methodology(self) -> Path:
        """Write a compact technical methodology note."""
        path = self.report_dir / "monte_carlo_methodology.md"
        lines = [
            "# Monte Carlo Simulation Methodology",
            "",
            "## Purpose",
            "",
            "The Monte Carlo workflow estimates the stability of the experimental Risk Priority "
            "Score under approximate input perturbations. It is not an official orbital "
            "propagation and does not estimate professional impact probability.",
            "",
            "## Perturbation approach",
            "",
            "The simulator perturbs score inputs such as diameter, H, MOID, close-approach "
            "distance, velocity, Sentry probability fields, condition code, RMS, observation "
            "arc, and observation count. Positive quantities use lognormal-style variation; "
            "bounded fields are clipped to simple physical or probability ranges.",
            "",
            "## Interpretation",
            "",
            "- `p95_score` is the 95th percentile of simulated score outcomes.",
            "- `std_score` describes score spread under approximate perturbations.",
            "- `category_shift_probability` is the share of simulations whose score category "
            "differs from the base category.",
            "",
            "## Limitations",
            "",
            "- This simulation perturbs tabular score inputs, not orbital states.",
            "- It should be read as score stability analysis, not impact-probability prediction.",
            "- Sparse source data can make the simulated distribution less informative.",
            "",
            f"Simulation version: `{MONTE_CARLO_VERSION}`",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
