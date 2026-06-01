"""Covariance parsing and orbital clone sampling utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ORBITAL_COVARIANCE_VERSION = "orbital-covariance-v0.2.0"

DEFAULT_COVARIANCE_LABELS = ["e", "a", "q", "i", "om", "w", "ma", "n"]
PROPAGATION_LABELS = ["a", "e", "i", "om", "w", "ma", "n"]
ANGLE_LABELS = {"i", "om", "w", "ma"}


def parse_covariance_payload(row: dict[str, Any]) -> dict[str, Any]:
    """Parse covariance payloads from a gold row or artifact path."""
    raw = row.get("covariance_matrix_json") or row.get("covariance_json")
    if raw is None and row.get("covariance_matrix_path"):
        path = Path(str(row["covariance_matrix_path"]))
        if path.exists():
            raw = path.read_text(encoding="utf-8")
    if raw is None or _is_missing(raw):
        return {
            "available": False,
            "matrix": None,
            "labels": [],
            "warnings": ["No SBDB covariance payload is available for this object."],
        }
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, json.JSONDecodeError) as exc:
        return {
            "available": False,
            "matrix": None,
            "labels": [],
            "warnings": [f"Covariance payload could not be parsed as JSON: {exc}."],
        }
    labels = _parse_labels(row.get("covariance_labels") or _payload_value(payload, "labels"))
    matrix_source = _payload_value(payload, "data") or _payload_value(payload, "matrix") or payload
    matrix = _matrix_from_payload(matrix_source)
    if matrix is None:
        vector = _payload_value(payload, "vec") or _payload_value(payload, "vector")
        matrix = vector_to_symmetric_matrix(vector) if vector is not None else None
    if matrix is None:
        return {
            "available": False,
            "matrix": None,
            "labels": labels,
            "warnings": ["Covariance payload did not contain a usable matrix or vector."],
        }
    if not labels:
        labels = DEFAULT_COVARIANCE_LABELS[: matrix.shape[0]]
    return {
        "available": True,
        "matrix": matrix,
        "labels": labels,
        "epoch": row.get("covariance_epoch") or _payload_value(payload, "epoch"),
        "form": row.get("covariance_form") or _payload_value(payload, "form"),
        "units": row.get("covariance_units") or _payload_value(payload, "units"),
        "warnings": [],
    }


def vector_to_symmetric_matrix(vector: Any) -> np.ndarray | None:
    """Convert a lower-triangular covariance vector to a symmetric matrix."""
    try:
        values = np.asarray(vector, dtype=float).ravel()
    except (TypeError, ValueError):
        return None
    if values.size == 0:
        return None
    dimension = int((np.sqrt(8 * values.size + 1) - 1) / 2)
    if dimension * (dimension + 1) // 2 != values.size:
        return None
    matrix = np.zeros((dimension, dimension), dtype=float)
    index = 0
    for row in range(dimension):
        for column in range(row + 1):
            matrix[row, column] = values[index]
            matrix[column, row] = values[index]
            index += 1
    return matrix


def sqrt_cov_to_covariance(matrix: Any) -> np.ndarray | None:
    """Convert a square-root covariance factor to covariance form."""
    try:
        factor = np.asarray(matrix, dtype=float)
    except (TypeError, ValueError):
        return None
    if factor.ndim != 2 or factor.shape[0] != factor.shape[1]:
        return None
    return factor @ factor.T


def validate_covariance_matrix(matrix: np.ndarray) -> dict[str, Any]:
    """Validate shape, numeric content, symmetry, diagonal, and PSD status."""
    warnings: list[str] = []
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        return {"valid": False, "warnings": ["Covariance matrix is not square."]}
    if not np.isfinite(matrix).all():
        return {"valid": False, "warnings": ["Covariance matrix contains NaN or infinite values."]}
    if not np.allclose(matrix, matrix.T, rtol=1e-7, atol=1e-12):
        warnings.append("Covariance matrix was not exactly symmetric; symmetrized copy is used.")
    symmetric = (matrix + matrix.T) / 2.0
    if np.any(np.diag(symmetric) < 0):
        return {"valid": False, "warnings": ["Covariance matrix has negative diagonal entries."]}
    eigenvalues = np.linalg.eigvalsh(symmetric)
    min_eigenvalue = float(eigenvalues.min()) if eigenvalues.size else None
    is_psd = bool(min_eigenvalue is not None and min_eigenvalue >= -1e-12)
    return {
        "valid": True,
        "matrix": symmetric,
        "warnings": warnings,
        "is_positive_semidefinite": is_psd,
        "min_eigenvalue": min_eigenvalue,
        "max_eigenvalue": float(eigenvalues.max()) if eigenvalues.size else None,
    }


def make_positive_semidefinite_if_needed(matrix: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    """Apply minimal jitter when a near-PSD covariance matrix has tiny negative eigenvalues."""
    validation = validate_covariance_matrix(matrix)
    if not validation.get("valid"):
        return matrix, validation
    symmetric = validation["matrix"]
    min_eigenvalue = validation.get("min_eigenvalue")
    if validation.get("is_positive_semidefinite"):
        return symmetric, {**validation, "jitter_applied": 0.0}
    if min_eigenvalue is None:
        return symmetric, validation
    jitter = abs(float(min_eigenvalue)) + 1e-12
    adjusted = symmetric + np.eye(symmetric.shape[0]) * jitter
    adjusted_validation = validate_covariance_matrix(adjusted)
    return adjusted, {**adjusted_validation, "jitter_applied": jitter}


def align_covariance_labels(
    matrix: np.ndarray,
    labels: list[str],
    target_labels: list[str] | None = None,
) -> tuple[np.ndarray, list[str], list[str]]:
    """Align a covariance matrix to labels available in the propagation state."""
    target_labels = target_labels or PROPAGATION_LABELS
    normalized = [_normalize_label(label) for label in labels]
    indices: list[int] = []
    aligned_labels: list[str] = []
    missing: list[str] = []
    for label in target_labels:
        if label in normalized:
            index = normalized.index(label)
            if index < matrix.shape[0]:
                indices.append(index)
                aligned_labels.append(label)
            else:
                missing.append(label)
        else:
            missing.append(label)
    if not indices:
        return np.empty((0, 0)), [], missing
    aligned = matrix[np.ix_(indices, indices)]
    return aligned, aligned_labels, missing


def sample_orbital_clones(
    elements: dict[str, float],
    covariance_payload: dict[str, Any],
    n_clones: int,
    rng: np.random.Generator,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Sample orbital clones from a valid covariance matrix."""
    matrix = covariance_payload.get("matrix")
    labels = covariance_payload.get("labels", [])
    diagnostics: dict[str, Any] = {
        "covariance_available": bool(covariance_payload.get("available")),
        "covariance_dimension": int(matrix.shape[0]) if isinstance(matrix, np.ndarray) else None,
        "covariance_labels": labels,
        "warnings": list(covariance_payload.get("warnings", [])),
    }
    if not isinstance(matrix, np.ndarray):
        diagnostics["status"] = "missing_covariance"
        return {}, diagnostics
    validation = validate_covariance_matrix(matrix)
    diagnostics.update({key: validation.get(key) for key in ("min_eigenvalue", "max_eigenvalue")})
    if not validation.get("valid"):
        diagnostics["status"] = "invalid_covariance"
        diagnostics["warnings"].extend(validation.get("warnings", []))
        return {}, diagnostics
    matrix, psd_diagnostics = make_positive_semidefinite_if_needed(validation["matrix"])
    diagnostics["jitter_applied"] = psd_diagnostics.get("jitter_applied", 0.0)
    diagnostics["warnings"].extend(psd_diagnostics.get("warnings", []))
    aligned_matrix, aligned_labels, missing = align_covariance_labels(matrix, labels)
    diagnostics["aligned_covariance_labels"] = aligned_labels
    diagnostics["missing_covariance_labels"] = missing
    if aligned_matrix.size == 0 or not aligned_labels:
        diagnostics["status"] = "unaligned_covariance"
        diagnostics["warnings"].append(
            "Covariance labels could not be aligned to propagation elements."
        )
        return {}, diagnostics
    mean = np.asarray([float(elements[label]) for label in aligned_labels], dtype=float)
    try:
        samples = rng.multivariate_normal(mean, aligned_matrix, size=max(int(n_clones), 1))
    except (ValueError, np.linalg.LinAlgError) as exc:
        diagnostics["status"] = "sampling_failed"
        diagnostics["warnings"].append(f"Covariance sampling failed: {exc}.")
        return {}, diagnostics
    clones = _nominal_clone_arrays(elements, len(samples))
    for column_index, label in enumerate(aligned_labels):
        clones[label] = samples[:, column_index]
    invalid = _invalid_clone_mask(clones)
    diagnostics["invalid_clone_count"] = int(invalid.sum())
    if invalid.any():
        for key in list(clones):
            clones[key] = clones[key][~invalid]
    clones = _repair_clone_bounds(clones)
    diagnostics["valid_clone_count"] = int(len(next(iter(clones.values()))) if clones else 0)
    diagnostics["status"] = (
        "success" if diagnostics["valid_clone_count"] else "empty_after_validation"
    )
    return clones, diagnostics


