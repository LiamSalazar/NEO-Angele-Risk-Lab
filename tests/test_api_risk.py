from __future__ import annotations

from fastapi.testclient import TestClient

from neo_ange.api.dependencies import get_risk_pipeline
from neo_ange.api.main import app
from neo_ange.pipelines.risk import RiskPipeline


def test_risk_status_responds(tmp_path) -> None:
    pipeline = RiskPipeline(
        gold_root=tmp_path / "gold",
        report_dir=tmp_path / "reports" / "risk",
        manifest_dir=tmp_path / "reports" / "manifests",
    )
    app.dependency_overrides[get_risk_pipeline] = lambda: pipeline
    try:
        response = TestClient(app).get("/risk/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_risk_explain_handles_missing_object(tmp_path) -> None:
    pipeline = RiskPipeline(
        gold_root=tmp_path / "gold",
        report_dir=tmp_path / "reports" / "risk",
        manifest_dir=tmp_path / "reports" / "manifests",
    )
    app.dependency_overrides[get_risk_pipeline] = lambda: pipeline
    try:
        response = TestClient(app).get("/risk/explain/does-not-exist")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "missing_data"


def test_risk_build_can_use_mocked_pipeline() -> None:
    class FakePipeline:
        def build_scores(self):
            return {"status": "success", "outputs": {}, "warnings": [], "errors": []}

    app.dependency_overrides[get_risk_pipeline] = lambda: FakePipeline()
    try:
        response = TestClient(app).post("/risk/build")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "success"
