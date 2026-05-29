"""Report writers for experimental risk-priority scores."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.risk.ranking import RiskRankingService
from neo_ange.risk.schemas import DEFAULT_COMPONENT_WEIGHTS, RISK_SCORE_VERSION
from neo_ange.utils.serialization import write_json


class RiskReportWriter:
    """Persist risk-score analytical outputs and concise methodology notes."""

    def __init__(
        self,
        score_output_dir: str | Path = "data/gold/risk_scores",
        report_dir: str | Path = "reports/risk",
    ) -> None:
        self.score_output_dir = Path(score_output_dir)
        self.report_dir = Path(report_dir)
        self.ranking = RiskRankingService()

    @property
    def score_path(self) -> Path:
        return self.score_output_dir / "risk_scores.parquet"

    def save_outputs(
        self,
        scored_df: pd.DataFrame,
        summary: dict[str, Any],
        weights: dict[str, float] | None = None,
        top_limit: int = 50,
    ) -> dict[str, str]:
        """Write parquet, summary JSON, top CSV, and methodology Markdown."""
        self.score_output_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        scored_df.to_parquet(self.score_path, index=False)
        summary_path = write_json(summary, self.report_dir / "risk_scores_summary.json")

        top_path = self.report_dir / "top_risk_objects.csv"
        self.ranking.rank(scored_df, limit=top_limit).to_csv(top_path, index=False)

        methodology_path = self.write_methodology(weights or DEFAULT_COMPONENT_WEIGHTS)
        return {
            "risk_scores_parquet": str(self.score_path),
            "risk_scores_summary_json": str(summary_path),
            "top_risk_objects_csv": str(top_path),
            "risk_methodology_md": str(methodology_path),
        }

    def write_methodology(self, weights: dict[str, float] | None = None) -> Path:
        """Write a compact technical methodology document."""
        weights = weights or DEFAULT_COMPONENT_WEIGHTS
        path = self.report_dir / "risk_methodology.md"
        lines = [
            "# Risk Priority Score Methodology",
            "",
            "## Purpose",
            "",
            "The Risk Priority Score is an experimental, explainable ranking signal for the "
            "Neo Angele Risk Lab. It helps prioritize review and follow-up inside this project. "
            "It is not an official alert, impact prediction, or replacement for NASA/JPL CNEOS "
            "or Sentry.",
            "",
            "## Components",
            "",
            "- Physical risk component: estimated diameter, absolute magnitude, and size proxies.",
            "- Orbital risk component: MOID, lunar-distance MOID, perihelion, eccentricity, and inclination.",
            "- Approach risk component: close-approach distance, relative velocity, and approach count.",
            "- Sentry risk component: Sentry presence, impact probability fields, Palermo/Torino fields, and virtual-impact count when available.",
            "- Uncertainty risk component: orbit condition code, RMS, observation arc, and observation count.",
            "- Data quality component: missingness and weaker observation coverage as a small moderator.",
            "",
            "## Weights",
            "",
            *[f"- `{name}`: {value:.2f}" for name, value in weights.items()],
            "",
            "## Categories",
            "",
            "- low: score < 20",
            "- moderate: 20 <= score < 40",
            "- elevated: 40 <= score < 60",
            "- high: 60 <= score < 80",
            "- critical: score >= 80",
            "",
            "## Limitations",
            "",
            "- The score is feature-based and educational; it is not a professional orbital propagation.",
            "- Sparse rows can still be scored, but explanations flag limited data coverage.",
            "- Sentry absence is treated as a low component, not proof of no risk.",
            "- Future Monte Carlo reports perturb score inputs to estimate score stability, not impact probability.",
            "",
            f"Score version: `{RISK_SCORE_VERSION}`",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
