from __future__ import annotations

import pandas as pd

from neo_ange.ml.feature_sets import FeatureSetRegistry


def test_registry_lists_feature_sets() -> None:
    registry = FeatureSetRegistry()

    assert "full_features" in registry.names()
    assert "no_definition_features" in registry.names()


def test_resolve_omits_missing_and_target() -> None:
    registry = FeatureSetRegistry()
    df = pd.DataFrame({"pha": [0], "h": [20.0], "moid": [0.01], "e": [0.2]})

    resolved = registry.resolve(df, "full_features", target="pha")

    assert "pha" not in resolved["features"]
    assert "h" in resolved["features"]
    assert resolved["missing_features"]
    assert resolved["warnings"]


def test_no_definition_features_excludes_definition_columns() -> None:
    registry = FeatureSetRegistry()
    definition = registry.get("no_definition_features")

    for feature in [
        "h",
        "diameter",
        "moid",
        "moid_ld",
        "inverse_moid",
        "log_diameter",
        "size_proxy_score",
        "proximity_proxy_score",
    ]:
        assert feature not in definition.features
