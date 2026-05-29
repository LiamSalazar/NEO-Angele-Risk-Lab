"""Monte Carlo simulation endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from neo_ange.api.schemas import BatchSimulationRequest, SimulationRequest, SimulationResponse
from neo_ange.pipelines.simulation import SimulationPipeline

from ..dependencies import get_simulation_pipeline

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/object", response_model=SimulationResponse)
def simulate_object(
    request: SimulationRequest,
    simulation_pipeline: Annotated[SimulationPipeline, Depends(get_simulation_pipeline)],
) -> SimulationResponse:
    """Run approximate Monte Carlo simulation for one object."""
    result = simulation_pipeline.simulate_object(
        object_key=request.object_key,
        n_simulations=request.n_simulations,
        random_state=request.random_state,
    )
    status = result.get("status", "unknown")
    return SimulationResponse(
        status=status,
        result=result.get("result"),
        summary=result.get("metrics_summary"),
        message="; ".join(result.get("errors", [])) or None,
    )


@router.post("/batch", response_model=SimulationResponse)
def simulate_batch(
    request: BatchSimulationRequest,
    simulation_pipeline: Annotated[SimulationPipeline, Depends(get_simulation_pipeline)],
) -> SimulationResponse:
    """Run approximate Monte Carlo simulation for top ranked objects."""
    result = simulation_pipeline.simulate_batch(
        limit=request.limit,
        n_simulations=request.n_simulations,
        random_state=request.random_state,
    )
    status = result.get("status", "unknown")
    return SimulationResponse(
        status=status,
        results=result.get("results", []),
        summary=result.get("metrics_summary"),
        message="; ".join(result.get("errors", [])) or None,
    )


@router.get("/status")
def simulation_status(
    simulation_pipeline: Annotated[SimulationPipeline, Depends(get_simulation_pipeline)],
) -> dict:
    """Return simulation pipeline status."""
    return simulation_pipeline.status()


@router.get("/object/{object_key}/latest", response_model=SimulationResponse)
def latest_for_object(
    object_key: str,
    simulation_pipeline: Annotated[SimulationPipeline, Depends(get_simulation_pipeline)],
) -> SimulationResponse:
    """Return the latest saved simulation result for one object."""
    result = simulation_pipeline.latest_for_object(object_key)
    if result is None:
        return SimulationResponse(
            status="not_found",
            result=None,
            message=(
                "Simulation results not found. Run: "
                "python -m neo_ange.cli simulate batch"
            ),
        )
    return SimulationResponse(status="success", result=result)
