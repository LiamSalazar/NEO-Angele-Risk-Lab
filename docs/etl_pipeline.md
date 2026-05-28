# Spark ETL Pipeline

## Overview

Neo Angele Risk Lab now supports a local PySpark ETL flow from bronze JSON wrappers to silver Parquet tables and an initial gold feature dataset. The flow is designed for small local portfolio runs today, while keeping table boundaries ready for future ML, simulation, ranking, and service layers.

```text
data/bronze/{source}/ingest_date=*/...json
        |
        v
Spark bronze reader
        |
        v
data/silver/{normalized_table}/
        |
        v
data/gold/neo_risk_features/
        |
        v
data/gold/quality_reports/
```

## Bronze Wrapper Format

Bronze files are JSON wrappers produced by the ingestion layer:

```json
{
  "metadata": {
    "source": "sbdb_object",
    "ingested_at_utc": "2026-05-28T00:00:00+00:00",
    "query_params": {},
    "object_id": "99942",
    "api_signature": {"version": "1.3"}
  },
  "data": {}
}
```

The ETL reader preserves source metadata, query parameters, object IDs, API signatures, ingest dates, and the bronze file path for lineage.

## Silver Tables

- `silver/sbdb_objects/`: normalized SBDB Object records with identifiers, orbital class, physical parameters, orbital elements, MOID fields, and raw payload JSON.
- `silver/close_approaches/`: normalized CAD rows built from the API `fields` plus `data` structure.
- `silver/sentry_objects/`: Sentry summary records with impact probability, Palermo/Torino scale fields, observations, and raw record JSON.
- `silver/sentry_virtual_impactors/`: optional virtual impactor records when available.
- `silver/ingestion_events/`: one event per bronze wrapper for lineage and monitoring.

## Gold Dataset

`gold/neo_risk_features/` is the initial analytical table for future ML, ranking, and simulation phases. It includes object identifiers, classification flags, physical and orbital fields, close approach aggregates, Sentry fields, and simple derived features.

This table is not the final Risk Priority Score. It intentionally contains transparent, conservative proxy features such as inverse MOID, inverse minimum close approach distance, relative velocity score, observation quality score, and feature completeness ratio.

## Quality Checks

Gold quality checks validate:

- required columns;
- non-empty output;
- null ratios for key fields;
- duplicate object keys;
- bounded numeric score ranges.

Reports are written to:

```text
data/gold/quality_reports/neo_risk_features_quality_YYYYMMDDTHHMMSSZ.json
```

Warnings do not stop the pipeline. Empty gold output or missing critical columns produces a failed quality status.

## Known Limitations

- PySpark requires a working Java installation.
- On Windows without Hadoop `winutils.exe`, the writer falls back to PyArrow for local Parquet writes.
- CAD and Sentry joins are best-effort and primarily use designation or SPK IDs when present.
- Derived features are initial engineering signals, not calibrated risk scores.
- The pipeline does not train ML models, serve APIs, run dashboards, run Monte Carlo simulations, or build graph models yet.

## Next Phases

Future phases can build on `neo_risk_features` for baseline ML, leakage audits, transparent scoring, analytical APIs, dashboarding, uncertainty simulation, and graph research.
