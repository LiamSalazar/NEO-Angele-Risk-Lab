"""Orbital similarity calculations for graph construction."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from neo_ange.domain.graph import OrbitalSimilarityEdge
from neo_ange.gnn.schemas import FORBIDDEN_GRAPH_FEATURES, SIMILARITY_FEATURES


class OrbitalSimilarityCalculator:
    """Compute kNN and radius edges from leakage-aware orbital features."""

    def __init__(self, default_features: list[str] | None = None) -> None:
        self.default_features = default_features or list(SIMILARITY_FEATURES)
        self.last_feature_names: list[str] = []

    def prepare_similarity_matrix(
        self,
        df: pd.DataFrame,
        features: list[str] | None = None,
    ) -> np.ndarray:
        """Return an imputed and scaled numeric matrix for similarity search."""
        normalized = self.normalize_features(df, features=features)
        if normalized.empty:
            return np.empty((len(df), 0), dtype=float)
        imputer = SimpleImputer(strategy="median")
        matrix = imputer.fit_transform(normalized)
        matrix = np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)
        scaler = StandardScaler()
        return scaler.fit_transform(matrix)

    def compute_knn_edges(
        self,
        df: pd.DataFrame,
        k: int = 10,
        metric: str = "euclidean",
    ) -> list[OrbitalSimilarityEdge]:
        """Compute undirected k-nearest-neighbor similarity edges."""
        if df.empty or len(df) < 2:
            return []
        matrix = self.prepare_similarity_matrix(df, self.default_features)
        if matrix.shape[1] == 0:
            return []
        n_neighbors = min(max(k, 1) + 1, len(df))
        model = NearestNeighbors(n_neighbors=n_neighbors, metric=metric)
        model.fit(matrix)
        distances, indices = model.kneighbors(matrix)
        edges: dict[tuple[int, int], OrbitalSimilarityEdge] = {}
        for source, (row_distances, row_indices) in enumerate(
            zip(distances, indices, strict=False)
        ):
            for distance, target in zip(row_distances, row_indices, strict=False):
                target = int(target)
                if source == target:
                    continue
                key = tuple(sorted((source, target)))
                distance_value = float(distance)
                similarity = float(1.0 / (1.0 + max(distance_value, 0.0)))
                existing = edges.get(key)
                if existing is None or distance_value < existing.distance:
                    edges[key] = OrbitalSimilarityEdge(
                        source=key[0],
                        target=key[1],
                        similarity=similarity,
                        distance=distance_value,
                        edge_type="knn_orbital_similarity",
                    )
        return list(edges.values())

    def compute_radius_edges(
        self,
        df: pd.DataFrame,
        radius: float,
    ) -> list[OrbitalSimilarityEdge]:
        """Compute undirected edges for neighbors within a scaled-feature radius."""
        if df.empty or len(df) < 2:
            return []
        matrix = self.prepare_similarity_matrix(df, self.default_features)
        if matrix.shape[1] == 0:
            return []
        model = NearestNeighbors(radius=max(radius, 0.0), metric="euclidean")
        model.fit(matrix)
        distances, indices = model.radius_neighbors(matrix)
        edges: dict[tuple[int, int], OrbitalSimilarityEdge] = {}
        for source, (row_distances, row_indices) in enumerate(
            zip(distances, indices, strict=False)
        ):
            for distance, target in zip(row_distances, row_indices, strict=False):
                target = int(target)
                if source == target:
                    continue
                key = tuple(sorted((source, target)))
                distance_value = float(distance)
                similarity = float(1.0 / (1.0 + max(distance_value, 0.0)))
                edges[key] = OrbitalSimilarityEdge(
                    source=key[0],
                    target=key[1],
                    similarity=similarity,
                    distance=distance_value,
                    edge_type="radius_orbital_similarity",
                )
        return list(edges.values())

    def normalize_features(
        self,
        df: pd.DataFrame,
        features: list[str] | None = None,
    ) -> pd.DataFrame:
        """Select safe numeric features, coerce types, and impute missing medians."""
        selected = _safe_features(df, features or self.default_features)
        self.last_feature_names = selected
        if not selected:
            return pd.DataFrame(index=df.index)
        numeric = df[selected].apply(pd.to_numeric, errors="coerce")
        if numeric.empty:
            return numeric
        medians = numeric.median(numeric_only=True)
        numeric = numeric.fillna(medians).fillna(0.0)
        return numeric


def _safe_features(df: pd.DataFrame, requested: list[str]) -> list[str]:
    safe: list[str] = []
    for feature in requested:
        if feature in FORBIDDEN_GRAPH_FEATURES:
            continue
        if feature not in df.columns:
            continue
        if not _is_numeric_like(df[feature]):
            continue
        safe.append(feature)
    return safe


def _is_numeric_like(series: pd.Series) -> bool:
    if pd.api.types.is_bool_dtype(series) or pd.api.types.is_numeric_dtype(series):
        return True
    converted = pd.to_numeric(series, errors="coerce")
    return bool(converted.notna().any())
