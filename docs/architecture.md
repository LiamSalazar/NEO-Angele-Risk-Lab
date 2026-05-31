# Architecture

Neo Angele Risk Lab follows a staged analytical data platform architecture. The current implementation includes ingestion, bronze storage, data expansion, Spark ETL, silver Parquet tables, a gold feature dataset, run manifests, baseline ML, leakage audit, quality reporting, Risk Priority Score, Monte Carlo simulations, orbital graph research, model evidence, findings, FastAPI, and a React frontend.

## High-Level Architecture

```text
NASA/JPL JSON APIs
        |
        v
Typed API clients
        |
        v
Ingestion pipeline
        |
        v
Bronze JSON storage
        ^
        |
Local CAD/Sentry discovery and bulk SBDB expansion
        |
        v
Spark bronze-to-silver ETL
        |
        v
Silver Parquet tables
        |
        v
Gold neo_risk_features
        |
        v
Risk scores, simulations, ML/GNN evidence, findings, API, frontend
```

## Current Implemented Layers

- API clients: wrap public NASA/JPL endpoints with timeout, connection, HTTP, JSON, and empty-response handling.
- Ingestion pipeline: orchestrates sample ingestion while allowing dependency injection for tests.
- Bronze storage: writes raw JSON payloads with metadata under date-partitioned paths.
- Expansion: discovers designations from local CAD and Sentry sources and bulk-ingests SBDB Object payloads while tolerating per-object failures.
- Manifests: writes JSON run records for ingestion, ETL, and ML workflows under `reports/manifests/`.
- Spark session factory: creates local PySpark sessions with conservative settings.
- Bronze reader: reads wrapped JSON files and preserves metadata, ingest date, and file path lineage.
- Silver ETL: normalizes SBDB Object, CAD, Sentry summary, Sentry virtual impactor, and ingestion event datasets.
- Gold builder: constructs `neo_risk_features` from available silver tables.
- Quality checks: produce JSON reports for required columns, emptiness, null ratios, duplicate keys, and numeric ranges.
- ML pipeline: loads gold features, validates target volume, trains baseline models when appropriate, writes metrics, and audits PHA leakage.
- Risk pipeline: builds the experimental Risk Priority Score, categories, rankings, explanations, and risk reports.
- Simulation pipelines: run score Monte Carlo and approximate orbital clone simulations.
- GNN and model evidence: build orbital similarity graphs, compare baselines, run optional GraphSAGE/GCN, and publish model cards, predictions, and disagreements.
- API and frontend: expose processed data through FastAPI and a React/Vite observatory.
- Reports and artifacts: writes ML JSON/CSV/Markdown reports under `reports/ml/` and generated model files under `artifacts/models/`.
- CLI: exposes repeatable ingestion, expansion, ETL, ML, and project information commands.
- Tests: cover clients, storage, pipeline behavior, and CLI entry points without requiring internet access.

## Implemented Analytical Layers

- Risk Priority Score based on transparent, explainable signals.
- FastAPI service for processed datasets, scores, simulations, GNN, findings, and model evidence.
- React frontend for exploration and portfolio presentation.
- Monte Carlo score simulation for input-perturbation stability analysis.
- Approximate orbital simulation for clone-based distance scenarios.
- GNN research over orbital similarity graphs.

## Directory Responsibilities

- `configs/`: application and datasource configuration.
- `data/bronze/`: raw JSON API responses with ingestion metadata.
- `data/silver/`: validated and normalized Parquet records.
- `data/gold/`: analytical marts, feature datasets, and quality reports.
- `docs/`: architecture, data source, and roadmap documentation.
- `notebooks/`: reserved for exploratory work, kept empty in this phase.
- `reports/`: run manifests, ML, risk, simulation, GNN, model evidence, findings, and data-quality reports.
- `artifacts/`: generated models and figures, ignored by git except `.gitkeep` placeholders.
- `src/neo_ange/clients/`: public NASA/JPL API clients.
- `src/neo_ange/domain/`: lightweight metadata models.
- `src/neo_ange/etl/`: bronze reader, silver transformers, gold builder, writers, and quality checks.
- `src/neo_ange/expansion/`: object discovery and bulk ingestion services.
- `src/neo_ange/manifests/`: run manifest models and persistence helpers.
- `src/neo_ange/ml/`: dataset loading, feature sets, preprocessing, baselines, metrics, leakage audit, experiments, and reporting.
- `src/neo_ange/pipelines/`: orchestration logic.
- `src/neo_ange/services/`: storage and persistence services.
- `src/neo_ange/spark/`: Spark session factory.
- `src/neo_ange/utils/`: configuration, logging, and time helpers.
- `tests/`: unit tests using mocks and temporary directories.
- `src/neo_ange/api/`: FastAPI application and routers.
- `frontend/`: React/TypeScript/Vite observatory.
