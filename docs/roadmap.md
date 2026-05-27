# Roadmap

## Phase 0: Operating Design

Document the purpose, limits, architecture, sources, and implementation roadmap.

## Phase 1: Repository Foundation

Create an installable, tested, linted Python package with Docker and CLI support.

## Phase 2: NASA/JPL Ingestion

Ingest raw JSON from SBDB Object, SBDB Query, Close Approach Data, and Sentry APIs into the bronze layer.

## Phase 3: Spark ETL

Normalize bronze payloads into silver tables and analytical gold datasets using Spark.

## Phase 4: Feature Engineering

Build reusable transformations for orbital, physical, close approach, and impact-risk features.

## Phase 5: Baseline ML and Leakage Audit

Train initial transparent models and audit features for temporal or target leakage.

## Phase 6: Risk Priority Score

Design a calibrated score that combines interpretable risk indicators.

## Phase 7: API and Dashboard

Expose processed data through FastAPI and a dashboard for exploration and presentation.

## Phase 8: Monte Carlo Simulation

Add uncertainty-aware simulation experiments for probabilistic risk analysis.

## Phase 9: Graph Research

Explore graph neural network methods over object, orbit, approach, and temporal relationships.

