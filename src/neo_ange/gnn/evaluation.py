"""Evaluation helpers for tabular and graph experiments."""

from __future__ import annotations

from typing import Any

import numpy as np

from neo_ange.ml.metrics import calculate_classification_metrics
from neo_ange.utils.serialization import to_jsonable


def evaluate_binary_classification(
    y_true: Any,
    y_pred: Any,
    y_proba: Any = None,
    top_k_values: list[int] | None = None,
) -> dict[str, Any]:
    """Calculate serializable binary-classification metrics."""
    y_true_array = np.asarray(y_true)
    if len(y_true_array) == 0:
        return {
            "n_samples": 0,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "roc_auc": None,
            "pr_auc": None,
            "confusion_matrix": [[0, 0], [0, 0]],
            "false_negative_rate": None,
            "top_k_recall": {},
            "warnings": ["No samples were available for evaluation."],
        }
    return to_jsonable(
        calculate_classification_metrics(
            y_true=y_true,
            y_pred=y_pred,
            y_proba=y_proba,
            top_k_values=top_k_values,
        )
    )
