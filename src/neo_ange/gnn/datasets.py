"""Dataset builders for graph experiments with optional torch-geometric support."""

from __future__ import annotations

import importlib.util
from typing import Any

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from neo_ange.domain.graph import OrbitalGraph
from neo_ange.gnn.schemas import GRAPH_NODE_FEATURES


class GNNDatasetBuilder:
    """Convert OrbitalGraph domain objects into arrays or PyG Data objects."""

    def build_node_feature_matrix(self, graph: OrbitalGraph) -> tuple[np.ndarray, list[str]]:
        """Build a dense node-feature matrix and feature-name list."""
        if not graph.nodes:
            return np.empty((0, 0), dtype=np.float32), []
        feature_names = _feature_names(graph)
        matrix = np.zeros((graph.node_count(), len(feature_names)), dtype=np.float32)
        for row_index, node in enumerate(graph.nodes):
            for col_index, feature in enumerate(feature_names):
                matrix[row_index, col_index] = _float_or_zero(node.features.get(feature))
        if matrix.size:
            matrix = np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)
            matrix = StandardScaler().fit_transform(matrix).astype(np.float32)
        return matrix, feature_names

    def build_edge_index(self, graph: OrbitalGraph) -> np.ndarray:
        """Build a directed edge_index array with both directions for each edge."""
        edges: list[tuple[int, int]] = []
        for edge in graph.edges:
            edges.append((int(edge.source), int(edge.target)))
            edges.append((int(edge.target), int(edge.source)))
        if not edges:
            return np.empty((2, 0), dtype=np.int64)
        return np.asarray(edges, dtype=np.int64).T

    def build_labels(self, graph: OrbitalGraph, target: str = "pha") -> np.ndarray:
        """Build numeric labels from graph node labels."""
        labels = [_label_to_int(node.label) for node in graph.nodes]
        return np.asarray(labels, dtype=np.int64)

    def split_masks(
        self,
        y: np.ndarray,
        train_ratio: float = 0.6,
        val_ratio: float = 0.2,
        random_state: int = 42,
    ) -> dict[str, np.ndarray]:
        """Create train/validation/test boolean masks, stratifying when possible."""
        n = len(y)
        train_mask = np.zeros(n, dtype=bool)
        val_mask = np.zeros(n, dtype=bool)
        test_mask = np.zeros(n, dtype=bool)
        labeled = np.where(y >= 0)[0]
        if len(labeled) == 0:
            return {"train_mask": train_mask, "val_mask": val_mask, "test_mask": test_mask}
        if len(labeled) < 3:
            train_mask[labeled[:1]] = True
            if len(labeled) > 1:
                test_mask[labeled[1:]] = True
            return {"train_mask": train_mask, "val_mask": val_mask, "test_mask": test_mask}

        train_ratio = min(max(train_ratio, 0.0), 1.0)
        val_ratio = min(max(val_ratio, 0.0), 1.0 - train_ratio)
        test_ratio = max(1.0 - train_ratio - val_ratio, 0.0)
        labels = y[labeled]
        stratify = labels if _can_stratify(labels) else None
        train_idx, remainder_idx = train_test_split(
            labeled,
            train_size=train_ratio,
            random_state=random_state,
            stratify=stratify,
        )
        if len(remainder_idx) == 0:
            train_mask[train_idx] = True
            return {"train_mask": train_mask, "val_mask": val_mask, "test_mask": test_mask}
        remainder_labels = y[remainder_idx]
        stratify_remainder = remainder_labels if _can_stratify(remainder_labels) else None
        val_share = val_ratio / (val_ratio + test_ratio) if (val_ratio + test_ratio) else 0.0
        if val_share <= 0:
            val_idx = np.asarray([], dtype=int)
            test_idx = remainder_idx
        elif val_share >= 1:
            val_idx = remainder_idx
            test_idx = np.asarray([], dtype=int)
        else:
            val_idx, test_idx = train_test_split(
                remainder_idx,
                train_size=val_share,
                random_state=random_state,
                stratify=stratify_remainder,
            )
        train_mask[train_idx] = True
        val_mask[val_idx] = True
        test_mask[test_idx] = True
        return {"train_mask": train_mask, "val_mask": val_mask, "test_mask": test_mask}

    def to_torch_geometric_data(
        self,
        graph: OrbitalGraph,
        target: str = "pha",
        random_state: int = 42,
    ) -> Any:
        """Return a torch-geometric Data object when dependencies are available."""
        if not torch_geometric_available():
            x, feature_names = self.build_node_feature_matrix(graph)
            edge_index = self.build_edge_index(graph)
            y = self.build_labels(graph, target=target)
            masks = self.split_masks(y, random_state=random_state)
            return {
                "status": "skipped_missing_dependency",
                "reason": "torch-geometric is not installed.",
                "x": x,
                "edge_index": edge_index,
                "y": y,
                "masks": masks,
                "feature_names": feature_names,
            }
        import torch
        from torch_geometric.data import Data

        x, feature_names = self.build_node_feature_matrix(graph)
        edge_index = self.build_edge_index(graph)
        y = self.build_labels(graph, target=target)
        masks = self.split_masks(y, random_state=random_state)
        data = Data(
            x=torch.tensor(x, dtype=torch.float32),
            edge_index=torch.tensor(edge_index, dtype=torch.long),
            y=torch.tensor(y, dtype=torch.long),
            train_mask=torch.tensor(masks["train_mask"], dtype=torch.bool),
            val_mask=torch.tensor(masks["val_mask"], dtype=torch.bool),
            test_mask=torch.tensor(masks["test_mask"], dtype=torch.bool),
        )
        data.feature_names = feature_names
        data.status = "success"
        return data


def torch_geometric_available() -> bool:
    """Return whether torch and torch-geometric can be imported."""
    return (
        importlib.util.find_spec("torch") is not None
        and importlib.util.find_spec("torch_geometric") is not None
    )


def _feature_names(graph: OrbitalGraph) -> list[str]:
    available = {feature for node in graph.nodes for feature in node.features}
    ordered = [feature for feature in GRAPH_NODE_FEATURES if feature in available]
    extras = sorted(available - set(ordered))
    return [*ordered, *extras]


def _float_or_zero(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return float(value)
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not np.isfinite(numeric):
        return 0.0
    return float(numeric)


def _label_to_int(value: Any) -> int:
    if value is None:
        return -1
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, float):
        if not np.isfinite(value):
            return -1
        return int(value)
    normalized = str(value).strip().lower()
    if normalized in {"true", "t", "1", "yes", "y"}:
        return 1
    if normalized in {"false", "f", "0", "no", "n"}:
        return 0
    return -1


def _can_stratify(labels: np.ndarray) -> bool:
    if len(labels) < 4:
        return False
    unique, counts = np.unique(labels, return_counts=True)
    return len(unique) > 1 and bool(np.all(counts >= 2))
