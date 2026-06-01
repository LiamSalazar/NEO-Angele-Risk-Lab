"""Uncertainty models for Risk Score propagation.

The score simulator deliberately separates uncertainty propagation from
deterministic sensitivity analysis.  Most public SBDB/CAD/Sentry fields do not
ship object-specific measurement uncertainties in the current gold table, so
the module records whether each sampled variable is empirical, reported, or a
heuristic fallback instead of presenting every run as formal Monte Carlo.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

SCORE_UNCERTAINTY_VERSION = "risk-score-uncertainty-v0.2.0"

BASE_SCORE_VARIABLES = [
    "h",
    "diameter",
    "albedo",
    "moid",
    "moid_ld",
    "min_close_approach_dist",
    "min_close_approach_dist_min",
    "max_close_approach_v_rel",
    "sentry_ip",
    "sentry_ps_cum",
    "sentry_ps_max",
    "sentry_ts_max",
    "condition_code",
    "rms",
    "arc_length",
    "n_obs_used",
]

DERIVED_SCORE_VARIABLES = [
    "log_diameter",
    "inverse_moid",
    "inverse_min_distance",
    "relative_velocity_score",
    "observation_quality_score",
    "uncertainty_proxy_score",
    "size_proxy_score",
    "proximity_proxy_score",
    "sentry_presence_score",
    "feature_completeness_ratio",
]

POSITIVE_VARIABLES = {
    "diameter",
    "albedo",
    "moid",
    "moid_ld",
    "min_close_approach_dist",
    "min_close_approach_dist_min",
    "max_close_approach_v_rel",
    "rms",
    "arc_length",
    "n_obs_used",
}

PROBABILITY_VARIABLES = {"sentry_ip"}
INTEGER_VARIABLES = {"condition_code", "n_obs_used"}

HEURISTIC_RELATIVE_SCALE = {
    "diameter": 0.25,
    "albedo": 0.25,
    "moid": 0.20,
    "moid_ld": 0.20,
    "min_close_approach_dist": 0.20,
    "min_close_approach_dist_min": 0.20,
    "max_close_approach_v_rel": 0.10,
    "arc_length": 0.20,
    "n_obs_used": 0.20,
}

HEURISTIC_ABSOLUTE_SCALE = {
    "h": 0.30,
    "condition_code": 0.75,
    "rms": 0.05,
    "sentry_ps_cum": 0.35,
    "sentry_ps_max": 0.35,
    "sentry_ts_max": 0.50,
}


@dataclass(frozen=True, slots=True)
class UncertaintySpec:
    """Serializable distribution declaration for one base score variable."""

    variable_name: str
    distribution_type: str
    parameters: dict[str, float | str | int | None]
    source: str
    justification: str
    mode: str
    is_formal_uncertainty: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""
        return asdict(self)


def build_uncertainty_specs(
    row: dict[str, Any] | pd.Series,
    reference_df: pd.DataFrame | None = None,
) -> list[UncertaintySpec]:
    """Build one uncertainty declaration per available base variable."""
    source = _row_to_dict(row)
    specs: list[UncertaintySpec] = []
    for variable in BASE_SCORE_VARIABLES:
        value = _to_float(source.get(variable))
        if value is None:
            continue
        reported_sigma = _reported_sigma(source, variable)
        if reported_sigma is not None and reported_sigma > 0:
            specs.append(_reported_uncertainty_spec(variable, value, reported_sigma))
            continue
        empirical_scale = _empirical_scale(reference_df, variable)
        if empirical_scale is not None and empirical_scale > 0:
            specs.append(_empirical_uncertainty_spec(variable, value, empirical_scale))
            continue
        specs.append(_heuristic_fallback_spec(variable, value))
    return specs


def sample_score_inputs(
    row: dict[str, Any] | pd.Series,
    specs: list[UncertaintySpec],
    n_simulations: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Sample base variables and recompute derived score features."""
    base = _row_to_dict(row)
    n = max(int(n_simulations), 1)
    records = [dict(base, simulation_index=index) for index in range(n)]
    frame = pd.DataFrame(records)
    for spec in specs:
        if spec.variable_name not in frame.columns:
            continue
        frame[spec.variable_name] = _sample_variable(spec, n, rng)
    return refresh_derived_features(apply_score_bounds(frame))


def apply_score_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """Apply basic physical/probability bounds to sampled base variables."""
    bounded = df.copy()
    for column in POSITIVE_VARIABLES:
        if column in bounded.columns:
            bounded[column] = pd.to_numeric(bounded[column], errors="coerce").clip(lower=0)
    if "sentry_ip" in bounded.columns:
        bounded["sentry_ip"] = pd.to_numeric(bounded["sentry_ip"], errors="coerce").clip(0.0, 1.0)
    if "condition_code" in bounded.columns:
        bounded["condition_code"] = (
            pd.to_numeric(bounded["condition_code"], errors="coerce").round().clip(0, 9)
        )
    if "n_obs_used" in bounded.columns:
        bounded["n_obs_used"] = (
            pd.to_numeric(bounded["n_obs_used"], errors="coerce").round().clip(lower=0)
        )
    return bounded


