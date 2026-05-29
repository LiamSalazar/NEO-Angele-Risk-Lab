from __future__ import annotations

import pandas as pd

from neo_ange.expansion.readiness import DatasetReadinessReporter, readiness_status


def test_readiness_status_thresholds() -> None:
    assert readiness_status(0) == "not_ready"
    assert readiness_status(100) == "minimal"
    assert readiness_status(300) == "usable"
    assert readiness_status(1000) == "strong"


def test_dataset_readiness_report_handles_counts_and_empty_data(tmp_path) -> None:
    gold = tmp_path / "data" / "gold" / "neo_risk_features"
    risk = tmp_path / "data" / "gold" / "risk_scores"
    gold.mkdir(parents=True)
    risk.mkdir(parents=True)
    pd.DataFrame(
        {
            "object_key": ["a", "b"],
            "pha": [True, False],
            "neo": [True, True],
            "sentry_flag": [True, None],
            "min_close_approach_dist": [0.01, None],
        }
    ).to_parquet(gold / "part.parquet")
    pd.DataFrame({"object_key": ["a"], "risk_score_0_100": [50], "pha": [True]}).to_parquet(
        risk / "risk_scores.parquet"
    )

    report = DatasetReadinessReporter(
        data_dir=tmp_path / "data",
        silver_root=tmp_path / "data" / "silver",
        gold_root=tmp_path / "data" / "gold",
        report_dir=tmp_path / "reports",
    ).build_report(write=True)

    assert report["counts"]["gold_neo_risk_features_count"] == 2
    assert report["pha_distribution"]["true"] == 1
    assert report["sentry_coverage"]["covered_rows"] == 1
    assert (tmp_path / "reports" / "dataset_readiness.json").exists()
