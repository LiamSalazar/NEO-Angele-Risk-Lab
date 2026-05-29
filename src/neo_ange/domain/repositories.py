"""Lightweight repositories for reading processed domain data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.domain.asteroid import Asteroid
from neo_ange.domain.factories import AsteroidFactory
from neo_ange.domain.risk import RiskScore
from neo_ange.domain.simulation import MonteCarloResult


class GoldFeatureRepository:
    """Read gold feature rows as asteroid domain entities."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        features_path: str | Path | None = None,
    ) -> None:
        self.gold_root = Path(gold_root)
        self.features_path = (
            Path(features_path) if features_path else self.gold_root / "neo_risk_features"
        )

    def load_dataframe(self) -> pd.DataFrame:
        """Load gold features, or return an empty frame if absent."""
        return _read_parquet(self.features_path)

    def load_asteroids(self) -> list[Asteroid]:
        """Load all gold rows as asteroid aggregates."""
        return AsteroidFactory.many_from_dataframe(self.load_dataframe())

    def get_by_object_key(self, object_key: str) -> Asteroid | None:
        """Return one asteroid by object_key or alternate identity fields."""
        row = _find_object(self.load_dataframe(), object_key)
        return AsteroidFactory.from_gold_row(row) if row is not None else None

    def count(self) -> int:
        """Return the number of gold feature rows."""
        return int(len(self.load_dataframe()))


class RiskScoreRepository:
    """Read persisted risk scores as domain entities."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        risk_scores_path: str | Path | None = None,
    ) -> None:
        self.gold_root = Path(gold_root)
        self.risk_scores_path = (
            Path(risk_scores_path) if risk_scores_path else self.gold_root / "risk_scores"
        )

    def load_dataframe(self) -> pd.DataFrame:
        """Load risk-score rows, or return an empty frame if absent."""
        preferred = self.risk_scores_path / "risk_scores.parquet"
        if preferred.exists():
            return _read_parquet(preferred)
        return _read_parquet(self.risk_scores_path)

    def load_scores(self) -> list[RiskScore]:
        """Load all score rows as RiskScore entities."""
        df = self.load_dataframe()
        if df.empty:
            return []
        return [AsteroidFactory.risk_score_from_row(row) for _, row in df.iterrows()]

    def get_score(self, object_key: str) -> RiskScore | None:
        """Return a score by object_key or alternate identity fields."""
        row = _find_object(self.load_dataframe(), object_key)
        return AsteroidFactory.risk_score_from_row(row) if row is not None else None

    def top(self, limit: int = 20) -> list[RiskScore]:
        """Return top scores sorted descending by 0-100 score."""
        df = self.load_dataframe()
        if df.empty:
            return []
        if "risk_score_0_100" in df.columns:
            df = df.sort_values("risk_score_0_100", ascending=False, na_position="last")
        return [AsteroidFactory.risk_score_from_row(row) for _, row in df.head(limit).iterrows()]


class SimulationResultRepository:
    """Read latest Monte Carlo results as domain entities."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        simulation_results_path: str | Path | None = None,
    ) -> None:
        self.gold_root = Path(gold_root)
        self.simulation_results_path = (
            Path(simulation_results_path)
            if simulation_results_path
            else self.gold_root / "simulation_results"
        )

    def load_latest_results(self) -> list[MonteCarloResult]:
        """Load latest simulation result rows."""
        df = self._load_dataframe()
        if df.empty:
            return []
        df = _latest_rows_by_object(df)
        return [
            AsteroidFactory.monte_carlo_result_from_dict(row.to_dict()) for _, row in df.iterrows()
        ]

    def get_latest_for_object(self, object_key: str) -> MonteCarloResult | None:
        """Return the newest simulation result for one object."""
        df = self._load_dataframe()
        row = _find_object(_latest_rows_by_object(df), object_key)
        if row is None:
            return None
        return AsteroidFactory.monte_carlo_result_from_dict(row)

    def _load_dataframe(self) -> pd.DataFrame:
        preferred = self.simulation_results_path / "monte_carlo_results.parquet"
        if preferred.exists():
            return _read_parquet(preferred)
        return _read_parquet(self.simulation_results_path)


def _read_parquet(path: Path) -> pd.DataFrame:
    if path.is_file():
        return pd.read_parquet(path)
    if path.is_dir() and any(path.glob("*.parquet")):
        return pd.read_parquet(path)
    return pd.DataFrame()


def _find_object(df: pd.DataFrame, object_key: str) -> dict[str, Any] | None:
    if df.empty:
        return None
    lookup = str(object_key)
    for column in ("object_key", "spkid", "des", "full_name", "name"):
        if column not in df.columns:
            continue
        matches = df[df[column].astype("string") == lookup]
        if not matches.empty:
            return matches.iloc[0].to_dict()
    return None


def _latest_rows_by_object(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "object_key" not in df.columns:
        return df
    sort_columns = [
        column
        for column in ("simulated_at_utc", "scored_at_utc", "object_key")
        if column in df.columns
    ]
    if sort_columns:
        df = df.sort_values(sort_columns)
    return df.drop_duplicates("object_key", keep="last")
