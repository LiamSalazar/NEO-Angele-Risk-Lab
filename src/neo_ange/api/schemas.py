"""Pydantic response/request schemas for the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp_utc: str


class StatusResponse(BaseModel):
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class RiskObjectResponse(BaseModel):
    status: str = "success"
    object: dict[str, Any] | None = None
    message: str | None = None


class RankingResponse(BaseModel):
    status: str = "success"
    objects: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] | None = None
    message: str | None = None


class ExplanationResponse(BaseModel):
    status: str
    explanation: dict[str, Any] | None = None
    message: str | None = None


class SimulationRequest(BaseModel):
    object_key: str
    n_simulations: int = Field(default=1000, ge=1, le=100_000)
    random_state: int | None = 42


class BatchSimulationRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=1000)
    n_simulations: int = Field(default=500, ge=1, le=100_000)
    random_state: int | None = 42


class SimulationResponse(BaseModel):
    status: str
    result: dict[str, Any] | None = None
    results: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] | None = None
    message: str | None = None


class GNNBuildGraphRequest(BaseModel):
    k: int = Field(default=10, ge=1, le=100)
    min_nodes: int = Field(default=100, ge=1)


class GNNRunRequest(BaseModel):
    target: str = "pha"
    k: int = Field(default=10, ge=1, le=100)
    min_nodes: int = Field(default=100, ge=1)


class GNNResponse(BaseModel):
    status: str
    result: dict[str, Any] | None = None
    message: str | None = None


class OrbitalSimulationRequest(BaseModel):
    object_key: str
    n_clones: int = Field(default=500, ge=1, le=20_000)
    horizon_days: int = Field(default=3650, ge=1, le=50_000)
    time_step_days: int = Field(default=10, ge=1, le=365)
    random_state: int | None = 42


class BatchOrbitalSimulationRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=1000)
    n_clones: int = Field(default=300, ge=1, le=20_000)
    horizon_days: int = Field(default=3650, ge=1, le=50_000)
    time_step_days: int = Field(default=10, ge=1, le=365)
    random_state: int | None = 42
