"""Ranking helpers for scored NEO objects."""

from __future__ import annotations

from typing import Any

import pandas as pd

from neo_ange.utils.serialization import to_jsonable


class RiskRankingService:
    """Sort, filter, and summarize scored risk-priority tables."""

    def rank(self, df: pd.DataFrame, limit: int | None = None) -> pd.DataFrame:
        """Rank by score, then uncertainty and Sentry components."""
        if df.empty:
            return df.copy()
        ranked = df.copy()
        for column in [
            "risk_score_0_100",
            "uncertainty_risk_component",
            "sentry_risk_component",
        ]:
            if column not in ranked.columns:
                ranked[column] = 0.0
        ranked = ranked.sort_values(
            by=[
                "risk_score_0_100",
                "uncertainty_risk_component",
                "sentry_risk_component",
            ],
            ascending=[False, False, False],
            kind="mergesort",
        )
        if limit is not None:
            ranked = ranked.head(max(int(limit), 0))
        return ranked.reset_index(drop=True)

    def top_by_category(
        self,
        df: pd.DataFrame,
        category: str,
        limit: int = 20,
    ) -> pd.DataFrame:
        """Return top ranked objects within one risk-priority category."""
        if "risk_category" not in df.columns:
            return pd.DataFrame(columns=df.columns)
        filtered = df[df["risk_category"].astype("string").str.lower() == category.lower()]
        return self.rank(filtered, limit=limit)

    def get_object(self, df: pd.DataFrame, object_key: str) -> dict[str, Any] | None:
        """Return one object by object_key, spkid, des, or full_name."""
        if df.empty:
            return None
        lookup = str(object_key)
        for column in ["object_key", "spkid", "des", "full_name", "name"]:
            if column not in df.columns:
                continue
            matches = df[df[column].astype("string") == lookup]
            if not matches.empty:
                return to_jsonable(matches.iloc[0].to_dict())
        return None

    def summarize_ranking(self, df: pd.DataFrame) -> dict[str, Any]:
        """Return score distribution, category counts, and top object."""
        if df.empty or "risk_score_0_100" not in df.columns:
            return {
                "n_objects": int(len(df)),
                "score_min": None,
                "score_mean": None,
                "score_median": None,
                "score_max": None,
                "category_counts": {},
                "top_object": None,
            }
        scores = pd.to_numeric(df["risk_score_0_100"], errors="coerce").fillna(0.0)
        ranked = self.rank(df, limit=1)
        top_object = ranked.iloc[0].to_dict() if not ranked.empty else None
        category_counts = (
            df["risk_category"].fillna("unknown").astype(str).value_counts().sort_index().to_dict()
            if "risk_category" in df.columns
            else {}
        )
        return {
            "n_objects": int(len(df)),
            "score_min": float(scores.min()) if len(scores) else None,
            "score_mean": float(scores.mean()) if len(scores) else None,
            "score_median": float(scores.median()) if len(scores) else None,
            "score_max": float(scores.max()) if len(scores) else None,
            "category_counts": {str(key): int(value) for key, value in category_counts.items()},
            "top_object": to_jsonable(top_object) if top_object is not None else None,
        }
