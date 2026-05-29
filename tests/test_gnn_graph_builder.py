from __future__ import annotations

import json

import pandas as pd

from neo_ange.gnn.graph_builder import OrbitalGraphBuilder


def _sample_scores(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "object_key": [f"obj-{i}" for i in range(n)],
            "pha": [i % 2 == 0 for i in range(n)],
            "e": [0.1 + i * 0.001 for i in range(n)],
            "a": [1.0 + i * 0.01 for i in range(n)],
            "q": [0.8 + i * 0.001 for i in range(n)],
            "i": [2.0 + i * 0.01 for i in range(n)],
            "moid": [0.01 + i * 0.001 for i in range(n)],
            "risk_score_0_100": [float(i) for i in range(n)],
        }
    )


def test_graph_builder_builds_and_exports_graph(tmp_path) -> None:
    risk_dir = tmp_path / "gold" / "risk_scores"
    risk_dir.mkdir(parents=True)
    _sample_scores(12).to_parquet(risk_dir / "risk_scores.parquet")
    builder = OrbitalGraphBuilder(gold_root=tmp_path / "gold", report_dir=tmp_path / "reports")

    graph = builder.build_graph_from_risk_scores(k=2, min_nodes=10)
    outputs = builder.export_graph(graph, tmp_path / "graph")

    assert graph.node_count() == 12
    assert graph.edge_count() > 0
    assert (tmp_path / "graph" / "nodes.parquet").exists()
    assert outputs["graph_summary"]["n_nodes"] == 12


def test_graph_builder_reports_insufficient_data(tmp_path) -> None:
    risk_dir = tmp_path / "gold" / "risk_scores"
    risk_dir.mkdir(parents=True)
    _sample_scores(3).to_parquet(risk_dir / "risk_scores.parquet")
    builder = OrbitalGraphBuilder(gold_root=tmp_path / "gold", report_dir=tmp_path / "reports")

    graph = builder.build_graph_from_risk_scores(k=2, min_nodes=10)
    summary = json.loads((tmp_path / "reports" / "graph_summary.json").read_text())

    assert graph.node_count() == 0
    assert summary["status"] == "insufficient_data"
