from __future__ import annotations

import numpy as np
import pandas as pd

from neo_ange.gnn.similarity import OrbitalSimilarityCalculator


def test_similarity_normalizes_and_excludes_forbidden_features() -> None:
    df = pd.DataFrame(
        {
            "object_key": ["a", "b", "c"],
            "pha": [True, False, True],
            "e": [0.1, np.nan, 0.3],
            "a": [1.0, 1.2, 1.4],
            "q": [0.8, 0.9, None],
            "i": [2.0, 3.0, 4.0],
        }
    )
    calculator = OrbitalSimilarityCalculator()

    normalized = calculator.normalize_features(df, ["object_key", "pha", "e", "a", "q", "i"])
    edges = calculator.compute_knn_edges(df, k=1)

    assert "object_key" not in calculator.last_feature_names
    assert "pha" not in calculator.last_feature_names
    assert not normalized.isna().any().any()
    assert edges
