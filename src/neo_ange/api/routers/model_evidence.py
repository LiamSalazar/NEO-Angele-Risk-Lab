"""Model evidence endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from neo_ange.api.dependencies import get_data_paths
from neo_ange.api.schemas import StatusResponse
from neo_ange.evidence.reporting import ModelEvidenceBuilder

router = APIRouter(prefix="/model-evidence", tags=["model-evidence"])


def _builder(paths: dict) -> ModelEvidenceBuilder:
    return ModelEvidenceBuilder(gold_root=paths["gold_dir"], reports_root=paths["reports_dir"])


@router.get("/summary", response_model=StatusResponse)
def summary(paths: Annotated[dict, Depends(get_data_paths)]) -> StatusResponse:
    """Return model-evidence summary, rebuilding if missing."""
    builder = _builder(paths)
    payload = builder.read_summary()
    if not payload:
        builder.build(write=True)
        payload = builder.read_summary()
    return StatusResponse(status=payload.get("status", "success"), details=payload)


@router.get("/cards", response_model=StatusResponse)
def cards(paths: Annotated[dict, Depends(get_data_paths)]) -> StatusResponse:
    """Return model cards."""
    builder = _builder(paths)
    payload = builder.read_cards()
    if not payload:
        builder.build(write=True)
        payload = builder.read_cards()
    return StatusResponse(status=payload.get("status", "success"), details=payload)


@router.get("/predictions", response_model=StatusResponse)
def predictions(
    paths: Annotated[dict, Depends(get_data_paths)],
    mode: str = "full",
) -> StatusResponse:
    """Return observable prediction rows for full inference or eval mode."""
    builder = _builder(paths)
    payload = builder.read_predictions(mode=mode)
    if payload.get("status") == "missing_data":
        builder.build(write=True)
        payload = builder.read_predictions(mode=mode)
    return StatusResponse(status=payload.get("status", "success"), details=payload)


@router.get("/disagreements", response_model=StatusResponse)
def disagreements(paths: Annotated[dict, Depends(get_data_paths)]) -> StatusResponse:
    """Return model disagreement rows."""
    builder = _builder(paths)
    payload = builder.read_disagreements()
    if payload.get("status") == "missing_data":
        builder.build(write=True)
        payload = builder.read_disagreements()
    return StatusResponse(status=payload.get("status", "success"), details=payload)


@router.get("/object/{object_key}", response_model=StatusResponse)
def object_evidence(
    object_key: str,
    paths: Annotated[dict, Depends(get_data_paths)],
    mode: str = "full",
) -> StatusResponse:
    """Return model evidence for one object."""
    builder = _builder(paths)
    if not builder.read_summary():
        builder.build(write=True)
    payload = builder.object_evidence(object_key, mode=mode)
    return StatusResponse(status=payload.get("status", "success"), details=payload)