def _nominal_clone_arrays(elements: dict[str, float], n: int) -> dict[str, np.ndarray]:
    return {
        key: np.full(n, float(elements[key]), dtype=float)
        for key in PROPAGATION_LABELS
        if key in elements and elements[key] is not None
    }


def _invalid_clone_mask(clones: dict[str, np.ndarray]) -> np.ndarray:
    n = len(next(iter(clones.values()))) if clones else 0
    invalid = np.zeros(n, dtype=bool)
    if "a" in clones:
        invalid |= ~np.isfinite(clones["a"]) | (clones["a"] <= 0)
    if "e" in clones:
        invalid |= ~np.isfinite(clones["e"]) | (clones["e"] < 0) | (clones["e"] >= 1)
    for key, values in clones.items():
        invalid |= ~np.isfinite(values)
    return invalid


def _repair_clone_bounds(clones: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    repaired = dict(clones)
    if "a" in repaired:
        repaired["a"] = np.clip(repaired["a"], 0.05, 12.0)
    if "e" in repaired:
        repaired["e"] = np.clip(repaired["e"], 0.0, 0.98)
    if "n" in repaired:
        repaired["n"] = np.clip(repaired["n"], 1e-6, None)
    for angle in ANGLE_LABELS:
        if angle in repaired:
            repaired[angle] = np.mod(repaired[angle], 360.0)
    return repaired


def _matrix_from_payload(value: Any) -> np.ndarray | None:
    if value is None:
        return None
    try:
        matrix = np.asarray(value, dtype=float)
    except (TypeError, ValueError):
        return None
    if matrix.ndim != 2:
        return None
    return matrix


def _payload_value(payload: Any, key: str) -> Any:
    if isinstance(payload, dict):
        for candidate in (key, key.lower(), key.upper()):
            if candidate in payload:
                return payload[candidate]
    return None


def _parse_labels(value: Any) -> list[str]:
    if value is None or _is_missing(value):
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = [item.strip() for item in value.split(",")]
    else:
        parsed = value
    if not isinstance(parsed, (list, tuple)):
        return []
    return [_normalize_label(str(item)) for item in parsed if str(item).strip()]


def _normalize_label(label: str) -> str:
    normalized = label.strip().lower()
    mapping = {
        "eccentricity": "e",
        "semi-major axis": "a",
        "semimajor_axis": "a",
        "a": "a",
        "perihelion": "q",
        "inclination": "i",
        "node": "om",
        "om": "om",
        "omega": "w",
        "w": "w",
        "ma": "ma",
        "mean anomaly": "ma",
        "n": "n",
        "mean motion": "n",
    }
    return mapping.get(normalized, normalized)


def _is_missing(value: Any) -> bool:
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False
