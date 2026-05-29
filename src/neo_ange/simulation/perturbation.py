"""Approximate perturbation engine for Monte Carlo score simulations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from neo_ange.simulation.schemas import PERTURBED_VARIABLES


@dataclass(slots=True)
class PerturbationConfig:
    """Configuration for approximate score-input perturbations."""

    n_simulations: int = 1000
    random_state: int | None = 42
    clip_values: bool = True


class PerturbationEngine:
    """Generate stochastic perturbations for variables that feed the score."""

    variables = list(PERTURBED_VARIABLES)

    def perturb_row(
        self,
        row: dict[str, Any] | pd.Series,
        config: PerturbationConfig,
    ) -> pd.DataFrame:
        """Return one row per perturbed scenario while preserving object identity."""
        base = _row_to_dict(row)
        n_simulations = max(int(config.n_simulations), 1)
        rng = np.random.default_rng(config.random_state)
        records = [dict(base, simulation_index=index) for index in range(n_simulations)]
        df = pd.DataFrame(records)

        for variable in self.variables:
            if variable not in base:
                continue
            value = _to_float(base.get(variable))
            if value is None:
                df[variable] = base.get(variable)
                continue
            df[variable] = self._perturb_values(value, variable, n_simulations, rng)

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
        bounded = df.copy()
        non_negative = [
            "diameter",
            "moid",
            "moid_ld",
            "min_close_approach_dist",
            "min_close_approach_dist_min",
            "max_close_approach_v_rel",
            "rms",
            "arc_length",
            "n_obs_used",
        ]
        for column in non_negative:
            if column in bounded.columns:
                bounded[column] = pd.to_numeric(bounded[column], errors="coerce").clip(lower=0)
        if "sentry_ip" in bounded.columns:
            bounded["sentry_ip"] = pd.to_numeric(bounded["sentry_ip"], errors="coerce").clip(
                0.0, 1.0
            )
        if "condition_code" in bounded.columns:
            bounded["condition_code"] = (
                pd.to_numeric(bounded["condition_code"], errors="coerce").round().clip(0, 9)
            )
        if "n_obs_used" in bounded.columns:
            bounded["n_obs_used"] = (
                pd.to_numeric(bounded["n_obs_used"], errors="coerce").round().clip(lower=0)
            )
        return _refresh_derived_features(bounded)

    def _perturb_values(
        self,
        value: float,
        variable: str,
        n_simulations: int,
        rng: np.random.Generator,
    ) -> np.ndarray:
        scale = self.infer_scale(value, variable)
        if variable in {
            "diameter",
            "moid",
            "moid_ld",
            "min_close_approach_dist",
            "min_close_approach_dist_min",
            "sentry_ip",
            "arc_length",
            "n_obs_used",
        }:
            if value <= 0:
                return rng.normal(loc=value, scale=max(scale, 0.01), size=n_simulations)
            return rng.lognormal(mean=math.log(value), sigma=scale, size=n_simulations)
        return rng.normal(loc=value, scale=scale, size=n_simulations)


def _refresh_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    refreshed = df.copy()
    if "diameter" in refreshed.columns:
        diameter = pd.to_numeric(refreshed["diameter"], errors="coerce")
        refreshed["log_diameter"] = np.where(diameter > 0, np.log1p(diameter), np.nan)
    if "moid" in refreshed.columns:
        moid = pd.to_numeric(refreshed["moid"], errors="coerce").clip(lower=0)
        refreshed["inverse_moid"] = 1.0 / (1.0 + moid)
    if "min_close_approach_dist" in refreshed.columns:
        distance = pd.to_numeric(refreshed["min_close_approach_dist"], errors="coerce").clip(
            lower=0
        )
        refreshed["inverse_min_distance"] = 1.0 / (1.0 + distance)
    if "max_close_approach_v_rel" in refreshed.columns:
        velocity = pd.to_numeric(refreshed["max_close_approach_v_rel"], errors="coerce")
        refreshed["relative_velocity_score"] = (velocity / 50.0).clip(0.0, 1.0)
    if "sentry_ip" in refreshed.columns:
        sentry = pd.to_numeric(refreshed["sentry_ip"], errors="coerce")
        refreshed["sentry_flag"] = sentry.fillna(0.0) > 0
        refreshed["sentry_presence_score"] = np.where(sentry.fillna(0.0) > 0, 1.0, 0.0)
    if {"diameter", "h"}.intersection(refreshed.columns):
        diameter_score = pd.Series(np.nan, index=refreshed.index, dtype="float64")
        if "diameter" in refreshed.columns:
            diameter = pd.to_numeric(refreshed["diameter"], errors="coerce")
            diameter_score = (np.log1p(diameter.clip(lower=0)) / np.log1p(10.0)).clip(0.0, 1.0)
        h_score = pd.Series(np.nan, index=refreshed.index, dtype="float64")
        if "h" in refreshed.columns:
            h_value = pd.to_numeric(refreshed["h"], errors="coerce")
            h_score = ((30.0 - h_value) / 15.0).clip(0.0, 1.0)
        refreshed["size_proxy_score"] = diameter_score.fillna(h_score).fillna(0.0)
    if {"condition_code", "arc_length", "n_obs_used", "rms"}.intersection(refreshed.columns):
        condition = (
            pd.to_numeric(refreshed.get("condition_code"), errors="coerce") / 9.0
            if "condition_code" in refreshed.columns
            else pd.Series(np.nan, index=refreshed.index)
        )
        refreshed["uncertainty_proxy_score"] = condition.clip(0.0, 1.0).fillna(0.35)
    return refreshed.replace([np.inf, -np.inf], np.nan)


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
