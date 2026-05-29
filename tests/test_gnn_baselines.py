from __future__ import annotations

import pandas as pd

from neo_ange.gnn.baselines import GraphBaselineRunner


def _baseline_df(n: int = 40) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "object_key": [f"obj-{i}" for i in range(n)],
            "pha": [i % 2 == 0 for i in range(n)],
            "e": [0.1 + i * 0.001 for i in range(n)],
            "a": [1.0 + i * 0.01 for i in range(n)],
            "q": [0.8 + i * 0.002 for i in range(n)],
            "i": [2.0 + i * 0.03 for i in range(n)],
            "om": [float(i) for i in range(n)],
            "w": [float(i) for i in range(n)],
            "ma": [float(i) for i in range(n)],
            "n": [0.2 + i * 0.001 for i in range(n)],
            "per": [300 + i for i in range(n)],
            "ad": [1.2 + i * 0.01 for i in range(n)],
            "risk_score_0_100": [float(i) for i in range(n)],
        }
    )


def test_graph_baselines_run_on_synthetic_data() -> None:
    runner = GraphBaselineRunner(random_state=7)
    df = _baseline_df()

    logistic = runner.run_logistic_regression_baseline(df, feature_set="orbital_only")
    forest = runner.run_random_forest_baseline(df, feature_set="orbital_only")
    mlp = runner.run_mlp_baseline(df, feature_set="orbital_only")

    assert logistic["status"] == "success"
    assert forest["status"] == "success"
    assert mlp["status"] in {"success", "failed"}


def test_graph_baselines_handle_small_data() -> None:
    result = GraphBaselineRunner().run_logistic_regression_baseline(_baseline_df(2))

    assert result["status"] == "insufficient_data"
