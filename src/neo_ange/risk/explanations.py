"""Human-readable explanations for experimental risk-priority scores."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


class RiskExplanationService:
    """Explain score drivers without presenting the score as an official alert."""

    _DRIVERS = {
        "physical_risk_component": (
            "physical_size",
            "Larger estimated size or lower absolute magnitude raises experimental priority.",
        ),
        "orbital_risk_component": (
            "orbital_proximity",
            "Lower MOID or more pronounced orbital proximity signals increase follow-up priority.",
        ),
        "approach_risk_component": (
            "close_approach_context",
            "Closer or faster recorded approaches increase experimental follow-up priority.",
        ),
        "sentry_risk_component": (
            "sentry_related_signal",
            "Sentry-related signal is present and raises the lab priority score.",
        ),
        "uncertainty_risk_component": (
            "orbital_uncertainty",
            "Limited orbital certainty raises follow-up priority rather than impact certainty.",
        ),
        "data_quality_component": (
            "data_quality_gap",
            "Limited data coverage adds a small priority adjustment.",
        ),
    }

    def explain_row(self, row: pd.Series | dict[str, Any]) -> dict[str, Any]:
        """Return structured explanatory text and factor lists for one scored object."""
        values = _row_to_dict(row)
        object_key = _object_key(values)
        score = _clean_float(values.get("risk_score_0_100"), default=0.0)
        category = str(values.get("risk_category") or "low")
        drivers = self.identify_main_drivers(values)
        protective = self.identify_protective_factors(values)
        limitations = self.identify_data_limitations(values)

        if drivers:
            lead = drivers[0]["factor"].replace("_", " ")
            short = (
                f"{object_key} has {category} experimental priority "
                f"({score:.1f}/100), mainly driven by {lead}."
            )
        else:
            short = (
                f"{object_key} has {category} experimental priority "
                f"({score:.1f}/100) with no dominant driver in the available data."
            )

        technical = (
            "This explanation summarizes component-level contributors to an experimental, "
            "educational risk-priority score. It indicates follow-up priority within this lab "
            "workflow and does not replace NASA/JPL CNEOS, Sentry, or professional orbital "
            "analysis."
        )
        if limitations:
            technical += f" Data limitations noted: {'; '.join(limitations)}."

        return {
            "object_key": object_key,
            "risk_score_0_100": round(score, 6),
            "risk_category": category,
            "main_drivers": drivers,
            "protective_factors": protective,
            "data_limitations": limitations,
            "short_explanation": short,
            "technical_explanation": technical,
        }

    def identify_main_drivers(self, row: pd.Series | dict[str, Any]) -> list[dict[str, Any]]:
        """Identify high component values that drove the score upward."""
        values = _row_to_dict(row)
        drivers = []
        for component, (factor, interpretation) in self._DRIVERS.items():
            component_value = _clean_float(values.get(component), default=None)
            if component_value is None or component_value < 0.45:
                continue
            drivers.append(
                {
                    "factor": factor,
                    "component": component,
                    "value": round(component_value, 6),
                    "interpretation": interpretation,
                }
            )
        drivers.sort(key=lambda item: item["value"], reverse=True)
        if not drivers:
            fallback = self._top_available_component(values)
            if fallback is not None:
                component, component_value = fallback
                factor, interpretation = self._DRIVERS[component]
                drivers.append(
                    {
                        "factor": factor,
                        "component": component,
                        "value": round(component_value, 6),
                        "interpretation": interpretation,
                    }
                )
        return drivers[:4]

    def identify_protective_factors(self, row: pd.Series | dict[str, Any]) -> list[dict[str, Any]]:
        """Identify low component values or stronger observation context."""
        values = _row_to_dict(row)
        protective: list[dict[str, Any]] = []
        checks = [
            (
                "orbital_distance",
                "orbital_risk_component",
                "Available orbital proximity signals are comparatively low.",
            ),
            (
                "limited_sentry_signal",
                "sentry_risk_component",
                "No strong Sentry-related signal is present in the available features.",
            ),
            (
                "physical_size_signal",
                "physical_risk_component",
                "Available size proxies do not dominate the priority score.",
            ),
        ]
        for factor, component, interpretation in checks:
            component_value = _clean_float(values.get(component), default=None)
            if component_value is not None and component_value <= 0.20:
                protective.append(
                    {
                        "factor": factor,
                        "component": component,
                        "value": round(component_value, 6),
                        "interpretation": interpretation,
                    }
                )

        completeness = _clean_float(values.get("feature_completeness_ratio"), default=None)
        if completeness is not None and completeness >= 0.75:
            protective.append(
                {
                    "factor": "feature_completeness",
                    "component": "data_quality_component",
                    "value": round(completeness, 6),
                    "interpretation": "Feature coverage is relatively complete for this dataset.",
                }
            )
        return protective[:4]

    def identify_data_limitations(self, row: pd.Series | dict[str, Any]) -> list[str]:
        """Return concise data limitations detected from missing or weak fields."""
        values = _row_to_dict(row)
        limitations: list[str] = []
        important_fields = [
            "diameter",
            "h",
            "moid",
            "min_close_approach_dist",
            "max_close_approach_v_rel",
            "condition_code",
            "arc_length",
            "n_obs_used",
            "rms",
        ]
        missing = [field for field in important_fields if _is_missing(values.get(field))]
        if len(missing) >= 4:
            limitations.append(f"limited data coverage; missing fields include {', '.join(missing[:5])}")

        completeness = _clean_float(values.get("feature_completeness_ratio"), default=None)
        if completeness is not None and completeness < 0.60:
            limitations.append("feature completeness is below 60 percent")

        arc_length = _clean_float(values.get("arc_length"), default=None)
        if arc_length is not None and arc_length < 30:
            limitations.append("short observation arc may increase follow-up uncertainty")

        n_obs = _clean_float(values.get("n_obs_used"), default=None)
        if n_obs is not None and n_obs < 20:
            limitations.append("low observation count may make the priority less stable")

        if "sentry_ip" not in values and "sentry_flag" not in values:
            limitations.append("Sentry-related fields are not available in this row")

        return limitations

    def _top_available_component(self, row: dict[str, Any]) -> tuple[str, float] | None:
        candidates: list[tuple[str, float]] = []
        for component in self._DRIVERS:
            value = _clean_float(row.get(component), default=None)
            if value is not None:
                candidates.append((component, value))
        if not candidates:
            return None
        return max(candidates, key=lambda item: item[1])


def _row_to_dict(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    if isinstance(row, pd.Series):
        return row.to_dict()
    return dict(row)


def _object_key(row: dict[str, Any]) -> str:
    for key in ("object_key", "spkid", "des", "full_name", "name"):
        value = row.get(key)
        if not _is_missing(value):
            return str(value)
    return "unknown-object"


def _is_missing(value: Any) -> bool:
    if value is None or value is pd.NA:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _clean_float(value: Any, default: float | None) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(numeric):
        return default
    return numeric
