"""Domain-oriented object endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends

from neo_ange.api.dependencies import get_data_paths
from neo_ange.api.schemas import RiskObjectResponse
from neo_ange.domain.repositories import (
    GoldFeatureRepository,
    RiskScoreRepository,
    SimulationResultRepository,
)

router = APIRouter(prefix="/domain", tags=["domain"])


@router.get("/objects/{object_key}", response_model=RiskObjectResponse)
def get_domain_object(
    object_key: str,
    paths: Annotated[dict[str, Path], Depends(get_data_paths)],
) -> RiskObjectResponse:
    """Return an asteroid using the domain aggregate representation."""
    asteroid = GoldFeatureRepository(paths["gold_dir"]).get_by_object_key(object_key)
    if asteroid is None:
        return RiskObjectResponse(
            status="not_found",
            object=None,
            message=f"Object '{object_key}' was not found in gold features.",
        )
    score = RiskScoreRepository(paths["gold_dir"]).get_score(object_key)
    simulation = SimulationResultRepository(paths["gold_dir"]).get_latest_for_object(object_key)
    return RiskObjectResponse(
        status="success",
        object={
            **asteroid.to_dict(),
            "risk_score": score.to_dict() if score is not None else None,
            "simulation_result": simulation.to_dict() if simulation is not None else None,
        },
    )
