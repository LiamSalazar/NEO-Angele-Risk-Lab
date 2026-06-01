from __future__ import annotations

from neo_ange.risk.scoring import RiskScorer


def test_lower_h_increases_physical_component() -> None:
    scorer = RiskScorer()
    base = _base_row()
    lower_h = dict(base, h=17.0)
    higher_h = dict(base, h=23.0)

    assert (
        scorer.score_row(lower_h)["physical_risk_component"]
        > scorer.score_row(higher_h)["physical_risk_component"]
    )


def test_lower_moid_increases_orbital_component() -> None:
    scorer = RiskScorer()
    close = dict(_base_row(), moid=0.01, moid_ld=3.9)
    farther = dict(_base_row(), moid=0.20, moid_ld=77.8)

    assert (
        scorer.score_row(close)["orbital_risk_component"]
        > scorer.score_row(farther)["orbital_risk_component"]
    )


def test_higher_sentry_ip_increases_sentry_component() -> None:
    scorer = RiskScorer()
    low = dict(_base_row(), sentry_flag=True, sentry_ip=1e-8)
    high = dict(_base_row(), sentry_flag=True, sentry_ip=1e-4)

    assert (
        scorer.score_row(high)["sentry_risk_component"]
        > scorer.score_row(low)["sentry_risk_component"]
    )


def test_worse_condition_code_and_rms_increase_uncertainty_component() -> None:
    scorer = RiskScorer()
    good = dict(_base_row(), condition_code=1, rms=0.2)
    poor = dict(_base_row(), condition_code=8, rms=1.5)

    assert (
        scorer.score_row(poor)["uncertainty_risk_component"]
        > scorer.score_row(good)["uncertainty_risk_component"]
    )


def test_higher_completeness_reduces_data_quality_penalty() -> None:
    scorer = RiskScorer()
    complete = dict(_base_row(), feature_completeness_ratio=0.95)
    sparse = dict(_base_row(), feature_completeness_ratio=0.40)

    assert (
        scorer.score_row(complete)["data_quality_component"]
        < scorer.score_row(sparse)["data_quality_component"]
    )


def _base_row() -> dict[str, object]:
    return {
        "object_key": "monotonicity-case",
        "h": 20.0,
        "diameter": 0.5,
        "moid": 0.05,
        "moid_ld": 19.5,
        "q": 0.9,
        "e": 0.3,
        "i": 8.0,
        "min_close_approach_dist": 0.03,
        "max_close_approach_v_rel": 20.0,
        "sentry_flag": False,
        "sentry_ip": 0.0,
        "condition_code": 3,
        "rms": 0.4,
        "arc_length": 500,
        "n_obs_used": 100,
        "feature_completeness_ratio": 0.8,
    }
