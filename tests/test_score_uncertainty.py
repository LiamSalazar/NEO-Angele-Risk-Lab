from __future__ import annotations

import numpy as np
import pandas as pd

from neo_ange.simulation.uncertainty import (
    build_uncertainty_specs,
    refresh_derived_features,
    sample_score_inputs,
)


def test_uncertainty_specs_mark_fallback_without_reported_uncertainty() -> None:
    specs = build_uncertainty_specs({"h": 20.0, "moid": 0.02})

    assert specs
    assert {spec.mode for spec in specs} == {"heuristic_fallback"}


def test_sample_score_inputs_recomputes_derived_features() -> None:
    row = {"object_key": "A", "diameter": 1.0, "moid": 0.02}
    specs = build_uncertainty_specs(row)
    sampled = sample_score_inputs(row, specs, 5, np.random.default_rng(42))

    assert len(sampled) == 5
    assert "log_diameter" in sampled.columns
    assert "inverse_moid" in sampled.columns


def test_refresh_derived_features_updates_inverse_moid() -> None:
    refreshed = refresh_derived_features(pd.DataFrame([{"moid": 0.0}, {"moid": 1.0}]))

    assert refreshed["inverse_moid"].tolist() == [1.0, 0.5]
