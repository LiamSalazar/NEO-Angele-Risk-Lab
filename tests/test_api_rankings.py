from __future__ import annotations

import pandas as pd
from fastapi.testclient import TestClient

from neo_ange.api.dependencies import get_risk_pipeline
from neo_ange.api.main import app
from neo_ange.pipelines.risk import RiskPipeline
from neo_ange.risk.scoring import RiskScorer


def test_rankings_top_and_summary_with_scores(tmp_path) -> None:
    pipeline = _pipeline_with_scores(tmp_path)
    app.dependency_overrides[get_risk_pipeline] = lambda: pipeline
    try:
        client = TestClient(app)
        top = client.get("/rankings/top?limit=1")
        summary = client.get("/rankings/summary")
    finally:
        app.dependency_overrides.clear()

    assert top.status_code == 200
    assert top.json()["objects"]
    assert summary.status_code == 200
    assert summary.json()["details"]["n_objects"] == 1


def test_rankings_handle_missing_scores(tmp_path) -> None:
    pipeline = RiskPipeline(
        gold_root=tmp_path / "gold",
        report_dir=tmp_path / "reports" / "risk",
        manifest_dir=tmp_path / "reports" / "manifests",
    )
    app.dependency_overrides[get_risk_pipeline] = lambda: pipeline
    try:
        response = TestClient(app).get("/rankings/top")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "missing_data"


def _pipeline_with_scores(tmp_path) -> RiskPipeline:
    scores_dir = tmp_path / "gold" / "risk_scores"
    scores_dir.mkdir(parents=True)
    scored = RiskScorer().score_dataframe(
        pd.DataFrame(
            [
                {
                    "object_key": "A",
                    "diameter": 1.0,
                    "h": 18.5,
                    "moid": 0.02,
                    "sentry_flag": True,
                    "sentry_ip": 1e-5,
                }
            ]
        )
    )
    scored.to_parquet(scores_dir / "risk_scores.parquet", index=False)
    return RiskPipeline(
        gold_root=tmp_path / "gold",
        report_dir=tmp_path / "reports" / "risk",
        manifest_dir=tmp_path / "reports" / "manifests",
    )
