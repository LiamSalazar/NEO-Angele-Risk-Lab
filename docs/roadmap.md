# Roadmap

## Phase 0: Operating Design

Document the purpose, limits, architecture, sources, and implementation roadmap.

## Phase 1: Repository Foundation

Create an installable, tested, linted Python package with Docker and CLI support.

## Phase 2: NASA/JPL Ingestion

Ingest raw JSON from SBDB Object, SBDB Query, Close Approach Data, and Sentry APIs into the bronze layer.

## Phase 3: Spark ETL

Implemented. Normalize bronze payloads into silver Parquet tables using Spark, including SBDB Object, CAD, Sentry, virtual impactor, and ingestion event outputs.

## Phase 4: Feature Engineering

Implemented. Build the initial `neo_risk_features` gold dataset with orbital, physical, close approach, Sentry, proxy-score, and feature-completeness fields.

## Phase 4.5: Data Expansion and ETL Hardening

Implemented. Discover object designations from local CAD/Sentry data, bulk-ingest additional SBDB Object payloads, write run manifests, and report gold ML-readiness warnings without blocking ETL.

## Phase 5: Baseline ML and Leakage Audit

Implemented. Train transparent baseline models when data volume is sufficient, skip honestly when it is not, compare leakage-aware feature sets, and generate JSON, CSV, and Markdown reports.

## Phase 6: Risk Priority Score

Design a calibrated score that combines interpretable risk indicators.

## Phase 7: API and Dashboard

Expose processed data through FastAPI and a dashboard for exploration and presentation.

## Phase 8: Monte Carlo Simulation

Add uncertainty-aware simulation experiments for probabilistic risk analysis.

## Phase 9: Graph Research

Explore graph neural network methods over object, orbit, approach, and temporal relationships.
