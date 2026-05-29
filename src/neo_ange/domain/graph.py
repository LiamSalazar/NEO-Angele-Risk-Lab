"""Graph domain entities for orbital similarity experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import networkx as nx


@dataclass(slots=True)
class OrbitalGraphNode:
    """One asteroid node in an orbital similarity graph."""

    node_id: int
    object_key: str
    features: dict[str, Any] = field(default_factory=dict)
    label: int | float | str | None = None
    risk_score_0_100: float | None = None
    risk_category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)


@dataclass(slots=True)
class OrbitalSimilarityEdge:
    """Undirected similarity edge between two asteroid nodes."""

    source: int
    target: int
    similarity: float
    distance: float
    edge_type: str = "knn_orbital_similarity"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)


@dataclass(slots=True)
class OrbitalGraph:
    """Orbital similarity graph with serializable nodes and edges."""

    nodes: list[OrbitalGraphNode] = field(default_factory=list)
    edges: list[OrbitalSimilarityEdge] = field(default_factory=list)
    graph_version: str = "orbital_similarity_graph_v1"

    def node_count(self) -> int:
        """Return the number of graph nodes."""
        return len(self.nodes)

    def edge_count(self) -> int:
        """Return the number of graph edges."""
        return len(self.edges)

    def density(self) -> float:
        """Return undirected graph density."""
        n_nodes = self.node_count()
        if n_nodes < 2:
            return 0.0
        max_edges = n_nodes * (n_nodes - 1) / 2
        return float(self.edge_count() / max_edges) if max_edges else 0.0

    def to_networkx(self) -> nx.Graph:
        """Build a NetworkX graph from domain nodes and edges."""
        graph = nx.Graph(graph_version=self.graph_version)
        for node in self.nodes:
            payload = node.to_dict()
            node_id = payload.pop("node_id")
            graph.add_node(node_id, **payload)
        for edge in self.edges:
            graph.add_edge(
                edge.source,
                edge.target,
                similarity=edge.similarity,
                distance=edge.distance,
                edge_type=edge.edge_type,
            )
        return graph

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "graph_version": self.graph_version,
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "density": self.density(),
        }


@dataclass(slots=True)
class GNNExperimentResult:
    """Serializable result envelope for one graph-learning experiment."""

    experiment_id: str
    model_name: str
    target: str
    feature_set: str
    n_nodes: int
    n_edges: int
    metrics: dict[str, Any] = field(default_factory=dict)
    baseline_metrics: dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)

    def summary(self) -> dict[str, Any]:
        """Return compact fields for CLI/API summaries."""
        return {
            "experiment_id": self.experiment_id,
            "model_name": self.model_name,
            "target": self.target,
            "feature_set": self.feature_set,
            "n_nodes": self.n_nodes,
            "n_edges": self.n_edges,
            "status": self.status,
            "metrics": self.metrics,
            "baseline_metrics": self.baseline_metrics,
            "warnings": self.warnings,
        }