def refresh_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute score-derived variables from sampled base variables."""
    refreshed = df.copy()
    index = refreshed.index
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
    if {"n_obs_used", "arc_length", "rms"}.intersection(refreshed.columns):
        obs = _numeric_series(refreshed, "n_obs_used", index)
        arc = _numeric_series(refreshed, "arc_length", index)
        rms = _numeric_series(refreshed, "rms", index)
        obs_quality = (np.log1p(obs.clip(lower=0)) / 9.21).clip(0.0, 1.0)
        arc_quality = (np.log1p(arc.clip(lower=0)) / 10.5).clip(0.0, 1.0)
        rms_quality = (1.0 / (1.0 + rms.clip(lower=0))).clip(0.0, 1.0)
        refreshed["observation_quality_score"] = (
            obs_quality.fillna(0.0) * 0.45
            + arc_quality.fillna(0.0) * 0.45
            + rms_quality.fillna(0.0) * 0.10
        ).clip(0.0, 1.0)
    if {"diameter", "h"}.intersection(refreshed.columns):
        diameter_score = pd.Series(np.nan, index=index, dtype="float64")
        if "diameter" in refreshed.columns:
            diameter = pd.to_numeric(refreshed["diameter"], errors="coerce")
            diameter_score = (np.log1p(diameter.clip(lower=0)) / np.log1p(10.0)).clip(0.0, 1.0)
        h_score = pd.Series(np.nan, index=index, dtype="float64")
        if "h" in refreshed.columns:
            h_value = pd.to_numeric(refreshed["h"], errors="coerce")
            h_score = ((30.0 - h_value) / 15.0).clip(0.0, 1.0)
        refreshed["size_proxy_score"] = diameter_score.fillna(h_score).fillna(0.0)
    if {"moid", "min_close_approach_dist"}.intersection(refreshed.columns):
        inverse_moid = _numeric_series(refreshed, "inverse_moid", index).fillna(0.0)
        inverse_distance = _numeric_series(refreshed, "inverse_min_distance", index).fillna(0.0)
        refreshed["proximity_proxy_score"] = np.maximum(inverse_moid, inverse_distance)
    if {"condition_code", "arc_length", "n_obs_used", "rms"}.intersection(refreshed.columns):
        condition = _numeric_series(refreshed, "condition_code", index) / 9.0
        refreshed["uncertainty_proxy_score"] = condition.clip(0.0, 1.0).fillna(0.35)
    return refreshed.replace([np.inf, -np.inf], np.nan)


def summarize_uncertainty_sources(specs: list[UncertaintySpec]) -> dict[str, Any]:
    """Summarize source quality for a simulation run."""
    source_counts: dict[str, int] = {}
    for spec in specs:
        source_counts[spec.source] = source_counts.get(spec.source, 0) + 1
    formal_count = sum(1 for spec in specs if spec.is_formal_uncertainty)
    fallback_count = sum(1 for spec in specs if spec.mode == "heuristic_fallback")
    if formal_count and fallback_count == 0:
        method = "uncertainty_propagation"
    elif any(spec.mode == "empirical_uncertainty" for spec in specs):
        method = "uncertainty_propagation"
    else:
        method = "heuristic_fallback"
    return {
        "simulation_method": method,
        "uncertainty_source": ", ".join(sorted(source_counts)) if source_counts else "none",
        "uncertainty_sources": [spec.to_dict() for spec in specs],
        "source_counts": source_counts,
        "fallback_count": fallback_count,
        "fallback_used": fallback_count > 0,
        "is_formal_uncertainty": bool(specs) and fallback_count == 0 and formal_count == len(specs),
    }


def _reported_uncertainty_spec(
    variable: str,
    value: float,
    sigma: float,
) -> UncertaintySpec:
    distribution = "bounded_normal"
    if variable in POSITIVE_VARIABLES and value > 0:
        distribution = "lognormal_positive"
    if variable in PROBABILITY_VARIABLES:
        distribution = "beta_probability"
    return UncertaintySpec(
        variable_name=variable,
        distribution_type=distribution,
        parameters={"center": value, "scale": float(sigma), "lower": _lower_bound(variable)},
        source="reported_uncertainty",
        justification=(
            "A source-specific uncertainty column was present for this variable in the input row."
        ),
        mode="reported_uncertainty",
        is_formal_uncertainty=True,
    )


def _empirical_uncertainty_spec(
    variable: str,
    value: float,
    scale: float,
) -> UncertaintySpec:
    distribution = "bounded_normal"
    if variable in POSITIVE_VARIABLES and value > 0:
        distribution = "lognormal_positive"
    if variable in PROBABILITY_VARIABLES:
        distribution = "beta_probability"
    return UncertaintySpec(
        variable_name=variable,
        distribution_type=distribution,
        parameters={"center": value, "scale": float(scale), "lower": _lower_bound(variable)},
        source="empirical_from_dataset",
        justification=(
            "No object-specific uncertainty was available; scale was estimated from the "
            "available dataset distribution and is reported as empirical, not calibrated."
        ),
        mode="empirical_uncertainty",
        is_formal_uncertainty=False,
    )


def _heuristic_fallback_spec(variable: str, value: float) -> UncertaintySpec:
    scale = HEURISTIC_ABSOLUTE_SCALE.get(variable)
    if scale is None:
        relative = HEURISTIC_RELATIVE_SCALE.get(variable, 0.10)
        scale = max(abs(value) * relative, 0.01)
    distribution = "bounded_normal"
    if variable in POSITIVE_VARIABLES and value > 0:
        distribution = "lognormal_positive"
        relative = HEURISTIC_RELATIVE_SCALE.get(variable, 0.10)
        scale = max(relative, min(float(scale) / max(abs(value), 1e-9), 1.0))
    if variable in PROBABILITY_VARIABLES:
        distribution = "beta_probability"
        scale = 200.0
    return UncertaintySpec(
        variable_name=variable,
        distribution_type=distribution,
        parameters={"center": value, "scale": float(scale), "lower": _lower_bound(variable)},
        source="heuristic_fallback",
        justification=(
            "No reported or dataset-estimated uncertainty was available; this variable is "
            "sampled only as an explicitly marked fallback stress model."
        ),
        mode="heuristic_fallback",
        is_formal_uncertainty=False,
    )


def _sample_variable(
    spec: UncertaintySpec,
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    center = float(spec.parameters.get("center") or 0.0)
    scale = float(spec.parameters.get("scale") or 0.0)
    if spec.distribution_type == "lognormal_positive" and center > 0:
        values = rng.lognormal(mean=math.log(center), sigma=max(scale, 1e-9), size=n)
    elif spec.distribution_type == "beta_probability":
        probability = min(max(center, 0.0), 1.0)
        concentration = max(scale, 2.0)
        alpha = max(probability * concentration, 1e-6)
        beta = max((1.0 - probability) * concentration, 1e-6)
        values = rng.beta(alpha, beta, size=n)
    else:
        values = rng.normal(loc=center, scale=max(scale, 1e-9), size=n)
    lower = _lower_bound(spec.variable_name)
    if lower is not None:
        values = np.clip(values, lower, None)
    if spec.variable_name in INTEGER_VARIABLES:
        values = np.rint(values)
    return values


def _reported_sigma(row: dict[str, Any], variable: str) -> float | None:
    for key in (f"{variable}_sigma", f"{variable}_uncertainty", f"{variable}_std"):
        value = _to_float(row.get(key))
        if value is not None and value > 0:
            return value
    return None


def _empirical_scale(reference_df: pd.DataFrame | None, variable: str) -> float | None:
    if reference_df is None or reference_df.empty or variable not in reference_df.columns:
        return None
    values = pd.to_numeric(reference_df[variable], errors="coerce").replace(
        [np.inf, -np.inf], np.nan
    )
    values = values.dropna()
    if len(values) < 20:
        return None
    q25 = float(values.quantile(0.25))
    q75 = float(values.quantile(0.75))
    iqr = q75 - q25
    if variable in POSITIVE_VARIABLES:
        positive = values[values > 0]
        if len(positive) < 20:
            return None
        log_values = np.log(positive)
        scale = float(np.nanstd(log_values, ddof=0))
        return min(max(scale, 0.02), 0.75)
    scale = iqr / 1.349 if iqr > 0 else float(values.std(ddof=0))
    if not math.isfinite(scale) or scale <= 0:
        return None
    return min(scale, max(abs(float(values.median())) * 0.5, 1.0))


def _lower_bound(variable: str) -> float | None:
    if variable in POSITIVE_VARIABLES or variable in PROBABILITY_VARIABLES:
        return 0.0
    if variable == "condition_code":
        return 0.0
    return None


def _numeric_series(df: pd.DataFrame, column: str, index: pd.Index) -> pd.Series:
    if column not in df.columns:
        return pd.Series(np.nan, index=index, dtype="float64")
    return pd.to_numeric(df[column], errors="coerce")


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
