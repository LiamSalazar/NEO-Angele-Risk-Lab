from __future__ import annotations

import pandas as pd

from neo_ange.pipelines.simulation import SimulationPipeline
from neo_ange.risk.scoring import RiskScorer


def test_simulation_pipeline_saves_outputs_and_latest(tmp_path) -> None:
    risk_scores_dir = tmp_path / "gold" / "risk_scores"
    risk_scores_dir.mkdir(parents=True)
    scored = RiskScorer().score_dataframe(
        pd.DataFrame(
            [
                {
                    "object_key": "A",
                    "diameter": 1.0,
                    "h": 18.5,
                    "moid": 0.02,
                    "min_close_approach_dist": 0.01,
                    "sentry_flag": True,
                    "sentry_ip": 1e-5,
                    "condition_code": 5,
                    "arc_length": 120,
                    "n_obs_used": 40,
                    "feature_completeness_ratio": 0.9,
                }
            ]
        )
    )
    scored.to_parquet(risk_scores_dir / "risk_scores.parquet", index=False)
    pipeline = SimulationPipeline(
        gold_root=tmp_path / "gold",
        report_dir=tmp_path / "reports" / "simulation",
        manifest_dir=tmp_path / "reports" / "manifests",
    )

    object_result = pipeline.simulate_object("A", n_simulations=20, random_state=42)
    batch_result = pipeline.simulate_batch(limit=1, n_simulations=10, random_state=42)
    latest = pipeline.latest_for_object("A")
    status = pipeline.status()

    assert object_result["status"] == "success"
    assert batch_result["status"] == "success"
    assert (tmp_path / "reports" / "simulation" / "monte_carlo_summary.json").exists()
    assert latest is not None
    assert status["simulation_results_available"] is True
