from __future__ import annotations

from neo_ange.ml.leakage import LeakageAuditor


def test_inspect_feature_leakage_categories() -> None:
    auditor = LeakageAuditor()

    result = auditor.inspect_feature_leakage(["pha", "h", "inverse_moid", "object_key", "e"])

    assert result["by_feature"]["pha"] == "direct_target_leakage"
    assert result["by_feature"]["h"] == "definition_related"
    assert result["by_feature"]["inverse_moid"] == "strong_proxy"
    assert result["by_feature"]["object_key"] == "identifier_or_metadata"
    assert result["by_feature"]["e"] == "safe_or_contextual"


def test_compare_feature_sets_and_generate_report(tmp_path) -> None:
    auditor = LeakageAuditor()
    results = [
        {
            "status": "success",
            "feature_set_name": "full_features",
            "model_name": "logistic_regression",
            "features": ["h", "moid", "e"],
            "metrics": {"pr_auc": 0.95, "f1": 0.9},
        },
        {
            "status": "success",
            "feature_set_name": "no_definition_features",
            "model_name": "logistic_regression",
            "features": ["e"],
            "metrics": {"pr_auc": 0.50, "f1": 0.4},
        },
        {
            "status": "success",
            "feature_set_name": "definition_features_only",
            "model_name": "logistic_regression",
            "features": ["h", "moid"],
            "metrics": {"pr_auc": 0.98, "f1": 0.95},
        },
    ]

    comparison = auditor.compare_feature_sets(results)
    report_path = auditor.generate_leakage_report(results, output_dir=tmp_path)

    assert comparison["status"] == "warning"
    assert "definition leakage" in comparison["conclusion"]
    assert report_path.exists()
    assert (tmp_path / "leakage_audit.json").exists()
