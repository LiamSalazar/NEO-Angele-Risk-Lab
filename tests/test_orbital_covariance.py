from __future__ import annotations

import numpy as np

from neo_ange.orbital_simulation.covariance import (
    sample_orbital_clones,
    validate_covariance_matrix,
    vector_to_symmetric_matrix,
)


def test_vector_to_symmetric_matrix() -> None:
    matrix = vector_to_symmetric_matrix([1.0, 0.1, 2.0, 0.2, 0.3, 3.0])

    assert matrix is not None
    assert matrix.shape == (3, 3)
    assert np.allclose(matrix, matrix.T)


def test_validate_covariance_matrix_rejects_negative_diagonal() -> None:
    result = validate_covariance_matrix(np.asarray([[1.0, 0.0], [0.0, -1.0]]))

    assert result["valid"] is False


def test_sample_orbital_clones_from_covariance() -> None:
    elements = {"a": 1.1, "e": 0.1, "i": 2.0, "om": 40.0, "w": 20.0, "ma": 10.0, "n": 0.9}
    covariance = np.diag([1e-6, 1e-6, 1e-4, 1e-4, 1e-4, 1e-4, 1e-6])

    clones, diagnostics = sample_orbital_clones(
        elements,
        {"available": True, "matrix": covariance, "labels": ["a", "e", "i", "om", "w", "ma", "n"]},
        n_clones=20,
        rng=np.random.default_rng(42),
    )

    assert diagnostics["status"] == "success"
    assert diagnostics["valid_clone_count"] == 20
    assert set(clones) == {"a", "e", "i", "om", "w", "ma", "n"}
