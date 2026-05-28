# Neo Angele Risk Lab

Neo Angele Risk Lab is an open-source data engineering and probabilistic risk intelligence project for exploring near-Earth objects with public NASA/JPL data. It is designed as a professional portfolio-grade foundation for ingestion, lakehouse-style data layers, machine learning, simulation, and future analytical applications.

## What This Project Does

The project builds a reproducible Python data platform around NASA/JPL Small-Body and CNEOS APIs. It supports raw JSON ingestion into a bronze layer, Spark-based normalization into silver Parquet tables, and an initial gold feature dataset for future ML, ranking, and simulation work.

## Current Phase Support

This release implements phases 0 through 4:

- Project documentation and operating design.
- Installable Python package using a `src/` layout.
- Modular API clients for NASA/JPL SSD and CNEOS JSON endpoints.
- CLI commands for sample ingestion.
- Bronze JSON storage with ingestion metadata.
- Local PySpark bronze-to-silver ETL.
- Silver Parquet tables for SBDB Object, CAD, Sentry, and ingestion events.
- Initial gold analytical dataset named `neo_risk_features`.
- JSON quality reports for the gold dataset.
- Unit tests with mocked clients and responses.
- Docker and Docker Compose entry points for CLI execution.

## What It Does Not Claim

Neo Angele Risk Lab does not replace NASA/JPL systems, does not produce official planetary defense alerts, and should not be used as an authoritative warning system. It is an educational and technical risk intelligence platform built on public NASA/JPL data. The current gold features are not the final Risk Priority Score.

## Data Sources

The current ingestion layer uses public JSON APIs from NASA/JPL SSD and CNEOS:

- SBDB Object API: object-level orbital, physical, close approach, virtual impactor, and covariance data.
- SBDB Query API: tabular queries over asteroid and comet sets.
- Close Approach Data API: close approach records for asteroids and comets.
- Sentry API: CNEOS Sentry impact risk summary, object, virtual impactor, and removed-object results.

No API keys or private credentials are required.

## Architecture Overview

The current architecture is intentionally small and modular:

- `clients/`: typed NASA/JPL API clients with explicit error handling.
- `pipelines/`: ingestion orchestration with injectable dependencies.
- `services/`: bronze storage and file layout.
- `domain/`: lightweight metadata models.
- `utils/`: configuration, logging, and UTC time helpers.
- `spark/`: local Spark session factory.
- `etl/`: bronze readers, silver transformers, gold builder, writers, and quality checks.
- `data/bronze/`: raw JSON landing zone for source responses.
- `data/silver/`: normalized Parquet tables.
- `data/gold/`: analytical feature datasets and quality reports.

Future phases will add baseline machine learning, leakage audits, calibrated risk scoring, dashboarding, FastAPI access, Monte Carlo simulation, and graph neural network research.

## Setup

Python 3.11 or newer is required.

### macOS and Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## CLI Usage

Show project and configuration information:

```bash
python -m neo_ange.cli info
```

Run a small multi-source ingestion sample:

```bash
python -m neo_ange.cli ingest sample
```

Ingest an SBDB Query NEO sample:

```bash
python -m neo_ange.cli ingest sbdb-query --limit 100
```

Ingest one object:

```bash
python -m neo_ange.cli ingest object --designation "99942"
```

Ingest close approach data:

```bash
python -m neo_ange.cli ingest cad --date-min 2026-01-01 --date-max 2026-12-31 --dist-max 0.2 --limit 100
```

Ingest Sentry summary data:

```bash
python -m neo_ange.cli ingest sentry
```

Ingest Sentry virtual impactors:

```bash
python -m neo_ange.cli ingest sentry-vi --ip-min 1e-6
```

## Spark ETL and Feature Engineering

PySpark requires Java to be installed and available on `PATH`. Java 17 is recommended for local development.

Inspect ETL data availability:

```bash
python -m neo_ange.cli etl status
```

Build silver tables from bronze JSON:

```bash
python -m neo_ange.cli etl bronze-to-silver
python -m neo_ange.cli etl bronze-to-silver --source sbdb_object
python -m neo_ange.cli etl bronze-to-silver --source cad
python -m neo_ange.cli etl bronze-to-silver --source sentry
```

Build the gold feature dataset:

```bash
python -m neo_ange.cli etl build-gold
```

Run the full local ETL flow:

```bash
python -m neo_ange.cli etl run-all
```

Outputs are written under:

- `data/silver/`
- `data/gold/neo_risk_features/`
- `data/gold/quality_reports/`

The gold features are initial, explainable engineering signals. They are not a final calibrated Risk Priority Score.

## Testing and Quality

Run tests:

```bash
pytest
```

Run linting and formatting checks:

```bash
ruff check .
black --check .
```

Equivalent Make targets are available:

```bash
make install
make test
make lint
make format
make ingest-sample
make etl-status
make build-gold
make etl
```

## Docker

Build and run the default CLI command:

```bash
docker compose run --rm app
```

Run ingestion from Docker Compose:

```bash
docker compose run --rm app python -m neo_ange.cli ingest sample
```

Run ETL status from Docker Compose:

```bash
docker compose run --rm app python -m neo_ange.cli etl status
```

## Roadmap Summary

- Phase 3: Spark ETL from bronze to silver and gold. Implemented.
- Phase 4: feature engineering for orbital and close approach risk analysis. Implemented.
- Phase 5: baseline ML and leakage audit.
- Phase 6: Risk Priority Score design and calibration.
- Phase 7: dashboard and FastAPI service.
- Phase 8: Monte Carlo simulation research.
- Phase 9: graph neural network experiments.
