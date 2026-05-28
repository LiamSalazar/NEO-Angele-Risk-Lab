"""Classification metrics for small, imbalanced NEO risk datasets."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def calculate_classification_metrics(
    y_true: Any,
    y_pred: Any,
    y_proba: Any = None,
    top_k_values: list[int] | None = None,
) -> dict[str, Any]:
    """Calculate JSON-serializable classification metrics without assuming scale."""
    top_k_values = top_k_values or [10, 25, 50]
    y_true_array = np.asarray(y_true).astype(int)
    y_pred_array = np.asarray(y_pred).astype(int)
    proba_positive = _positive_probability(y_proba)
    positive_support = int((y_true_array == 1).sum())
    negative_support = int((y_true_array == 0).sum())
    warnings: list[str] = []

    matrix = confusion_matrix(y_true_array, y_pred_array, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    unique_classes = np.unique(y_true_array)

    metrics: dict[str, Any] = {
        "n_samples": int(len(y_true_array)),
        "positive_support": positive_support,
        "negative_support": negative_support,
        "accuracy": float(accuracy_score(y_true_array, y_pred_array)),
        "precision": float(precision_score(y_true_array, y_pred_array, zero_division=0)),
        "recall": float(recall_score(y_true_array, y_pred_array, zero_division=0)),
        "f1": float(f1_score(y_true_array, y_pred_array, zero_division=0)),
        "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) else None,
        "roc_auc": None,
        "pr_auc": None,
        "brier_score": None,
        "confusion_matrix": matrix.astype(int).tolist(),
        "top_k_recall": {},
        "warnings": warnings,
    }

    if len(unique_classes) < 2:
        warnings.append("ROC-AUC and PR-AUC are undefined for a single-class y_true.")
    elif proba_positive is None:
        warnings.append("Probability scores were not provided; rank metrics are unavailable.")
    else:
        metrics["roc_auc"] = float(roc_auc_score(y_true_array, proba_positive))
        metrics["pr_auc"] = float(average_precision_score(y_true_array, proba_positive))

    if proba_positive is None:
        warnings.append("Brier score and top-k recall require probability scores.")
    else:
        metrics["brier_score"] = float(brier_score_loss(y_true_array, proba_positive))
        metrics["top_k_recall"] = _top_k_recall(y_true_array, proba_positive, top_k_values)

    return metrics


def _positive_probability(y_proba: Any) -> np.ndarray | None:
    if y_proba is None:
        return None
    array = np.asarray(y_proba)
    if array.ndim == 1:
        return array.astype(float)
    if array.ndim == 2 and array.shape[1] >= 2:
        return array[:, 1].astype(float)
    return None


def _top_k_recall(
    y_true: np.ndarray,
    proba_positive: np.ndarray,
    top_k_values: list[int],
) -> dict[str, float | None]:
    positive_total = int((y_true == 1).sum())
    if positive_total == 0:
        return {str(k): None for k in top_k_values}
    order = np.argsort(-proba_positive)
    recalls: dict[str, float | None] = {}
    for k in top_k_values:
        if k <= 0:
            recalls[str(k)] = None
            continue
        selected = order[: min(k, len(order))]
        recalls[str(k)] = float((y_true[selected] == 1).sum() / positive_total)
    return recalls
