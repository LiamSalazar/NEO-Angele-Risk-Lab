"""Factories that translate tabular rows into domain entities."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from neo_ange.domain.approach import CloseApproachSummary
from neo_ange.domain.asteroid import Asteroid
from neo_ange.domain.identity import AsteroidIdentity
from neo_ange.domain.orbit import Orbit
from neo_ange.domain.physical import PhysicalProperties
from neo_ange.domain.risk import RiskScore
from neo_ange.domain.sentry import SentryRiskSignal
from neo_ange.domain.simulation import MonteCarloResult


class AsteroidFactory:
    """Build domain objects from gold, risk-score, and simulation records."""

    @classmethod
    def from_gold_row(cls, row: dict[str, Any] | pd.Series) -> Asteroid:
        """Create an asteroid aggregate from a gold feature row."""
        data = _clean_row(row)
        object_key = _string_or_none(
            data.get("object_key")
            or data.get("spkid")
            or data.get("des")
            or data.get("full_name")
            or data.get("name")
        )
        identity = AsteroidIdentity(
            object_key=object_key,
            spkid=_string_or_none(data.get("spkid")),
            des=_string_or_none(data.get("des")),
            full_name=_string_or_none(data.get("full_name")),
            name=_string_or_none(data.get("name")),
            orbit_class_code=_string_or_none(data.get("orbit_class_code")),
            orbit_class_name=_string_or_none(data.get("orbit_class_name")),
        )
        orbit = Orbit(
            e=_float_or_none(data.get("e")),
            a=_float_or_none(data.get("a")),
            q=_float_or_none(data.get("q")),
            i=_float_or_none(data.get("i")),
            om=_float_or_none(data.get("om")),
            w=_float_or_none(data.get("w")),
            ma=_float_or_none(data.get("ma")),
            n=_float_or_none(data.get("n")),
            per=_float_or_none(data.get("per")),
            ad=_float_or_none(data.get("ad")),
            moid=_float_or_none(data.get("moid")),
            moid_ld=_float_or_none(data.get("moid_ld")),
            condition_code=data.get("condition_code"),
            arc_length=_float_or_none(data.get("arc_length")),
            n_obs_used=_int_or_none(data.get("n_obs_used")),
            rms=_float_or_none(data.get("rms")),
        )
        physical = PhysicalProperties(
            h=_float_or_none(data.get("h")),
            diameter=_float_or_none(data.get("diameter")),
            albedo=_float_or_none(data.get("albedo")),
            log_diameter=_float_or_none(data.get("log_diameter")),
        )
        approach = CloseApproachSummary(
            min_close_approach_dist=_float_or_none(data.get("min_close_approach_dist")),
            min_close_approach_dist_min=_float_or_none(data.get("min_close_approach_dist_min")),
            max_close_approach_v_rel=_float_or_none(data.get("max_close_approach_v_rel")),
            next_close_approach_datetime=_string_or_none(data.get("next_close_approach_datetime")),
            close_approach_count=_int_or_none(data.get("close_approach_count")),
        )
        sentry = SentryRiskSignal(
            sentry_flag=_bool_or_none(data.get("sentry_flag")),
            sentry_ip=_float_or_none(data.get("sentry_ip")),
            sentry_ps_cum=_float_or_none(data.get("sentry_ps_cum")),
            sentry_ps_max=_float_or_none(data.get("sentry_ps_max")),
            sentry_ts_max=_float_or_none(data.get("sentry_ts_max")),
            sentry_n_imp=_int_or_none(data.get("sentry_n_imp")),
        )
        return Asteroid(
            identity=identity,
            orbit=orbit,
            physical=physical,
            close_approach_summary=approach if approach.has_close_approach_data() else None,
            sentry_signal=sentry if sentry.has_sentry_signal() else None,
            neo=_bool_or_none(data.get("neo")),
            pha=_bool_or_none(data.get("pha")),
        )

    @classmethod
    def from_risk_row(cls, row: dict[str, Any] | pd.Series) -> tuple[Asteroid, RiskScore | None]:
        """Create an asteroid aggregate and optional score from a risk-score row."""
        data = _clean_row(row)
        asteroid = cls.from_gold_row(data)
        if "risk_score_0_100" not in data and "risk_score" not in data:
            return asteroid, None
        return asteroid, cls.risk_score_from_row(data)

    @classmethod
    def many_from_dataframe(cls, df: pd.DataFrame) -> list[Asteroid]:
        """Create asteroid aggregates from every row in a frame."""
        if df.empty:
            return []
        return [cls.from_gold_row(row) for _, row in df.iterrows()]

    @classmethod
    def risk_score_from_row(cls, row: dict[str, Any] | pd.Series) -> RiskScore:
        """Create a RiskScore entity from a scored row."""
        data = _clean_row(row)
        object_key = _string_or_none(
            data.get("object_key")
            or data.get("spkid")
            or data.get("des")
            or data.get("full_name")
            or data.get("name")
        )
        return RiskScore(
            object_key=object_key or "unknown-object",
            risk_score=_float_or_none(data.get("risk_score")),
            risk_score_0_100=_float_or_none(data.get("risk_score_0_100")),
            risk_category=_string_or_none(data.get("risk_category")),
            physical_risk_component=_float_or_none(data.get("physical_risk_component")),
            orbital_risk_component=_float_or_none(data.get("orbital_risk_component")),
            approach_risk_component=_float_or_none(data.get("approach_risk_component")),
            sentry_risk_component=_float_or_none(data.get("sentry_risk_component")),
            uncertainty_risk_component=_float_or_none(data.get("uncertainty_risk_component")),
            data_quality_component=_float_or_none(data.get("data_quality_component")),
            score_version=_string_or_none(data.get("score_version")),
            scored_at_utc=_string_or_none(data.get("scored_at_utc")),
        )

    @classmethod
    def monte_carlo_result_from_dict(cls, data: dict[str, Any]) -> MonteCarloResult:
        """Create a MonteCarloResult from a serialized result dictionary."""
        clean = _clean_row(data)
        return MonteCarloResult(
            object_key=_string_or_none(clean.get("object_key")) or "unknown-object",
            n_simulations=_int_or_none(clean.get("n_simulations")),
            base_score=_float_or_none(clean.get("base_score")),
            mean_score=_float_or_none(clean.get("mean_score")),
            std_score=_float_or_none(clean.get("std_score")),
            p05_score=_float_or_none(clean.get("p05_score")),
            p25_score=_float_or_none(clean.get("p25_score")),
            median_score=_float_or_none(clean.get("median_score")),
            p75_score=_float_or_none(clean.get("p75_score")),
            p95_score=_float_or_none(clean.get("p95_score")),
            max_score=_float_or_none(clean.get("max_score")),
            probability_score_above_60=_float_or_none(clean.get("probability_score_above_60")),
            probability_score_above_80=_float_or_none(clean.get("probability_score_above_80")),
            category_shift_probability=_float_or_none(clean.get("category_shift_probability")),
            base_category=_string_or_none(clean.get("base_category")),
            p95_category=_string_or_none(clean.get("p95_category")),
            simulation_version=_string_or_none(clean.get("simulation_version")),
        )


def _clean_row(row: dict[str, Any] | pd.Series) -> dict[str, Any]:
    values = row.to_dict() if isinstance(row, pd.Series) else dict(row)
    return {key: _none_if_missing(value) for key, value in values.items()}


def _none_if_missing(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _float_or_none(value: Any) -> float | None:
    value = _none_if_missing(value)
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _int_or_none(value: Any) -> int | None:
    numeric = _float_or_none(value)
    if numeric is None:
        return None
    return int(numeric)


def _bool_or_none(value: Any) -> bool | None:
    value = _none_if_missing(value)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            return None
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"true", "t", "1", "yes", "y"}:
        return True
    if normalized in {"false", "f", "0", "no", "n"}:
        return False
    return None


def _string_or_none(value: Any) -> str | None:
    value = _none_if_missing(value)
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "null"}:
        return None
    return text
