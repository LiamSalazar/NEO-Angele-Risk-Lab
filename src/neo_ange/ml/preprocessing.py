"""Preprocessing and train-test splitting helpers for baseline models."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler


def build_preprocessor(feature_names: list[str]) -> Pipeline:
    """Build the default scaled preprocessor for linear models."""
    return build_linear_preprocessor(feature_names)


def build_linear_preprocessor(feature_names: list[str]) -> Pipeline:
    """Convert features to numeric, impute medians, and scale."""
    return Pipeline(
        steps=[
            ("to_numeric", FunctionTransformer(_to_numeric_frame, validate=False)),
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )


def build_tree_preprocessor(feature_names: list[str]) -> Pipeline:
    """Convert features to numeric and impute medians for tree models."""
    return Pipeline(
        steps=[
            ("to_numeric", FunctionTransformer(_to_numeric_frame, validate=False)),
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )


def split_dataset(
    X: Any,
    y: Any,
    test_size: float = 0.25,
    random_state: int = 42,
) -> tuple[Any, Any, Any, Any, list[str]]:
    """Split data, using stratification only when both classes can support it."""
    y_series = pd.Series(y)
    class_counts = y_series.value_counts(dropna=False)
    warnings: list[str] = []
    stratify = y_series if len(class_counts) > 1 and int(class_counts.min()) >= 2 else None
    if stratify is None:
        warnings.append(
            "Train-test split was not stratified because at least one class has fewer than "
            "two examples."
        )
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )
    return X_train, X_test, y_train, y_test, warnings


def _to_numeric_frame(X: Any) -> pd.DataFrame:
    if isinstance(X, pd.DataFrame):
        frame = X.copy()
    else:
        frame = pd.DataFrame(X)
    for column in frame.columns:
        if pd.api.types.is_bool_dtype(frame[column]):
            frame[column] = frame[column].astype("Int64")
        else:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame
