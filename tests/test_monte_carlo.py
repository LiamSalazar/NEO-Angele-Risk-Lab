from __future__ import annotations

import pandas as pd

from neo_ange.risk.scoring import RiskScorer
from neo_ange.simulation.monte_carlo import MonteCarloEngine


def test_simulate_object_generates_summary() -> None:
    row = _scored_features().iloc[0].to_dict()

    result = MonteCarloEngine().simulate_object(row, n_simulations=50, random_state=42)

    for key in ["p05_score", "p95_score", "median_score", "mean_score"]:
        assert key in result
    assert 0 <= result["probability_score_above_60"] <= 1
    assert 0 <= result["probability_score_above_80"] <= 1
    assert 0 <= result["category_shift_probability"] <= 1


def test_simulate_batch_processes_multiple_objects() -> None:
    df = _scored_features()

    result = MonteCarloEngine().simulate_batch(df, limit=2, n_simulations=20, random_state=5)

    assert result["status"] == "success"
    assert len(result["results"]) == 2


def _scored_features() -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {
                "object_key": "A",
                "diameter": 1.0,
                "h": 18.5,
                "moid": 0.02,
                "moid_ld": 8.0,
                "min_close_approach_dist": 0.01,
                "max_close_approach_v_rel": 22.0,
                "sentry_flag": True,
                "sentry_ip": 1e-5,
                "sentry_ps_cum": -3.0,
                "condition_code": 5,
                "rms": 0.5,
                "arc_length": 120,
                "n_obs_used": 40,
                "feature_completeness_ratio": 0.9,
            },
            {
                "object_key": "B",
                "diameter": 0.2,
                "h": 23.0,
                "moid": 0.15,
                "sentry_flag": False,
                "condition_code": 2,
                "arc_length": 800,
                "n_obs_used": 120,
                "feature_completeness_ratio": 0.7,
            },
        ]
    )
    return RiskScorer().score_dataframe(df)
