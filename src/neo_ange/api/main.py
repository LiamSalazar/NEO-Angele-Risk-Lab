"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from neo_ange import __version__
from neo_ange.api.routers import health, objects, rankings, risk, simulations

app = FastAPI(
    title="Neo Angele Risk Lab API",
    version=__version__,
    description=(
        "Lightweight API for experimental NEO risk-priority scores and approximate "
        "Monte Carlo score-stability simulations."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(objects.router)
app.include_router(rankings.router)
app.include_router(risk.router)
app.include_router(simulations.router)
