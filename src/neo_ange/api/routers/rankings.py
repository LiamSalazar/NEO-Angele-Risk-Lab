"""Risk ranking endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from neo_ange.api.schemas import RankingResponse, StatusResponse
from neo_ange.pipelines.risk import RiskPipeline
from neo_ange.risk.ranking import RiskRankingService
from neo_ange.utils.serialization import to_jsonable

from ..dependencies import get_risk_pipeline

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/top", response_model=RankingResponse)
def top_rankings(
    risk_pipeline: Annotated[RiskPipeline, Depends(get_risk_pipeline)],
    limit: int = 20,
) -> RankingResponse:
    """Return top risk-priority objects."""
    df = risk_pipeline.load_risk_scores()
    if df.empty:
        return RankingResponse(
            status="missing_data",
            objects=[],
            message="Risk scores not found. Run: python -m neo_ange.cli risk build",
        )
    ranked = RiskRankingService().rank(df, limit=limit)
    return RankingResponse(objects=to_jsonable(ranked.to_dict(orient="records")))


@router.get("/summary", response_model=StatusResponse)
def ranking_summary(
    risk_pipeline: Annotated[RiskPipeline, Depends(get_risk_pipeline)],
) -> StatusResponse:
    """Return ranking summary statistics."""
    df = risk_pipeline.load_risk_scores()
    if df.empty:
        return StatusResponse(
            status="missing_data",
            details={"message": "Risk scores not found. Run: python -m neo_ange.cli risk build"},
        )
    return StatusResponse(status="success", details=RiskRankingService().summarize_ranking(df))


@router.get("/category/{category}", response_model=RankingResponse)
def rankings_by_category(
    category: str,
    risk_pipeline: Annotated[RiskPipeline, Depends(get_risk_pipeline)],
    limit: int = 20,
) -> RankingResponse:
    """Return top risk-priority objects for one category."""
    df = risk_pipeline.load_risk_scores()
    if df.empty:
        return RankingResponse(
            status="missing_data",
            objects=[],
            message="Risk scores not found. Run: python -m neo_ange.cli risk build",
        )
    ranked = RiskRankingService().top_by_category(df, category, limit=limit)
    return RankingResponse(objects=to_jsonable(ranked.to_dict(orient="records")))
