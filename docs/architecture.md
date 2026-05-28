# Architecture

Neo Angele Risk Lab follows a staged analytical data platform architecture. The current implementation includes ingestion, bronze storage, Spark ETL, silver Parquet tables, a gold feature dataset, and quality reporting.

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
Spark bronze-to-silver ETL
        |
        v
Silver Parquet tables
        |
        v
Gold neo_risk_features
        |
        v
Quality reports and future models/APIs/dashboard
```

## Current Implemented Layers

- API clients: wrap public NASA/JPL endpoints with timeout, connection, HTTP, JSON, and empty-response handling.
- Ingestion pipeline: orchestrates sample ingestion while allowing dependency injection for tests.
- Bronze storage: writes raw JSON payloads with metadata under date-partitioned paths.
- Spark session factory: creates local PySpark sessions with conservative settings.
- Bronze reader: reads wrapped JSON files and preserves metadata, ingest date, and file path lineage.
- Silver ETL: normalizes SBDB Object, CAD, Sentry summary, Sentry virtual impactor, and ingestion event datasets.
- Gold builder: constructs `neo_risk_features` from available silver tables.
- Quality checks: produce JSON reports for required columns, emptiness, null ratios, duplicate keys, and numeric ranges.
- CLI: exposes repeatable ingestion commands and project information.
- Tests: cover clients, storage, pipeline behavior, and CLI entry points without requiring internet access.

## Future Layers

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
- `data/silver/`: validated and normalized Parquet records.
- `data/gold/`: analytical marts, feature datasets, and quality reports.
- `docs/`: architecture, data source, and roadmap documentation.
- `notebooks/`: reserved for exploratory work, kept empty in this phase.
- `src/neo_ange/clients/`: public NASA/JPL API clients.
- `src/neo_ange/domain/`: lightweight metadata models.
- `src/neo_ange/etl/`: bronze reader, silver transformers, gold builder, writers, and quality checks.
- `src/neo_ange/pipelines/`: orchestration logic.
- `src/neo_ange/services/`: storage and persistence services.
- `src/neo_ange/spark/`: Spark session factory.
- `src/neo_ange/utils/`: configuration, logging, and time helpers.
- `tests/`: unit tests using mocks and temporary directories.
- `api/`: reserved for future FastAPI implementation.
- `dashboard/`: reserved for future dashboard implementation.
