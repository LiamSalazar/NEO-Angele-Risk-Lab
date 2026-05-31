from __future__ import annotations

import pandas as pd
from fastapi.testclient import TestClient

from neo_ange.api.dependencies import get_data_paths, get_orbital_simulation_service
from neo_ange.api.main import app
from neo_ange.orbital_simulation.service import OrbitalSimulationService
from neo_ange.risk.scoring import RiskScorer


def _write_risk_scores(tmp_path) -> None:
    risk_dir = tmp_path / "gold" / "risk_scores"
    risk_dir.mkdir(parents=True)
    rows = []
    for index in range(48):
        is_pha = index % 3 == 0
        rows.append(
            {
                "object_key": f"A-{index:03d}",
                "des": f"2026 Q{index}",
                "a": 1.0 + (index % 7) * 0.03,
                "e": 0.08 + (index % 5) * 0.025,
                "i": 1.0 + (index % 9),
                "om": float((index * 13) % 360),
                "w": float((index * 17) % 360),
                "ma": float((index * 19) % 360),
                "diameter": 1.0 if is_pha else 0.2,
                "h": 18.5 if is_pha else 23.5,
                "moid": 0.02 if is_pha else 0.18,
                "min_close_approach_dist": 0.01 if is_pha else 0.12,
                "sentry_flag": index == 0,
                "pha": is_pha,
                "condition_code": index % 8,
                "rms": 0.2 + (index % 4) * 0.1,
                "arc_length": 50 + index * 4,
                "n_obs_used": 20 + index,
            }
        )
    scored = RiskScorer().score_dataframe(pd.DataFrame(rows))
    scored.to_parquet(risk_dir / "risk_scores.parquet", index=False)


def _paths(tmp_path) -> dict:
    return {
        "data_dir": tmp_path / "data",
        "bronze_dir": tmp_path / "data" / "bronze",
        "silver_dir": tmp_path / "data" / "silver",
        "gold_dir": tmp_path / "gold",
        "gold_features_dir": tmp_path / "gold" / "neo_risk_features",
        "risk_scores_dir": tmp_path / "gold" / "risk_scores",
        "simulation_results_dir": tmp_path / "gold" / "simulation_results",
        "orbital_simulation_dir": tmp_path / "gold" / "orbital_simulation",
        "gnn_graph_dir": tmp_path / "gold" / "gnn_graph",
        "reports_dir": tmp_path / "reports",
        "manifest_dir": tmp_path / "reports" / "manifests",
    }


def test_new_api_surfaces_return_structured_payloads(tmp_path) -> None:
    _write_risk_scores(tmp_path)
    service = OrbitalSimulationService(
        gold_root=tmp_path / "gold",
        output_dir=tmp_path / "gold" / "orbital_simulation",
        report_dir=tmp_path / "reports" / "orbital_simulation",
        manifest_dir=tmp_path / "reports" / "manifests",
    )
    service.simulate_batch(limit=1, n_clones=8, horizon_days=90, time_step_days=30)

    app.dependency_overrides[get_data_paths] = lambda: _paths(tmp_path)
    app.dependency_overrides[get_orbital_simulation_service] = lambda: service
    try:
        client = TestClient(app)
        orbital_status = client.get("/orbital-simulation/status")
        findings = client.get("/findings/summary")
        model_evidence = client.get("/model-evidence/summary")
    finally:
        app.dependency_overrides.clear()

    assert orbital_status.status_code == 200
    assert orbital_status.json()["details"]["row_count"] == 1
    assert findings.status_code == 200
    assert "findings" in findings.json()["details"]
    assert model_evidence.status_code == 200
    assert "best_defensible_model" in model_evidence.json()["details"]
