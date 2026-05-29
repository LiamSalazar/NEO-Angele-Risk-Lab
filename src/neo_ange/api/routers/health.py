"""Health and system status endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from neo_ange import __version__
from neo_ange.api.dependencies import get_data_paths, get_risk_pipeline, get_simulation_pipeline
from neo_ange.api.schemas import HealthResponse, StatusResponse
from neo_ange.manifests.run_manifest import list_manifests, load_latest_manifest
from neo_ange.pipelines.risk import RiskPipeline
from neo_ange.pipelines.simulation import SimulationPipeline
from neo_ange.utils.paths import contains_files

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return basic service health."""
    return HealthResponse(
        status="ok",
        service="neo-ange-risk-lab-api",
        version=__version__,
        timestamp_utc=datetime.now(UTC).isoformat(),
    )


@router.get("/status", response_model=StatusResponse)
def status(
    paths: Annotated[dict[str, Path], Depends(get_data_paths)],
    risk_pipeline: Annotated[RiskPipeline, Depends(get_risk_pipeline)],
    simulation_pipeline: Annotated[SimulationPipeline, Depends(get_simulation_pipeline)],
) -> StatusResponse:
    """Return data/report availability across the project."""
    manifest_dir = paths["manifest_dir"]
    latest_manifests: dict[str, Any] = {}
    for run_type in ["ingestion", "etl", "ml", "risk", "simulation"]:
        latest = load_latest_manifest(run_type, manifest_dir)
        latest_manifests[run_type] = latest
    details = {
        "bronze_available": contains_files(paths["bronze_dir"], "*.json"),
        "silver_available": contains_files(paths["silver_dir"], "*.parquet"),
        "gold_features_available": contains_files(paths["gold_features_dir"], "*.parquet"),
        "risk_scores_available": contains_files(paths["risk_scores_dir"], "*.parquet"),
        "simulation_reports_available": contains_files(Path("reports/simulation"), "*"),
        "latest_manifest_paths": {
            run_type: [str(path) for path in list_manifests(run_type, manifest_dir)[-3:]]
            for run_type in ["ingestion", "etl", "ml", "risk", "simulation"]
        },
        "latest_manifests": latest_manifests,
        "risk": risk_pipeline.status(),
        "simulation": simulation_pipeline.status(),
    }
    return StatusResponse(status="ok", details=details)
