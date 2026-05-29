# Domain model

The project now has a dedicated domain layer under `src/neo_ange/domain`.

## Entity boundaries

- Entities represent real NEO concepts: asteroid identity, orbit, physical properties, close approach
  context, Sentry signal, risk score, Monte Carlo stability, and orbital graph structure.
- Services can accept existing `dict` or `DataFrame` rows for compatibility, but domain factories convert
  processed rows into richer objects when domain behavior is useful.
- Pipelines remain orchestration code: they load data, call services, persist outputs, and save manifests.
- Repositories are read-only adapters for processed Parquet data.

## Flow

`gold row -> Asteroid -> RiskScore / RiskExplanation -> MonteCarloResult -> OrbitalGraph`

This keeps the domain model independent from Spark, FastAPI, and CLI details while still allowing those
layers to serialize objects cleanly.
