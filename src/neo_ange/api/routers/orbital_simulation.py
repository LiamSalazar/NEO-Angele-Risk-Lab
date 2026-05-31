"""Approximate orbital simulation endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from neo_ange.api.dependencies import get_orbital_simulation_service
from neo_ange.api.schemas import (
    BatchOrbitalSimulationRequest,
    OrbitalSimulationRequest,
    SimulationResponse,
    StatusResponse,
)
from neo_ange.orbital_simulation.service import OrbitalSimulationService

router = APIRouter(prefix="/orbital-simulation", tags=["orbital-simulation"])


@router.get("/status", response_model=StatusResponse)
def status(
    service: Annotated[OrbitalSimulationService, Depends(get_orbital_simulation_service)],
) -> StatusResponse:
    """Return orbital simulation availability."""
    payload = service.status()
    return StatusResponse(status=payload.get("status", "ok"), details=payload)


@router.post("/object", response_model=SimulationResponse)
def simulate_object(
    request: OrbitalSimulationRequest,
    service: Annotated[OrbitalSimulationService, Depends(get_orbital_simulation_service)],
) -> SimulationResponse:
    """Run approximate orbital simulation for one object."""
    result = service.simulate_object(
        object_key=request.object_key,
        n_clones=request.n_clones,
        horizon_days=request.horizon_days,
        time_step_days=request.time_step_days,
        random_state=request.random_state,
    )
    return SimulationResponse(
        status=result.get("status", "unknown"),
        result=result.get("result"),
        summary=result.get("metrics_summary"),
        message="; ".join(result.get("errors", [])) or None,
    )


@router.post("/batch", response_model=SimulationResponse)
def simulate_batch(
    request: BatchOrbitalSimulationRequest,
    service: Annotated[OrbitalSimulationService, Depends(get_orbital_simulation_service)],
) -> SimulationResponse:
    """Run approximate orbital simulation for top-ranked objects."""
    result = service.simulate_batch(
        limit=request.limit,
        n_clones=request.n_clones,
        horizon_days=request.horizon_days,
        time_step_days=request.time_step_days,
        random_state=request.random_state,
    )
    return SimulationResponse(
        status=result.get("status", "unknown"),
        results=result.get("results", []),
        summary=result.get("metrics_summary"),
        message="; ".join(result.get("errors", [])) or None,
    )


@router.get("/object/{object_key}/latest", response_model=SimulationResponse)
def latest_for_object(
    object_key: str,
    service: Annotated[OrbitalSimulationService, Depends(get_orbital_simulation_service)],
) -> SimulationResponse:
    """Return latest saved orbital simulation for one object."""
    result = service.latest_for_object(object_key)
    if result is None:
        return SimulationResponse(
            status="not_found",
            result=None,
            message="Orbital simulation results not found for this object.",
        )
    return SimulationResponse(status="success", result=result)


@router.get("/findings", response_model=StatusResponse)
def findings(
    service: Annotated[OrbitalSimulationService, Depends(get_orbital_simulation_service)],
) -> StatusResponse:
    """Return orbital simulation findings."""
    payload = service.findings()
    return StatusResponse(status=payload.get("status", "success"), details=payload)
