"""Risk-score endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from neo_ange.api.schemas import ExplanationResponse, StatusResponse
from neo_ange.pipelines.risk import RiskPipeline

from ..dependencies import get_risk_pipeline

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post("/build", response_model=StatusResponse)
def build_risk_scores(
    risk_pipeline: Annotated[RiskPipeline, Depends(get_risk_pipeline)],
) -> StatusResponse:
    """Run the risk scoring pipeline."""
    result = risk_pipeline.build_scores()
    return StatusResponse(status=result.get("status", "unknown"), details=result)


@router.get("/status", response_model=StatusResponse)
def risk_status(
    risk_pipeline: Annotated[RiskPipeline, Depends(get_risk_pipeline)],
) -> StatusResponse:
    """Return risk pipeline status."""
    return StatusResponse(status="ok", details=risk_pipeline.status())


@router.get("/explain/{object_key}", response_model=ExplanationResponse)
def explain_object(
    object_key: str,
    risk_pipeline: Annotated[RiskPipeline, Depends(get_risk_pipeline)],
) -> ExplanationResponse:
    """Return a structured score explanation for one object."""
    explanation = risk_pipeline.explain(object_key)
    status = explanation.get("status", "success")
    if status != "success":
        return ExplanationResponse(
            status=status, explanation=None, message=explanation.get("message")
        )
    return ExplanationResponse(status="success", explanation=explanation)


@router.get("/methodology", response_model=StatusResponse)
def methodology(
    risk_pipeline: Annotated[RiskPipeline, Depends(get_risk_pipeline)],
) -> StatusResponse:
    """Return methodology report content or path."""
    payload: dict[str, Any] = risk_pipeline.methodology()
    return StatusResponse(status="success", details=payload)
