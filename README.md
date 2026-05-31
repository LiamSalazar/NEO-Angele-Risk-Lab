# Neo Angele Risk Lab

Neo Angele Risk Lab is an open-source data engineering and probabilistic risk intelligence project for exploring near-Earth objects with public NASA/JPL data. It is designed as a professional portfolio-grade foundation for ingestion, lakehouse-style data layers, machine learning, simulation, and future analytical applications.

## What This Project Does

The project builds a reproducible Python data platform around NASA/JPL Small-Body and CNEOS APIs. It supports raw JSON ingestion into a bronze layer, Spark-based normalization into silver Parquet tables, an initial gold feature dataset, data expansion workflows, and leakage-aware baseline ML reports.

## Current Phase Support

This release implements phases 0 through 9 as an analytical observatory:

- Project documentation and operating design.
- Installable Python package using a `src/` layout.
- Modular API clients for NASA/JPL SSD and CNEOS JSON endpoints.
- CLI commands for sample ingestion.
- Bronze JSON storage with ingestion metadata.
- Local PySpark bronze-to-silver ETL.
- Silver Parquet tables for SBDB Object, CAD, Sentry, and ingestion events.
- Initial gold analytical dataset named `neo_risk_features`.
- JSON quality reports for the gold dataset.
- Data expansion from local CAD/Sentry designations into additional SBDB Object payloads.
- Run manifests for ingestion, ETL, and ML workflows.
- Baseline scikit-learn models and leakage-aware feature-set experiments.
- PHA leakage audit reports that separate definition-related variables from contextual signals.
- Unit tests with mocked clients and responses.
- Risk Priority Score tables and explanation endpoints.
- Score Monte Carlo simulation outputs.
- Orbital graph artifacts and GNN research endpoints.
- Approximate orbital scenario simulation.
- Model evidence cards, prediction rows, and disagreement queues.
- User-facing findings generated from current artifacts.
- Docker and Docker Compose entry points for API and frontend execution.

## Frontend Observatory

A React/TypeScript frontend now lives in `frontend/`. It provides the Neo Angele Risk Lab observatory for Control Panel, Risk Ranking, Object Profile, Score Simulation, Orbital Simulation, Orbital Graph, Findings, and Methodology. See `frontend/README.md`, `docs/frontend_observatory.md`, and `docs/frontend_product_refinement.md`.

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
- `pipelines/`: ingestion, ETL, and ML orchestration with injectable dependencies.
- `services/`: bronze storage and file layout.
- `expansion/`: local object discovery and bulk SBDB Object ingestion.
- `manifests/`: JSON run manifest models and persistence.
- `ml/`: dataset loading, feature sets, preprocessing, baselines, metrics, leakage audit, and reporting.
- `domain/`: lightweight metadata models.
- `utils/`: configuration, logging, and UTC time helpers.
- `spark/`: local Spark session factory.
- `etl/`: bronze readers, silver transformers, gold builder, writers, and quality checks.
- `data/bronze/`: raw JSON landing zone for source responses.
- `data/silver/`: normalized Parquet tables.
- `data/gold/`: analytical feature datasets and quality reports.
- `reports/`: manifests, ML reports, and data-quality outputs.
- `artifacts/`: generated models and figures, ignored by git except placeholders.

Future phases will add calibrated risk scoring, dashboarding, FastAPI access, Monte Carlo simulation, and graph neural network research.

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

## Data Expansion

Discover candidate object designations from local silver/bronze CAD and Sentry data, falling back to a curated seed list when needed:

```bash
python -m neo_ange.cli expand discover --strategy all --limit 100
```

Ingest a small curated SBDB Object set:

```bash
python -m neo_ange.cli expand ingest-objects --strategy curated --limit 10
```

Ingest discovered objects while skipping bronze files that already exist:

```bash
python -m neo_ange.cli expand ingest-objects --strategy all --limit 100 --skip-existing
```

Bulk ingestion is tolerant of per-object API failures. It writes an ingestion manifest under `reports/manifests/`.

## Baseline ML

Inspect current ML readiness:

```bash
python -m neo_ange.cli ml status
```

Train baseline models when volume and class balance are sufficient:

```bash
python -m neo_ange.cli ml train-baselines --target pha
```

Run the leakage audit:

```bash
python -m neo_ange.cli ml leakage-audit --target pha
```

Run the full ML flow:

```bash
python -m neo_ange.cli ml run-all --target pha
```

Reports are written under `reports/ml/`. Lightweight serialized models are written under `artifacts/models/` and ignored by git.

## Recommended Workflow

```bash
python -m neo_ange.cli ingest sample
python -m neo_ange.cli etl run-all
python -m neo_ange.cli expand ingest-objects --strategy all --limit 100 --skip-existing
python -m neo_ange.cli etl run-all
python -m neo_ange.cli ml run-all --target pha
```

## Honest Limitation

Baseline ML may return `insufficient_data` if `neo_risk_features` does not have enough rows or enough positive PHA examples. That is expected behavior. The project should expand ingestion and rebuild ETL before training rather than fabricate metrics from a tiny or single-class dataset.

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
make expand-curated
make expand-all
make ml-status
make ml
make leakage-audit
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

Run ML status from Docker Compose:

```bash
docker compose run --rm app python -m neo_ange.cli ml status
```

Run the API and frontend together:

```bash
docker compose up --build
```

The API is exposed on `http://127.0.0.1:8000`; the frontend is exposed on `http://127.0.0.1:5174`.

Build the advanced analytical artifacts:

```bash
python -m neo_ange.cli final build-all --target 4000
python -m neo_ange.cli findings build
python -m neo_ange.cli model-evidence build
python -m neo_ange.cli orbital-sim batch --limit 50 --n-clones 300
python -m neo_ange.cli benchmark run
```

## Roadmap Summary

- Phase 3: Spark ETL from bronze to silver and gold. Implemented.
- Phase 4: feature engineering for orbital and close approach risk analysis. Implemented.
- Phase 4.5: data expansion and ETL hardening. Implemented.
- Phase 5: baseline ML and leakage audit. Implemented.
- Phase 6: Risk Priority Score design and calibration. Implemented.
- Phase 7: dashboard and FastAPI service. Implemented.
- Phase 8: Monte Carlo simulation research. Implemented.
- Phase 9: graph neural network experiments. Implemented.
- Advanced mode: orbital simulation, model evidence, findings, and Docker frontend/API orchestration. Implemented.
