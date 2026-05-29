from __future__ import annotations

import pandas as pd

from neo_ange.domain.repositories import (
    GoldFeatureRepository,
    RiskScoreRepository,
    SimulationResultRepository,
)


def test_domain_repositories_load_parquet(tmp_path) -> None:
    gold_root = tmp_path / "gold"
    features = gold_root / "neo_risk_features"
    risk = gold_root / "risk_scores"
    simulation = gold_root / "simulation_results"
    features.mkdir(parents=True)
    risk.mkdir(parents=True)
    simulation.mkdir(parents=True)

    pd.DataFrame(
        {"object_key": ["100"], "e": [0.1], "a": [1.0], "q": [0.8], "i": [2.0]}
    ).to_parquet(features / "part.parquet")
    pd.DataFrame({"object_key": ["100"], "risk_score_0_100": [42.0]}).to_parquet(
        risk / "risk_scores.parquet"
    )
    pd.DataFrame(
        {
            "object_key": ["100"],
            "n_simulations": [10],
            "mean_score": [43.0],
            "simulated_at_utc": ["2026-05-29T00:00:00Z"],
        }
    ).to_parquet(simulation / "monte_carlo_results.parquet")

    assert GoldFeatureRepository(gold_root).count() == 1
    assert GoldFeatureRepository(gold_root).get_by_object_key("100") is not None
    assert RiskScoreRepository(gold_root).get_score("100").risk_score_0_100 == 42.0
    assert SimulationResultRepository(gold_root).get_latest_for_object("100").mean_score == 43.0
