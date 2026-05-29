from __future__ import annotations

import pandas as pd

from neo_ange.pipelines.risk import RiskPipeline


def test_risk_pipeline_builds_outputs_and_explains(tmp_path) -> None:
    gold = tmp_path / "gold" / "neo_risk_features"
    gold.mkdir(parents=True)
    _features().to_parquet(gold / "part.parquet", index=False)
    pipeline = RiskPipeline(
        gold_root=tmp_path / "gold",
        report_dir=tmp_path / "reports" / "risk",
        manifest_dir=tmp_path / "reports" / "manifests",
    )

    result = pipeline.build_scores()
    top = pipeline.top(limit=1)
    explanation = pipeline.explain("A")
    status = pipeline.status()

    assert result["status"] in {"success", "partial_success"}
    assert (tmp_path / "gold" / "risk_scores" / "risk_scores.parquet").exists()
    assert (tmp_path / "reports" / "risk" / "risk_scores_summary.json").exists()
    assert top[0]["object_key"] in {"A", "B"}
    assert explanation["status"] == "success"
    assert status["risk_scores_available"] is True


def _features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "object_key": "A",
                "des": "2026 AA",
                "diameter": 1.0,
                "h": 18.5,
                "moid": 0.02,
                "moid_ld": 8.0,
                "q": 0.9,
                "e": 0.5,
                "i": 8.0,
                "min_close_approach_dist": 0.01,
                "max_close_approach_v_rel": 22.0,
                "close_approach_count": 5,
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
                "des": "2026 BB",
                "diameter": 0.1,
                "h": 24.0,
                "moid": 0.3,
                "moid_ld": 110,
                "sentry_flag": False,
                "condition_code": 1,
                "arc_length": 1000,
                "n_obs_used": 250,
                "feature_completeness_ratio": 0.7,
            },
        ]
    )
