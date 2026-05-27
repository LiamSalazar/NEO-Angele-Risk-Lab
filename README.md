# Neo Angele Risk Lab

Neo Angele Risk Lab is an open-source data engineering and probabilistic risk intelligence project for exploring near-Earth objects with public NASA/JPL data. It is designed as a professional portfolio-grade foundation for ingestion, lakehouse-style data layers, machine learning, simulation, and future analytical applications.

## What This Project Does

The project builds a reproducible Python data platform around NASA/JPL Small-Body and CNEOS APIs. In this phase, it focuses on reliable ingestion of raw JSON responses into a bronze data layer, preserving source metadata and API signatures for downstream processing.

## Current Phase Support

This release implements phases 0, 1, and 2:

- Project documentation and operating design.
- Installable Python package using a `src/` layout.
- Modular API clients for NASA/JPL SSD and CNEOS JSON endpoints.
- CLI commands for sample ingestion.
- Bronze JSON storage with ingestion metadata.
- Unit tests with mocked clients and responses.
- Docker and Docker Compose entry points for CLI execution.

## What It Does Not Claim

Neo Angele Risk Lab does not replace NASA/JPL systems, does not produce official planetary defense alerts, and should not be used as an authoritative warning system. It is an educational and technical risk intelligence platform built on public NASA/JPL data. The current phase only implements ingestion into the bronze layer.

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
- `data/bronze/`: raw JSON landing zone for source responses.

Future phases will add Spark-based bronze/silver/gold ETL, feature engineering, baseline machine learning, leakage audits, risk scoring, dashboarding, FastAPI access, Monte Carlo simulation, and graph neural network research.

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

## Roadmap Summary

- Phase 3: Spark ETL from bronze to silver and gold.
- Phase 4: feature engineering for orbital and close approach risk analysis.
- Phase 5: baseline ML and leakage audit.
- Phase 6: Risk Priority Score design and calibration.
- Phase 7: dashboard and FastAPI service.
- Phase 8: Monte Carlo simulation research.
- Phase 9: graph neural network experiments.

