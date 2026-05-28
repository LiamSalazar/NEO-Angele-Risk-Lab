"""Feature-set definitions for baseline ML and leakage-aware experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

IDENTIFIER_OR_METADATA_COLUMNS = {
    "object_key",
    "spkid",
    "des",
    "full_name",
    "name",
    "raw_json",
    "built_at_utc",
    "source_availability_json",
    "next_close_approach_datetime",
    "neo",
    "orbit_class_code",
    "orbit_class_name",
}

DEFINITION_RELATED_COLUMNS = {
    "h",
    "diameter",
    "moid",
    "moid_ld",
    "inverse_moid",
    "log_diameter",
    "size_proxy_score",
    "proximity_proxy_score",
}


@dataclass(frozen=True, slots=True)
class FeatureSetDefinition:
    """Human-readable feature-set metadata."""

    name: str
    features: list[str]
    description: str


class FeatureSetRegistry:
    """Resolve named feature sets against an available pandas DataFrame."""

    FULL_FEATURES = [
        "h",
        "diameter",
        "albedo",
        "e",
        "a",
        "q",
        "i",
        "om",
        "w",
        "ma",
        "n",
        "per",
        "ad",
        "moid",
        "moid_ld",
        "condition_code",
        "arc_length",
        "n_obs_used",
        "rms",
        "min_close_approach_dist",
        "min_close_approach_dist_min",
        "max_close_approach_v_rel",
        "close_approach_count",
        "sentry_flag",
        "sentry_ip",
        "sentry_ps_cum",
        "sentry_ps_max",
        "sentry_ts_max",
        "sentry_n_imp",
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

    DEFINITIONS = {
        "full_features": FeatureSetDefinition(
            name="full_features",
            features=FULL_FEATURES,
            description="All model-ready numeric, boolean, and score features.",
        ),
        "definition_features_only": FeatureSetDefinition(
            name="definition_features_only",
            features=[
                "h",
                "moid",
                "moid_ld",
                "diameter",
                "inverse_moid",
                "size_proxy_score",
                "proximity_proxy_score",
            ],
            description="Features directly related to the approximate PHA definition.",
        ),
        "no_definition_features": FeatureSetDefinition(
            name="no_definition_features",
            features=[
                feature for feature in FULL_FEATURES if feature not in DEFINITION_RELATED_COLUMNS
            ],
            description="Full feature set after removing H, MOID, diameter, and their proxies.",
        ),
        "orbital_only": FeatureSetDefinition(
            name="orbital_only",
            features=["e", "a", "q", "i", "om", "w", "ma", "n", "per", "ad"],
            description="Classical orbital elements only.",
        ),
        "approach_and_quality": FeatureSetDefinition(
            name="approach_and_quality",
            features=[
                "condition_code",
                "arc_length",
                "n_obs_used",
                "rms",
                "min_close_approach_dist",
                "min_close_approach_dist_min",
                "max_close_approach_v_rel",
                "close_approach_count",
                "feature_completeness_ratio",
            ],
            description="Close-approach aggregates plus observation quality features.",
        ),
        "sentry_related": FeatureSetDefinition(
            name="sentry_related",
            features=[
                "sentry_flag",
                "sentry_ip",
                "sentry_ps_cum",
                "sentry_ps_max",
                "sentry_ts_max",
                "sentry_n_imp",
                "sentry_presence_score",
            ],
            description="Sentry hazard-list fields and derived Sentry presence score.",
        ),
    }

    def list_feature_sets(self) -> list[FeatureSetDefinition]:
        """Return all registered feature-set definitions."""
        return list(self.DEFINITIONS.values())

    def names(self) -> list[str]:
        """Return registered feature-set names."""
        return list(self.DEFINITIONS)

    def get(self, name: str) -> FeatureSetDefinition:
        """Return one feature-set definition by name."""
        try:
            return self.DEFINITIONS[name]
        except KeyError as exc:
            allowed = ", ".join(self.names())
            raise ValueError(f"Unknown feature set '{name}'. Expected one of: {allowed}.") from exc

    def resolve(
        self,
        df: pd.DataFrame,
        feature_set_name: str,
        target: str = "pha",
    ) -> dict[str, Any]:
        """Return existing usable features and warnings for missing or unsafe columns."""
        definition = self.get(feature_set_name)
        forbidden = {target, *IDENTIFIER_OR_METADATA_COLUMNS}
        features: list[str] = []
        missing: list[str] = []
        warnings: list[str] = []

        for feature in definition.features:
            if feature in forbidden:
                warnings.append(f"Excluded forbidden feature '{feature}'.")
                continue
            if feature not in df.columns:
                missing.append(feature)
                continue
            features.append(feature)

        if missing:
            warnings.append(
                f"Feature set '{feature_set_name}' omitted missing features: "
                f"{', '.join(missing)}."
            )
        return {
            "name": definition.name,
            "description": definition.description,
            "features": features,
            "missing_features": missing,
            "warnings": warnings,
        }
