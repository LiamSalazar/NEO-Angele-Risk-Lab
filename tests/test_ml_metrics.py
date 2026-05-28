from __future__ import annotations

from neo_ange.ml.metrics import calculate_classification_metrics


def test_classification_metrics_basic_and_rank_metrics() -> None:
    metrics = calculate_classification_metrics(
        y_true=[0, 1, 1, 0],
        y_pred=[0, 1, 0, 0],
        y_proba=[0.1, 0.9, 0.4, 0.2],
        top_k_values=[1, 2],
    )

    assert metrics["n_samples"] == 4
    assert metrics["positive_support"] == 2
    assert metrics["confusion_matrix"] == [[2, 0], [1, 1]]
    assert metrics["roc_auc"] is not None
    assert metrics["pr_auc"] is not None
    assert metrics["top_k_recall"]["1"] == 0.5


def test_metrics_do_not_break_with_single_class() -> None:
    metrics = calculate_classification_metrics(y_true=[0, 0], y_pred=[0, 0])

    assert metrics["roc_auc"] is None
    assert metrics["pr_auc"] is None
    assert metrics["warnings"]
