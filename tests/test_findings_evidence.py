from __future__ import annotations

import pandas as pd

from neo_ange.evidence.disagreement import build_disagreements
from neo_ange.evidence.model_cards import build_model_card, leakage_risk_for_feature_set
from neo_ange.evidence.predictions import confidence_bucket
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
