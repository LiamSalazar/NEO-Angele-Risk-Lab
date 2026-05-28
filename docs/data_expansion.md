# Data Expansion

Data expansion increases the number of SBDB Object payloads available in bronze so the silver and gold layers can support meaningful ML experiments.

## Discovery Strategies

The `ObjectDiscoveryService` searches local data only:

- `silver-cad`: designations from `data/silver/close_approaches/`.
- `silver-sentry`: designations from `data/silver/sentry_objects/` and `data/silver/sentry_virtual_impactors/`.
- `bronze-cad`: designations from raw CAD JSON wrappers when silver is not available.
- `bronze-sentry`: designations from raw Sentry JSON wrappers when silver is not available.
- `curated`: a deterministic seed list for demos and tests.
- `all`: silver first, bronze second, curated fallback last.

Discovery never calls the internet. Missing sources are reported as warnings and do not fail the command.

## Bulk Ingestion

Bulk ingestion uses the existing SBDB Object client and bronze storage service:

```bash
python -m neo_ange.cli expand ingest-objects --strategy curated --limit 10
python -m neo_ange.cli expand ingest-objects --strategy all --limit 100 --skip-existing
```

Each object is attempted independently. A failed API response is recorded in the run summary and does not stop the rest of the batch.

## `skip_existing`

`--skip-existing` checks date-partitioned bronze files under `data/bronze/sbdb_object/` and skips object ids already present. This avoids re-downloading objects during iterative ETL and ML work.

## Manifests

Bulk ingestion writes run manifests under:

```text
reports/manifests/
```

The manifest captures status, inputs, object counts, output paths, warnings, and per-object errors.

## Recommended Limits

Use `--limit 10` for smoke tests and portfolio demos. Use `--limit 100` after CAD/Sentry ingestion and ETL have produced local discovery sources. Larger runs should be staged gradually to remain respectful of public NASA/JPL APIs.

