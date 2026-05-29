from __future__ import annotations

from neo_ange.domain.graph import OrbitalGraph, OrbitalGraphNode, OrbitalSimilarityEdge
from neo_ange.gnn.datasets import GNNDatasetBuilder


def test_gnn_dataset_builder_arrays_and_masks() -> None:
    graph = OrbitalGraph(
        nodes=[
            OrbitalGraphNode(0, "a", {"e": 0.1, "a": 1.0}, label=1),
            OrbitalGraphNode(1, "b", {"e": 0.2, "a": 1.1}, label=0),
            OrbitalGraphNode(2, "c", {"e": 0.3, "a": 1.2}, label=1),
            OrbitalGraphNode(3, "d", {"e": 0.4, "a": 1.3}, label=0),
        ],
        edges=[OrbitalSimilarityEdge(0, 1, 0.8, 0.2), OrbitalSimilarityEdge(2, 3, 0.7, 0.3)],
    )
    builder = GNNDatasetBuilder()

    x, features = builder.build_node_feature_matrix(graph)
    edge_index = builder.build_edge_index(graph)
    y = builder.build_labels(graph)
    masks = builder.split_masks(y)
    data = builder.to_torch_geometric_data(graph)

    assert x.shape == (4, 2)
    assert features == ["e", "a"]
    assert edge_index.shape == (2, 4)
    assert y.tolist() == [1, 0, 1, 0]
    assert masks["train_mask"].shape == (4,)
    assert data is not None
