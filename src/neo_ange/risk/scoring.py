"""Experimental, explainable risk-priority score computation."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from neo_ange.risk.categories import RiskCategoryAssigner
from neo_ange.risk.explanations import RiskExplanationService
from neo_ange.risk.schemas import (
    COMPONENT_COLUMNS,
    DEFAULT_COMPONENT_WEIGHTS,
    RISK_SCORE_VERSION,
)


class RiskScorer:
    """Compute a reproducible experimental priority score from gold features."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = self._validate_weights(weights or DEFAULT_COMPONENT_WEIGHTS)
        self.category_assigner = RiskCategoryAssigner()

    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of ``df`` with risk-priority columns added."""
        if df.empty:
            result = df.copy()
            for column in [
                "risk_score",
                "risk_score_0_100",
                *self.component_columns(),
                "risk_category",
                "risk_explanation_short",
                "scored_at_utc",
                "score_version",
            ]:
                if column not in result.columns:
                    result[column] = pd.Series(dtype="object")
            return result

        scored_rows = [self.score_row(row) for _, row in df.iterrows()]
        scored = pd.DataFrame(scored_rows, index=df.index)
        result = df.copy()
        for column in scored.columns:
            result[column] = scored[column]
        return result

    def score_row(self, row: pd.Series | dict[str, Any]) -> dict[str, Any]:
        """Score one object row and return only the derived scoring fields."""
        values = _row_to_dict(row)
        components = {
            "physical_risk_component": self._physical_component(values),
            "orbital_risk_component": self._orbital_component(values),
            "approach_risk_component": self._approach_component(values),
            "sentry_risk_component": self._sentry_component(values),
            "uncertainty_risk_component": self._uncertainty_component(values),
            "data_quality_component": self._data_quality_component(values),
        }
        risk_score = sum(components[name] * self.weights[name] for name in COMPONENT_COLUMNS)
        risk_score = _bounded(risk_score)
        score_0_100 = round(risk_score * 100.0, 6)
        category = self.category_assigner.assign(score_0_100)
        explanation_row = {
            **values,
            **components,
            "risk_score": risk_score,
            "risk_score_0_100": score_0_100,
            "risk_category": category,
        }
        explanation = RiskExplanationService().explain_row(explanation_row)
        return {
            "risk_score": risk_score,
            "risk_score_0_100": score_0_100,
            **components,
            "risk_category": category,
            "risk_explanation_short": explanation["short_explanation"],
            "scored_at_utc": datetime.now(UTC).isoformat(),
            "score_version": self.score_version(),
        }

    def component_columns(self) -> list[str]:
        """Return the score component columns in formula order."""
        return list(COMPONENT_COLUMNS)

    def score_version(self) -> str:
        """Return the stable score formula version."""
        return RISK_SCORE_VERSION

    def _physical_component(self, row: dict[str, Any]) -> float:
        diameter = _to_float(row.get("diameter"))
        h_value = _to_float(row.get("h"))
        log_diameter = _to_float(row.get("log_diameter"))
        size_proxy = _to_float(row.get("size_proxy_score"))

        diameter_score = _bounded(math.log1p(diameter) / math.log1p(10.0)) if diameter else None
        h_score = _bounded((30.0 - h_value) / 15.0) if h_value is not None else None
        log_diameter_score = _bounded(log_diameter / math.log1p(10.0)) if log_diameter else None
        size_proxy_score = _bounded(size_proxy) if size_proxy is not None else None

        return _weighted_available(
            [
                (diameter_score, 0.35),
                (h_score, 0.30),
                (log_diameter_score, 0.15),
                (size_proxy_score, 0.20),
            ],
            default=0.0,
        )

    def _orbital_component(self, row: dict[str, Any]) -> float:
        moid = _to_float(row.get("moid"))
        moid_ld = _to_float(row.get("moid_ld"))
        inverse_moid = _to_float(row.get("inverse_moid"))
        q_value = _to_float(row.get("q"))
        eccentricity = _to_float(row.get("e"))
        inclination = _to_float(row.get("i"))

        moid_score = (
            _bounded(1.0 / (1.0 + max(moid, 0.0) * 20.0)) if moid is not None else None
        )
        moid_ld_score = (
            _bounded(1.0 / (1.0 + max(moid_ld, 0.0) / 10.0))
            if moid_ld is not None
            else None
        )
        inverse_moid_score = _bounded(inverse_moid) if inverse_moid is not None else None
        q_score = _bounded((1.3 - q_value) / 1.3) if q_value is not None else None
        eccentricity_score = _bounded(eccentricity) if eccentricity is not None else None
        inclination_score = _bounded(inclination / 40.0) if inclination is not None else None

        return _weighted_available(
            [
                (moid_score, 0.35),
                (moid_ld_score, 0.20),
                (inverse_moid_score, 0.15),
                (q_score, 0.10),
                (eccentricity_score, 0.12),
                (inclination_score, 0.08),
            ],
            default=0.0,
        )

    def _approach_component(self, row: dict[str, Any]) -> float:
        distance = _to_float(row.get("min_close_approach_dist"))
        distance_min = _to_float(row.get("min_close_approach_dist_min"))
        velocity = _to_float(row.get("max_close_approach_v_rel"))
        approach_count = _to_float(row.get("close_approach_count"))
        inverse_distance = _to_float(row.get("inverse_min_distance"))
        velocity_score = _to_float(row.get("relative_velocity_score"))

        distance_score = (
            _bounded(1.0 / (1.0 + max(distance, 0.0) * 25.0))
            if distance is not None
            else None
        )
        min_distance_score = (
            _bounded(1.0 / (1.0 + max(distance_min, 0.0) * 25.0))
            if distance_min is not None
            else None
        )
        inverse_distance_score = _bounded(inverse_distance) if inverse_distance is not None else None
        direct_velocity_score = _bounded(velocity / 50.0) if velocity is not None else None
        stored_velocity_score = _bounded(velocity_score) if velocity_score is not None else None
        count_score = (
            _bounded(math.log1p(max(approach_count, 0.0)) / math.log1p(25.0))
            if approach_count is not None
            else None
        )

        return _weighted_available(
            [
                (distance_score, 0.28),
                (min_distance_score, 0.20),
                (inverse_distance_score, 0.14),
                (direct_velocity_score, 0.16),
                (stored_velocity_score, 0.12),
                (count_score, 0.10),
            ],
            default=0.0,
        )

    def _sentry_component(self, row: dict[str, Any]) -> float:
        flag_score = 1.0 if _to_bool(row.get("sentry_flag")) else 0.0
        presence = _to_float(row.get("sentry_presence_score"))
        sentry_ip = _to_float(row.get("sentry_ip"))
        ps_cum = _to_float(row.get("sentry_ps_cum"))
        ps_max = _to_float(row.get("sentry_ps_max"))
        ts_max = _to_float(row.get("sentry_ts_max"))
        n_imp = _to_float(row.get("sentry_n_imp"))

        ip_score = _probability_signal(sentry_ip) if sentry_ip is not None else None
        ps_cum_score = _palermo_signal(ps_cum) if ps_cum is not None else None
        ps_max_score = _palermo_signal(ps_max) if ps_max is not None else None
        ts_score = _bounded(ts_max / 10.0) if ts_max is not None else None
        impact_count_score = (
            _bounded(math.log1p(max(n_imp, 0.0)) / math.log1p(100.0))
            if n_imp is not None
            else None
        )

        return _weighted_available(
            [
                (flag_score, 0.20),
                (_bounded(presence) if presence is not None else None, 0.15),
                (ip_score, 0.25),
                (ps_cum_score, 0.13),
                (ps_max_score, 0.12),
                (ts_score, 0.10),
                (impact_count_score, 0.05),
            ],
            default=0.0,
        )

    def _uncertainty_component(self, row: dict[str, Any]) -> float:
        condition_code = _to_float(row.get("condition_code"))
        rms = _to_float(row.get("rms"))
        arc_length = _to_float(row.get("arc_length"))
        n_obs = _to_float(row.get("n_obs_used"))
        uncertainty_proxy = _to_float(row.get("uncertainty_proxy_score"))

        condition_score = _bounded(condition_code / 9.0) if condition_code is not None else None
        rms_score = _bounded(rms / 2.0) if rms is not None else None
        short_arc_score = (
            1.0 - _bounded(math.log1p(max(arc_length, 0.0)) / math.log1p(3650.0))
            if arc_length is not None
            else None
        )
        low_obs_score = (
            1.0 - _bounded(math.log1p(max(n_obs, 0.0)) / math.log1p(1000.0))
            if n_obs is not None
            else None
        )
        proxy_score = _bounded(uncertainty_proxy) if uncertainty_proxy is not None else None

        return _weighted_available(
            [
                (condition_score, 0.28),
                (rms_score, 0.18),
                (short_arc_score, 0.22),
                (low_obs_score, 0.20),
                (proxy_score, 0.12),
            ],
            default=0.35,
        )

    def _data_quality_component(self, row: dict[str, Any]) -> float:
        completeness = _to_float(row.get("feature_completeness_ratio"))
        arc_length = _to_float(row.get("arc_length"))
        n_obs = _to_float(row.get("n_obs_used"))

        incompleteness_score = (
            1.0 - _bounded(completeness) if completeness is not None else None
        )
        short_arc_score = (
            1.0 - _bounded(math.log1p(max(arc_length, 0.0)) / math.log1p(3650.0))
            if arc_length is not None
            else None
        )
        low_obs_score = (
            1.0 - _bounded(math.log1p(max(n_obs, 0.0)) / math.log1p(1000.0))
            if n_obs is not None
            else None
        )

        return _weighted_available(
            [
                (incompleteness_score, 0.50),
                (short_arc_score, 0.25),
                (low_obs_score, 0.25),
            ],
            default=0.40,
        )

    def _validate_weights(self, weights: dict[str, float]) -> dict[str, float]:
        missing = [column for column in COMPONENT_COLUMNS if column not in weights]
        if missing:
            raise ValueError(f"Missing risk-score weights for components: {missing}")
        cleaned: dict[str, float] = {}
        for column in COMPONENT_COLUMNS:
            value = _to_float(weights[column])
            if value is None or value < 0:
                raise ValueError(f"Weight for {column} must be a non-negative finite number.")
            cleaned[column] = value
        total = sum(cleaned.values())
        if not math.isfinite(total) or total <= 0:
            raise ValueError("Risk-score weights must have a positive finite sum.")
        if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
            cleaned = {column: value / total for column, value in cleaned.items()}
        return cleaned


def _row_to_dict(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    if isinstance(row, pd.Series):
        return row.to_dict()
    return dict(row)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if value is pd.NA:
        return None
    try:
        if isinstance(value, str) and value.strip() == "":
            return None
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value is pd.NA:
        return False
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    normalized = str(value).strip().lower()
    return normalized in {"true", "t", "1", "yes", "y"}


def _bounded(value: float | None, lower: float = 0.0, upper: float = 1.0) -> float:
    if value is None:
        return 0.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(numeric):
        return 0.0
    return min(max(numeric, lower), upper)


def _weighted_available(values: list[tuple[float | None, float]], default: float) -> float:
    available = [(value, weight) for value, weight in values if value is not None]
    if not available:
        return _bounded(default)
    total_weight = sum(weight for _, weight in available)
    if total_weight <= 0:
        return _bounded(default)
    return _bounded(sum(_bounded(value) * weight for value, weight in available) / total_weight)


def _probability_signal(value: float) -> float:
    probability = _bounded(value, 0.0, 1.0)
    if probability <= 0:
        return 0.0
    return _bounded((math.log10(probability) + 10.0) / 10.0)


def _palermo_signal(value: float) -> float:
    return _bounded((value + 8.0) / 10.0)
