# Architecture

Neo Angele Risk Lab follows a staged data platform architecture. The current implementation keeps the scope intentionally narrow: production-quality ingestion into a raw bronze layer, with clear interfaces for future ETL, modeling, simulation, and application layers.

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
        |
        v
Future silver/gold ETL, features, models, APIs, and dashboard
```

## Current Implemented Layers

- API clients: wrap public NASA/JPL endpoints with timeout, connection, HTTP, JSON, and empty-response handling.
- Ingestion pipeline: orchestrates sample ingestion while allowing dependency injection for tests.
- Bronze storage: writes raw JSON payloads with metadata under date-partitioned paths.
- CLI: exposes repeatable ingestion commands and project information.
- Tests: cover clients, storage, pipeline behavior, and CLI entry points without requiring internet access.

## Future Layers

- Spark bronze/silver/gold ETL for scalable normalization and enrichment.
- Feature engineering for orbital, physical, close approach, and impact-risk fields.
- Baseline ML models for exploratory risk classification and ranking.
- Leakage audit to prevent future-looking labels or derived target leakage.
- Risk Priority Score based on transparent, calibrated signals.
- Dashboard for exploration and portfolio presentation.
- FastAPI service for programmatic access to processed datasets and scores.
- Monte Carlo simulation for uncertainty-aware trajectory and risk experiments.
- GNN research over object, approach, orbit-class, and temporal relationship graphs.

## Directory Responsibilities

- `configs/`: application and datasource configuration.
- `data/bronze/`: raw JSON API responses with ingestion metadata.
- `data/silver/`: reserved for validated and normalized records in future phases.
- `data/gold/`: reserved for analytical marts and model-ready datasets in future phases.
- `docs/`: architecture, data source, and roadmap documentation.
- `notebooks/`: reserved for exploratory work, kept empty in this phase.
- `src/neo_ange/clients/`: public NASA/JPL API clients.
- `src/neo_ange/domain/`: lightweight metadata models.
- `src/neo_ange/pipelines/`: orchestration logic.
- `src/neo_ange/services/`: storage and persistence services.
- `src/neo_ange/utils/`: configuration, logging, and time helpers.
- `tests/`: unit tests using mocks and temporary directories.
- `api/`: reserved for future FastAPI implementation.
- `dashboard/`: reserved for future dashboard implementation.

