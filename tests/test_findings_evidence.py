from __future__ import annotations

import pandas as pd

from neo_ange.evidence.disagreement import build_disagreements
from neo_ange.evidence.model_cards import build_model_card, leakage_risk_for_feature_set
from neo_ange.evidence.predictions import confidence_bucket
from neo_ange.evidence.reporting import ModelEvidenceBuilder
from neo_ange.findings.reporting import (
    FindingsBuilder,
    build_orbital_findings,
    build_risk_findings,
)
from neo_ange.risk.scoring import RiskScorer


def _risk_scores() -> pd.DataFrame:
    scored = RiskScorer().score_dataframe(
        pd.DataFrame(
            [
                {
                    "object_key": "A-001",
                    "diameter": 1.2,
                    "h": 18.2,
                    "moid": 0.018,
                    "min_close_approach_dist": 0.01,
                    "sentry_flag": True,
                    "pha": True,
                    "condition_code": 5,
                },
                {
                    "object_key": "B-001",
                    "diameter": 0.2,
                    "h": 23.1,
                    "moid": 0.15,
                    "sentry_flag": False,
                    "pha": False,
                    "condition_code": 1,
                },
            ]
        )
    )
    return scored


def test_findings_builder_summarizes_risk_and_orbital_rows(tmp_path) -> None:
    risk_dir = tmp_path / "gold" / "risk_scores"
    orbital_dir = tmp_path / "gold" / "orbital_simulation"
    risk_dir.mkdir(parents=True)
    orbital_dir.mkdir(parents=True)
    _risk_scores().to_parquet(risk_dir / "risk_scores.parquet", index=False)
    pd.DataFrame(
        [
            {
                "object_key": "A-001",
                "scenario_category": "variable",
                "dispersion_index": 0.7,
                "simulated_min_distance_p05_au": 0.02,
            }
        ]
    ).to_parquet(orbital_dir / "orbital_monte_carlo_results.parquet", index=False)

    payload = FindingsBuilder(
        gold_root=tmp_path / "gold",
        reports_root=tmp_path / "reports",
    ).build_all()

    assert payload["status"] == "success"
    assert payload["summary"]["risk_rows"] == 2
    assert payload["summary"]["orbital_simulation_rows"] == 1
    assert payload["summary"]["finding_count"] >= 1
    assert (tmp_path / "reports" / "findings" / "findings_summary.json").exists()


def test_findings_helpers_return_conclusions() -> None:
    risk_findings = build_risk_findings(_risk_scores())
    orbital_findings = build_orbital_findings(
        pd.DataFrame(
            [
                {
                    "object_key": "A-001",
                    "scenario_category": "needs_review",
                    "dispersion_index": 1.4,
                    "simulated_min_distance_p05_au": 0.01,
                }
            ]
        )
    )

    assert any("priority" in item["title"].lower() for item in risk_findings)
    assert any(item["source_module"] == "orbital_simulation" for item in orbital_findings)


def test_model_evidence_marks_leakage_and_confidence() -> None:
    card = build_model_card(
        model_name="random_forest",
        model_family="tabular",
        feature_set="graph_node_features",
        target="pha",
        metrics={"pr_auc": 0.9, "recall": 0.8},
    )

    assert leakage_risk_for_feature_set("graph_node_features") == "high"
    assert card["leakage_risk"] == "high"
    assert confidence_bucket(0.9) == "high"
    assert confidence_bucket(0.52) == "low"


def test_model_disagreements_capture_split_predictions() -> None:
    disagreements = build_disagreements(
        pd.DataFrame(
            [
                {
                    "object_key": "A-001",
                    "actual_label": 1,
                    "predicted_label": 1,
                    "confidence_bucket": "high",
                    "correct": True,
                    "risk_score_0_100": 50,
                    "risk_category": "elevated",
                },
                {
                    "object_key": "A-001",
                    "actual_label": 1,
                    "predicted_label": 0,
                    "confidence_bucket": "high",
                    "correct": False,
                    "risk_score_0_100": 50,
                    "risk_category": "elevated",
                },
            ]
        )
    )

    assert len(disagreements) == 1
    assert disagreements.iloc[0]["reason"] == "model_family_disagreement"


def test_model_evidence_separates_eval_and_full_inference(tmp_path) -> None:
    risk_dir = tmp_path / "gold" / "risk_scores"
    risk_dir.mkdir(parents=True)
    rows = []
    for index in range(48):
        is_pha = index % 3 == 0
        rows.append(
            {
                "object_key": f"A-{index:03d}",
                "des": f"2026 Q{index}",
                "pha": is_pha,
                "h": 18.5 if is_pha else 23.5,
                "diameter": 1.0 if is_pha else 0.2,
                "moid": 0.02 if is_pha else 0.18,
                "e": 0.08 + (index % 5) * 0.025,
                "a": 1.0 + (index % 7) * 0.03,
                "q": 0.9 + (index % 6) * 0.02,
                "i": 1.0 + (index % 9),
                "om": float((index * 13) % 360),
                "w": float((index * 17) % 360),
                "ma": float((index * 19) % 360),
                "n": 0.2 + (index % 8) * 0.01,
                "per": 300 + index,
                "ad": 1.2 + (index % 10) * 0.02,
                "risk_score_0_100": 70.0 if is_pha else 20.0,
                "risk_category": "elevated" if is_pha else "low",
            }
        )
    pd.DataFrame(rows).to_parquet(risk_dir / "risk_scores.parquet", index=False)

    result = ModelEvidenceBuilder(
        gold_root=tmp_path / "gold",
        reports_root=tmp_path / "reports",
    ).build(write=True)

    eval_predictions = pd.read_parquet(
        tmp_path / "reports" / "model_evidence" / "model_predictions_eval.parquet"
    )
    full_predictions = pd.read_parquet(
        tmp_path / "reports" / "model_evidence" / "model_predictions_full.parquet"
    )

    assert result["summary"]["unique_eval_object_keys"] < 48
    assert result["summary"]["unique_full_object_keys"] == 48
    assert result["summary"]["coverage_ratio"] == 1.0
    assert result["summary"]["full_inference_available"] is True
    assert eval_predictions["object_key"].nunique() < full_predictions["object_key"].nunique()
    assert full_predictions["object_key"].nunique() == 48
