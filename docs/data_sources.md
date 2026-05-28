# Data Sources

Neo Angele Risk Lab currently uses public JSON endpoints from NASA/JPL SSD and CNEOS. These endpoints do not require API keys.

## SBDB Object API

- Base endpoint: `https://ssd-api.jpl.nasa.gov/sbdb.api`
- Purpose: object-level data for a specified asteroid or comet.
- Key selector params: `sstr`, `spk`, `des`.
- Useful flags: `phys-par`, `ca-data`, `vi-data`, `cov`, `full-prec`.

The ingestion client uses this endpoint for object-specific samples and richer future-ready payloads that preserve physical parameters, close approach summaries, virtual impactor data, ancillary data, and covariance outputs when requested.

## SBDB Query API

- Base endpoint: `https://ssd-api.jpl.nasa.gov/sbdb_query.api`
- Purpose: query sets of asteroids and comets.
- Useful params: `fields`, `limit`, `limit-from`, `full-prec`, `sort`.

The current NEO sample uses `sb-group=neo` from the common SBDB filter parameters and requests a compact set of object, physical, and orbital fields.

## Close Approach Data API

- Base endpoint: `https://ssd-api.jpl.nasa.gov/cad.api`
- Purpose: close approach data for asteroids and comets.
- Useful params: `date-min`, `date-max`, `dist-max`, `body`, `neo`, `pha`, `des`, `spk`, `limit`, `sort`, `diameter`, `fullname`.

The current sample defaults to near-term Earth approaches and supports explicit date windows. Relative windows such as `date-max=+60` are passed as query params so the plus sign is encoded correctly.

## Sentry API

- Base endpoint: `https://ssd-api.jpl.nasa.gov/sentry.api`
- Purpose: CNEOS Sentry impact risk results.
- Modes:
  - Summary mode when no selector is passed.
  - Object mode with `des` or `spk`.
  - Virtual impactor mode with `all=1`.
  - Removed objects mode with `removed=1`.

The Sentry client keeps these modes separate and avoids combining incompatible selectors.

## Downstream Normalization Notes

The Spark ETL layer reads all source responses through the bronze wrapper format. SBDB Object payloads are normalized by extracting object metadata, physical parameters, and orbital elements. CAD payloads are normalized from the API `fields` plus `data` tabular shape. Sentry summary and virtual impactor payloads are processed defensively because their modes expose different fields.

Missing optional fields are kept as nulls in silver and gold outputs rather than failing the pipeline.
