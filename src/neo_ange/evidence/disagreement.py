"""Disagreement analysis for model evidence predictions."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_disagreements(predictions: pd.DataFrame) -> pd.DataFrame:
    """Return high-signal model disagreement rows."""
    if predictions.empty:
        return pd.DataFrame()
    rows = []
    for object_key, group in predictions.groupby("object_key"):
        labels = set(group["predicted_label"].dropna().astype(int).tolist())
        actual_values = set(group["actual_label"].dropna().astype(int).tolist())
        high_conf_wrong = group[
            (group["confidence_bucket"] == "high")
            & (group["correct"].astype(bool) == False)  # noqa: E712
        ]
        if len(labels) > 1 or not high_conf_wrong.empty:
            row: dict[str, Any] = {
                "object_key": object_key,
                "actual_label": next(iter(actual_values)) if actual_values else None,
                "predicted_labels": sorted(labels),
                "model_count": int(len(group)),
                "high_confidence_wrong_count": int(len(high_conf_wrong)),
                "reason": (
                    "model_family_disagreement" if len(labels) > 1 else "high_confidence_error"
                ),
                "risk_score_0_100": group["risk_score_0_100"].dropna().max(),
                "risk_category": (
                    group["risk_category"].dropna().iloc[0]
                    if group["risk_category"].notna().any()
                    else None
                ),
            }
            rows.append(row)
    return pd.DataFrame(rows)
