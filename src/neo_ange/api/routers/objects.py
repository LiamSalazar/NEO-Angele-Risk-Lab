"""Object browsing endpoints."""

from __future__ import annotations

from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends

from neo_ange.api.schemas import RankingResponse, RiskObjectResponse
from neo_ange.pipelines.risk import RiskPipeline
from neo_ange.risk.ranking import RiskRankingService
from neo_ange.utils.serialization import to_jsonable

from ..dependencies import get_risk_pipeline

router = APIRouter(prefix="/objects", tags=["objects"])


@router.get("", response_model=RankingResponse)
def list_objects(
    risk_pipeline: Annotated[RiskPipeline, Depends(get_risk_pipeline)],
    limit: int = 50,
    offset: int = 0,
    category: str | None = None,
    sentry_flag: bool | None = None,
) -> RankingResponse:
    """List scored objects with basic filtering."""
    df = risk_pipeline.load_risk_scores()
    message = None
    if df.empty:
        df = risk_pipeline.load_gold_features()
        message = "Risk scores not found. Run: python -m neo_ange.cli risk build"
    if df.empty:
        return RankingResponse(status="missing_data", objects=[], message=message)

    filtered = df.copy()
    if category and "risk_category" in filtered.columns:
        filtered = filtered[filtered["risk_category"].astype("string").str.lower() == category.lower()]
    if sentry_flag is not None and "sentry_flag" in filtered.columns:
        filtered = filtered[_bool_series(filtered["sentry_flag"]) == sentry_flag]
    if "risk_score_0_100" in filtered.columns:
        filtered = RiskRankingService().rank(filtered)
    paged = filtered.iloc[max(offset, 0) : max(offset, 0) + max(limit, 0)]
    return RankingResponse(
        status="success" if message is None else "partial",
        objects=to_jsonable(paged.to_dict(orient="records")),
        message=message,
    )


@router.get("/{object_key}", response_model=RiskObjectResponse)
def get_object(
    object_key: str,
    risk_pipeline: Annotated[RiskPipeline, Depends(get_risk_pipeline)],
) -> RiskObjectResponse:
    """Return one object's features and score when available."""
    ranking = RiskRankingService()
    df = risk_pipeline.load_risk_scores()
    message = None
    if df.empty:
        df = risk_pipeline.load_gold_features()
        message = "Risk scores not found. Run: python -m neo_ange.cli risk build"
    row = ranking.get_object(df, object_key)
    if row is None:
        return RiskObjectResponse(
            status="not_found",
            object=None,
            message=f"Object '{object_key}' was not found.",
        )
    return RiskObjectResponse(status="success", object=row, message=message)


def _bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype("string").str.lower().isin(["true", "1", "yes", "y"])
