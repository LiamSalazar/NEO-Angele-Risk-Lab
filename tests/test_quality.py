from __future__ import annotations

import json

from neo_ange.etl.quality import DataQualityChecker


def test_quality_checks_return_json_serializable_results(spark) -> None:
    df = spark.createDataFrame(
        [
            {
                "object_key": "1",
                "neo": True,
                "pha": False,
                "sentry_flag": True,
                "feature_completeness_ratio": 0.8,
                "relative_velocity_score": 0.2,
                "observation_quality_score": 0.7,
                "uncertainty_proxy_score": 0.1,
                "size_proxy_score": 0.6,
                "proximity_proxy_score": 0.9,
                "sentry_presence_score": 1.0,
                "diameter": 0.3,
                "moid": 0.1,
                "built_at_utc": "2026-05-28T00:00:00Z",
                "source_availability_json": "{}",
            }
        ]
    )
    checker = DataQualityChecker()

    assert checker.check_required_columns(df, ["object_key"])["status"] == "pass"
    assert checker.check_non_empty(df, "sample")["status"] == "pass"
    assert checker.check_null_ratio(df, ["diameter"])["ratios"]["diameter"] == 0
    assert checker.check_duplicate_keys(df, ["object_key"])["status"] == "pass"
    assert checker.check_numeric_ranges(df, {"diameter": (0.0, None)})["status"] == "pass"

    report = checker.run_gold_quality_checks(df)
    assert report["dataset"] == "neo_risk_features"
    json.dumps(report)
