from __future__ import annotations

from neo_ange.domain.graph import OrbitalGraph, OrbitalGraphNode, OrbitalSimilarityEdge
from neo_ange.gnn.datasets import GNNDatasetBuilder, torch_geometric_available
from neo_ange.gnn.training import GNNTrainer


def test_gnn_training_skips_or_runs_with_synthetic_graph() -> None:
    graph = OrbitalGraph(
        nodes=[
            OrbitalGraphNode(0, "a", {"e": 0.1, "a": 1.0}, label=1),
            OrbitalGraphNode(1, "b", {"e": 0.2, "a": 1.1}, label=0),
            OrbitalGraphNode(2, "c", {"e": 0.3, "a": 1.2}, label=1),
            OrbitalGraphNode(3, "d", {"e": 0.4, "a": 1.3}, label=0),
            OrbitalGraphNode(4, "e", {"e": 0.5, "a": 1.4}, label=1),
            OrbitalGraphNode(5, "f", {"e": 0.6, "a": 1.5}, label=0),
        ],
        edges=[
            OrbitalSimilarityEdge(0, 1, 0.8, 0.2),
            OrbitalSimilarityEdge(1, 2, 0.7, 0.3),
            OrbitalSimilarityEdge(2, 3, 0.6, 0.4),
            OrbitalSimilarityEdge(3, 4, 0.6, 0.4),
            OrbitalSimilarityEdge(4, 5, 0.6, 0.4),
        ],
    )
    data = GNNDatasetBuilder().to_torch_geometric_data(graph)
    result = GNNTrainer().train_graphsage(data, epochs=2, patience=1)

    if torch_geometric_available():
        assert result["status"] in {"success", "insufficient_data"}
    else:
        assert result["status"] == "skipped_missing_dependency"


def test_gnn_training_single_class_is_handled() -> None:
    graph = OrbitalGraph(
        nodes=[
            OrbitalGraphNode(0, "a", {"e": 0.1}, label=1),
            OrbitalGraphNode(1, "b", {"e": 0.2}, label=1),
            OrbitalGraphNode(2, "c", {"e": 0.3}, label=1),
            OrbitalGraphNode(3, "d", {"e": 0.4}, label=1),
        ],
        edges=[OrbitalSimilarityEdge(0, 1, 0.8, 0.2)],
    )
    data = GNNDatasetBuilder().to_torch_geometric_data(graph)
    result = GNNTrainer().train_gcn(data, epochs=2, patience=1)

    assert result["status"] in {"skipped_missing_dependency", "insufficient_data"}
