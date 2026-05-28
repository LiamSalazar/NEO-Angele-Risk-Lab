"""Load and validate gold feature datasets for baseline ML experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.utils.paths import contains_files


class MLDatasetLoader:
    """Read the gold ``neo_risk_features`` table into pandas."""

    def __init__(self, gold_root: str | Path = "data/gold") -> None:
        self.gold_root = Path(gold_root)

    @property
    def features_path(self) -> Path:
        """Return the expected gold feature table path."""
        return self.gold_root / "neo_risk_features"

    def load_gold_features(self) -> pd.DataFrame:
        """Load ``data/gold/neo_risk_features`` or return an empty frame if absent."""
        if not contains_files(self.features_path, "*.parquet"):
            return pd.DataFrame()
        return pd.read_parquet(self.features_path)

    def validate_target(self, df: pd.DataFrame, target: str = "pha") -> dict[str, Any]:
        """Validate target availability and class distribution."""
        warnings: list[str] = []
        n_rows = int(len(df))
        if target not in df.columns:
            return {
                "status": "missing_target",
                "n_rows": n_rows,
                "n_positive": 0,
                "n_negative": 0,
                "positive_rate": None,
                "warnings": [f"Target column '{target}' is missing."],
            }

        target_values = _target_to_numeric(df[target]).dropna()
        n_labeled = int(len(target_values))
        n_positive = int((target_values == 1).sum())
        n_negative = int((target_values == 0).sum())
        positive_rate = float(n_positive / n_labeled) if n_labeled else None

        if n_labeled == 0:
            status = "insufficient_data"
            warnings.append(f"Target column '{target}' has no labeled rows.")
        elif n_positive == 0 or n_negative == 0:
            status = "single_class"
            warnings.append(f"Target column '{target}' has only one observed class.")
        else:
            status = "ok"

        return {
            "status": status,
            "n_rows": n_rows,
            "n_positive": n_positive,
            "n_negative": n_negative,
            "positive_rate": positive_rate,
            "warnings": warnings,
        }

    def prepare_training_frame(
        self,
        target: str = "pha",
        dropna_target: bool = True,
    ) -> pd.DataFrame:
        """Return a training frame with the target converted to integer labels."""
        df = self.load_gold_features().copy()
        if target not in df.columns:
            return df

        converted = _target_to_numeric(df[target])
        if dropna_target:
            df = df.loc[converted.notna()].copy()
            converted = converted.loc[df.index]
        df[target] = converted.astype("int64") if converted.notna().all() else converted
        return df


def _target_to_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype("Int64")
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").astype("Int64")

    normalized = series.astype("string").str.strip().str.lower()
    mapped = normalized.map(
        {
            "true": 1,
            "t": 1,
            "1": 1,
            "yes": 1,
            "y": 1,
            "false": 0,
            "f": 0,
            "0": 0,
            "no": 0,
            "n": 0,
        }
    )
    return mapped.astype("Int64")
