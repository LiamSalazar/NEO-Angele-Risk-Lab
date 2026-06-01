"""Perturbation engine for Risk Score uncertainty propagation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from neo_ange.simulation.schemas import PERTURBED_VARIABLES
from neo_ange.simulation.uncertainty import (
    apply_score_bounds,
    build_uncertainty_specs,
    refresh_derived_features,
    sample_score_inputs,
    summarize_uncertainty_sources,
)


@dataclass(slots=True)
class PerturbationConfig:
    """Configuration for approximate score-input perturbations."""

    n_simulations: int = 1000
    random_state: int | None = 42
    clip_values: bool = True


class PerturbationEngine:
    """Generate sampled base variables for score uncertainty propagation."""

    variables = list(PERTURBED_VARIABLES)
    last_uncertainty_summary: dict[str, Any] = {}

    def perturb_row(
        self,
        row: dict[str, Any] | pd.Series,
        config: PerturbationConfig,
        reference_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Return one row per sampled scenario while preserving object identity.

        Only base variables are sampled.  Derived score features are recomputed
        from the sampled base values by ``refresh_derived_features``.
        """
        base = _row_to_dict(row)
        n_simulations = max(int(config.n_simulations), 1)
        rng = np.random.default_rng(config.random_state)
        specs = build_uncertainty_specs(base, reference_df=reference_df)
        df = sample_score_inputs(base, specs, n_simulations, rng)
        self.last_uncertainty_summary = summarize_uncertainty_sources(specs)
        if config.clip_values:
            df = self.apply_bounds(df)
        return df

    def infer_scale(self, value: Any, variable_name: str) -> float:
        """Infer a reasonable perturbation scale for a variable."""
        numeric = _to_float(value)
        if numeric is None:
            return 0.0
        if variable_name in {"diameter", "moid", "moid_ld"}:
            return 0.25
        if variable_name in {"min_close_approach_dist", "min_close_approach_dist_min"}:
            return 0.20
        if variable_name == "max_close_approach_v_rel":
            return max(abs(numeric) * 0.10, 0.25)
        if variable_name == "sentry_ip":
            return 0.60
        if variable_name == "sentry_ps_cum":
            return 0.35
        if variable_name == "h":
            return 0.30
        if variable_name == "condition_code":
            return 0.75
        if variable_name == "rms":
            return max(abs(numeric) * 0.25, 0.05)
        if variable_name in {"arc_length", "n_obs_used"}:
            return 0.25
        return max(abs(numeric) * 0.10, 0.01)

    def apply_bounds(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clip perturbed values to simple physical/probability bounds."""
        return refresh_derived_features(apply_score_bounds(df))


def _row_to_dict(row: dict[str, Any] | pd.Series) -> dict[str, Any]:
    if isinstance(row, pd.Series):
        return row.to_dict()
    return dict(row)


def _to_float(value: Any) -> float | None:
    if value is None or value is pd.NA:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric
