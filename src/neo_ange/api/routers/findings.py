"""User-facing analytical findings endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from neo_ange.api.dependencies import get_data_paths
from neo_ange.api.schemas import StatusResponse
from neo_ange.findings.reporting import FindingsBuilder

router = APIRouter(prefix="/findings", tags=["findings"])


def _builder(paths: dict) -> FindingsBuilder:
    return FindingsBuilder(gold_root=paths["gold_dir"], reports_root=paths["reports_dir"])


@router.get("/summary", response_model=StatusResponse)
def findings_summary(paths: Annotated[dict, Depends(get_data_paths)]) -> StatusResponse:
    """Return generated summary findings, rebuilding if needed."""
    payload = _builder(paths).read_group("summary")
    return StatusResponse(status=payload.get("status", "success"), details=payload)


@router.get("/risk", response_model=StatusResponse)
def risk_findings(paths: Annotated[dict, Depends(get_data_paths)]) -> StatusResponse:
    """Return risk findings."""
    payload = _builder(paths).read_group("risk")
    return StatusResponse(status=payload.get("status", "success"), details=payload)


@router.get("/score-simulation", response_model=StatusResponse)
def score_simulation_findings(paths: Annotated[dict, Depends(get_data_paths)]) -> StatusResponse:
    """Return score-simulation findings."""
    payload = _builder(paths).read_group("score_simulation")
    return StatusResponse(status=payload.get("status", "success"), details=payload)


@router.get("/orbital-simulation", response_model=StatusResponse)
def orbital_simulation_findings(paths: Annotated[dict, Depends(get_data_paths)]) -> StatusResponse:
    """Return orbital-simulation findings."""
    payload = _builder(paths).read_group("orbital_simulation")
    return StatusResponse(status=payload.get("status", "success"), details=payload)


@router.get("/orbital-graph", response_model=StatusResponse)
def orbital_graph_findings(paths: Annotated[dict, Depends(get_data_paths)]) -> StatusResponse:
    """Return orbital-graph findings."""
    payload = _builder(paths).read_group("orbital_graph")
    return StatusResponse(status=payload.get("status", "success"), details=payload)


@router.get("/model-evidence", response_model=StatusResponse)
def model_evidence_findings(paths: Annotated[dict, Depends(get_data_paths)]) -> StatusResponse:
    """Return model-evidence findings."""
    payload = _builder(paths).read_group("model_evidence")
    return StatusResponse(status=payload.get("status", "success"), details=payload)


@router.get("/object/{object_key}", response_model=StatusResponse)
def object_findings(
    object_key: str,
    paths: Annotated[dict, Depends(get_data_paths)],
) -> StatusResponse:
    """Return object-specific findings."""
    payload = _builder(paths).object_findings(object_key)
    return StatusResponse(status=payload.get("status", "success"), details=payload)
