from __future__ import annotations

import pandas as pd

from neo_ange.risk.schemas import DEFAULT_COMPONENT_WEIGHTS, RISK_SCORE_COLUMNS
from neo_ange.risk.scoring import RiskScorer


def test_score_dataframe_adds_expected_columns_and_bounds() -> None:
    df = _sample_features()
    scored = RiskScorer().score_dataframe(df)

    for column in RISK_SCORE_COLUMNS:
        assert column in scored.columns
    assert scored["risk_score_0_100"].between(0, 100).all()
    assert scored[["risk_score", "risk_score_0_100"]].isna().sum().sum() == 0


def test_score_dataframe_handles_nulls_without_nan_scores() -> None:
    df = pd.DataFrame(
        [
            {
                "object_key": "null-object",
                "diameter": None,
                "h": None,
                "moid": None,
                "sentry_flag": None,
            }
        ]
    )

    scored = RiskScorer().score_dataframe(df)

    assert scored["risk_score_0_100"].between(0, 100).all()
    assert scored["risk_score_0_100"].isna().sum() == 0


def test_weights_sum_and_custom_weights_are_normalized() -> None:
    assert round(sum(DEFAULT_COMPONENT_WEIGHTS.values()), 10) == 1.0

    scorer = RiskScorer(
        {
            "physical_risk_component": 2,
            "orbital_risk_component": 2,
            "approach_risk_component": 2,
            "sentry_risk_component": 2,
            "uncertainty_risk_component": 1,
            "data_quality_component": 1,
        }
    )

    assert round(sum(scorer.weights.values()), 10) == 1.0


def _sample_features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "object_key": "A",
                "des": "2026 AA",
                "diameter": 0.8,
                "h": 19.5,
                "log_diameter": 0.58,
                "size_proxy_score": 0.55,
                "moid": 0.02,
                "moid_ld": 7.8,
                "inverse_moid": 0.98,
                "q": 0.9,
                "e": 0.45,
                "i": 12.0,
                "min_close_approach_dist": 0.015,
                "min_close_approach_dist_min": 0.012,
                "max_close_approach_v_rel": 28.0,
                "close_approach_count": 5,
                "inverse_min_distance": 0.99,
                "relative_velocity_score": 0.56,
                "sentry_flag": True,
                "sentry_ip": 1e-5,
                "sentry_ps_cum": -3.0,
                "sentry_ps_max": -3.5,
                "sentry_ts_max": 1.0,
                "sentry_n_imp": 2,
                "condition_code": 5,
                "rms": 0.7,
                "arc_length": 120.0,
                "n_obs_used": 45,
                "uncertainty_proxy_score": 0.55,
                "feature_completeness_ratio": 0.9,
            }
        ]
    )
