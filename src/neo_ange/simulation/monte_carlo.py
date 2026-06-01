"""Risk Score uncertainty propagation and sensitivity analysis engine."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from neo_ange.domain.asteroid import Asteroid
from neo_ange.risk.categories import RiskCategoryAssigner
from neo_ange.risk.ranking import RiskRankingService
from neo_ange.risk.scoring import RiskScorer
from neo_ange.simulation.perturbation import PerturbationConfig, PerturbationEngine
from neo_ange.simulation.schemas import MONTE_CARLO_VERSION
from neo_ange.simulation.sensitivity import SensitivityAnalyzer
from neo_ange.utils.serialization import to_jsonable


class MonteCarloEngine:
    """Run score uncertainty propagation over base score inputs."""

    def __init__(self, risk_scorer: RiskScorer | None = None) -> None:
        self.risk_scorer = risk_scorer or RiskScorer()
        self.perturbation_engine = PerturbationEngine()
        self.sensitivity = SensitivityAnalyzer(self.risk_scorer)
        self.categories = RiskCategoryAssigner()
        self.ranking = RiskRankingService()

    def simulate_object(
        self,
        row: dict[str, Any] | pd.Series | Asteroid,
        n_simulations: int = 1000,
        random_state: int | None = 42,
        reference_df: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        """Sample one object's base variables and summarize propagated score outcomes."""
        base_row = _row_to_dict(row)
        config = PerturbationConfig(
            n_simulations=n_simulations,
            random_state=random_state,
            clip_values=True,
        )
        perturbed = self.perturbation_engine.perturb_row(
            base_row,
            config,
            reference_df=reference_df,
        )
        scored = self.risk_scorer.score_dataframe(perturbed)
        summary = self.summarize_simulated_scores(scored, base_row)
        sensitivity_rows = self.sensitivity.top_sensitivity_factors(base_row, limit=5)
        summary.update(self.perturbation_engine.last_uncertainty_summary)
        summary["most_influential_variables"] = sensitivity_rows
        summary["score_sensitivity_index"] = _score_sensitivity_index(
            summary.get("std_score"),
            summary.get("base_score"),
            sensitivity_rows,
        )
        summary["random_state"] = random_state
        summary["simulated_at_utc"] = datetime.now(UTC).isoformat()
        return to_jsonable(summary)

    def simulate_batch(
        self,
        df: pd.DataFrame,
        limit: int = 50,
        n_simulations: int = 500,
        random_state: int | None = 42,
    ) -> dict[str, Any]:
        """Simulate the top scored objects, or first N rows when no score exists."""
        if df.empty:
            return {
                "status": "missing_data",
                "results": [],
                "summary": {"n_objects": 0},
                "warnings": ["Risk scores are not available for batch simulation."],
            }
        source = (
            self.ranking.rank(df, limit=limit)
            if "risk_score_0_100" in df.columns
            else df.head(limit)
        )
        results = []
        for index, (_, row) in enumerate(source.iterrows()):
            seed = None if random_state is None else int(random_state) + index
            results.append(
                self.simulate_object(
                    row,
                    n_simulations=n_simulations,
                    random_state=seed,
                    reference_df=df,
                )
            )
        mean_scores = [item["mean_score"] for item in results if item.get("mean_score") is not None]
        summary = {
            "n_objects": len(results),
            "n_simulations_per_object": int(max(n_simulations, 1)),
            "mean_of_mean_scores": float(np.mean(mean_scores)) if mean_scores else None,
            "max_p95_score": max((item.get("p95_score", 0.0) for item in results), default=None),
            "simulation_version": self.simulation_version(),
        }
        return {
            "status": "success",
            "results": to_jsonable(results),
            "summary": to_jsonable(summary),
            "warnings": [],
        }

    def summarize_simulated_scores(
        self,
        simulated_df: pd.DataFrame,
        base_row: dict[str, Any],
    ) -> dict[str, Any]:
        """Summarize simulated 0-100 risk scores for one object."""
        scores = pd.to_numeric(simulated_df["risk_score_0_100"], errors="coerce").fillna(0.0)
        base_scored = dict(base_row)
        if "risk_score_0_100" not in base_scored or pd.isna(base_scored.get("risk_score_0_100")):
            base_scored.update(self.risk_scorer.score_row(base_row))
        base_score = float(base_scored.get("risk_score_0_100", 0.0) or 0.0)
        base_category = str(base_scored.get("risk_category") or self.categories.assign(base_score))
        categories = simulated_df["risk_category"].fillna("low").astype(str)
        category_shift_probability = (
            float((categories != base_category).mean()) if len(categories) else 0.0
        )
        p95_score = float(scores.quantile(0.95)) if len(scores) else 0.0
        return {
            "object_key": _object_key(base_row),
            "n_simulations": int(len(scores)),
            "base_score": base_score,
            "mean_score": float(scores.mean()) if len(scores) else 0.0,
            "mean": float(scores.mean()) if len(scores) else 0.0,
            "std_score": float(scores.std(ddof=0)) if len(scores) else 0.0,
            "std": float(scores.std(ddof=0)) if len(scores) else 0.0,
            "min_score": float(scores.min()) if len(scores) else 0.0,
            "p05_score": float(scores.quantile(0.05)) if len(scores) else 0.0,
            "p05": float(scores.quantile(0.05)) if len(scores) else 0.0,
            "p25_score": float(scores.quantile(0.25)) if len(scores) else 0.0,
            "median_score": float(scores.median()) if len(scores) else 0.0,
            "p50": float(scores.median()) if len(scores) else 0.0,
            "p75_score": float(scores.quantile(0.75)) if len(scores) else 0.0,
            "p95_score": p95_score,
            "p95": p95_score,
            "max_score": float(scores.max()) if len(scores) else 0.0,
            "probability_score_above_60": float((scores > 60.0).mean()) if len(scores) else 0.0,
            "probability_score_above_80": float((scores > 80.0).mean()) if len(scores) else 0.0,
            "prob_score_gt_60": float((scores > 60.0).mean()) if len(scores) else 0.0,
            "prob_score_gt_80": float((scores > 80.0).mean()) if len(scores) else 0.0,
            "category_shift_probability": category_shift_probability,
            "base_category": base_category,
            "p95_category": self.categories.assign(p95_score),
            "simulation_version": self.simulation_version(),
        }

    def simulation_version(self) -> str:
        """Return the stable simulation version."""
        return MONTE_CARLO_VERSION


def _row_to_dict(row: dict[str, Any] | pd.Series | Asteroid) -> dict[str, Any]:
    if isinstance(row, Asteroid):
        return row.to_feature_dict()
    if isinstance(row, pd.Series):
        return row.to_dict()
    return dict(row)


def _object_key(row: dict[str, Any]) -> str:
    for key in ("object_key", "spkid", "des", "full_name", "name"):
        value = row.get(key)
        if value is not None and not pd.isna(value):
            return str(value)
    return "unknown-object"


def _score_sensitivity_index(
    std_score: Any,
    base_score: Any,
    sensitivity_rows: list[dict[str, Any]],
) -> float:
    try:
        std_part = float(std_score or 0.0) / max(abs(float(base_score or 0.0)), 1.0)
    except (TypeError, ValueError):
        std_part = 0.0
    max_delta = 0.0
    for row in sensitivity_rows:
        try:
            max_delta = max(max_delta, abs(float(row.get("absolute_effect") or 0.0)) / 100.0)
        except (TypeError, ValueError):
            continue
    return float(min(max(std_part + max_delta, 0.0), 1.0))
