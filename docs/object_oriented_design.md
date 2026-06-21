# Object-Oriented Design

## Purpose

Neo Angele Risk Lab uses object-oriented design to make the Near-Earth Object domain explicit without replacing the dataframe pipeline that makes ingestion, scoring, ML, GNN, and reporting efficient.

The goal is not to wrap every CSV or Parquet column in a class. NASA/JPL sources arrive as heterogeneous JSON payloads and tabular records from SBDB, CAD, and Sentry APIs. The project first preserves raw data in bronze, normalizes source-specific structures in silver, and builds analytical gold rows. `AsteroidFactory` then translates those rows into domain objects that represent real NEO concepts.

## From NASA/JPL records to domain objects

The data path is:

```text
NASA/JPL APIs
-> bronze raw wrappers
-> silver source-normalized tables
-> gold analytical features
-> AsteroidFactory
-> Asteroid aggregate and component objects
```

The factory boundary is important. It lets the project keep vectorized Parquet and pandas/Spark operations for batch work while still exposing a coherent domain model to the API, documentation, object profile views, and future extension points.

## Pure domain model

The pure domain model is intentionally small:

```text
Asteroid
|-- AsteroidIdentity
|-- Orbit
|-- PhysicalProperties
|-- CloseApproachHistory
|   `-- CloseApproach
|-- CloseApproachSummary
`-- SentryRiskSignal
```

`Orbit` is the concrete class name in the codebase. `OrbitalElements` is only a documentation/import alias defined in `src/neo_ange/domain/orbit.py`.

Pure entity source files:

- `src/neo_ange/domain/asteroid.py`
- `src/neo_ange/domain/identity.py`
- `src/neo_ange/domain/orbit.py`
- `src/neo_ange/domain/physical.py`
- `src/neo_ange/domain/approach.py`
- `src/neo_ange/domain/sentry.py`

## Asteroid as aggregate root

`Asteroid` is the aggregate root because it represents one NEO as the rest of the system interprets it. It owns references to identity, orbit, physical properties, close-approach context, optional Sentry signal, and source flags.

Main methods:

- `object_key()` delegates to `AsteroidIdentity.best_identifier()`.
- `display_name()` delegates to `AsteroidIdentity.display_name()`.
- `has_risk_relevant_data()` checks whether any orbit, physical, approach, Sentry, `neo`, or `pha` data is available.
- `to_feature_dict()` exports a flattened feature representation compatible with scoring, reports, API, ML, GNN, and simulations.
- `to_dict()` exports the nested domain representation.

## Identity separation

`AsteroidIdentity` is separate from `Asteroid` because an object can have several identifiers and labels. NASA/JPL records can contain `spkid`, `des`, `full_name`, `name`, and a local `object_key`. The "best lookup key" and the "best display label" are domain rules, not raw storage details.

`best_identifier()` chooses the first available stable identifier in priority order. `display_name()` prefers the most readable label for UI and reports.

## Orbit and physical value objects

`Orbit` owns classical orbital elements and observation-quality metadata:

- elements: `e`, `a`, `q`, `i`, `om`, `w`, `ma`, `n`, `per`, `ad`;
- proximity fields: `moid`, `moid_ld`;
- quality fields: `condition_code`, `arc_length`, `n_obs_used`, `rms`.

Its methods check minimum data completeness, export a fixed-width vector, compute a bounded proximity indicator, and compute an uncertainty indicator from orbit-quality fields.

`PhysicalProperties` owns `h`, `diameter`, `albedo`, and `log_diameter`. It exposes size availability and a bounded size indicator that uses diameter first, then log diameter, then absolute magnitude.

## CloseApproachHistory and CloseApproachSummary

`CloseApproachHistory` models the real CAD relationship: one object can have many close-approach records. It can count records, select the closest approach, select the fastest approach, select the next comparable approach date, and derive a `CloseApproachSummary`.

`CloseApproachSummary` remains in the model because it is the stable analytical contract used by scoring, API responses, reports, frontend panels, and current gold rows. It carries:

- `min_close_approach_dist`
- `min_close_approach_dist_min`
- `max_close_approach_v_rel`
- `next_close_approach_datetime`
- `close_approach_count`

When detailed CAD records are available, `CloseApproachHistory.summarize()` can derive the summary. When gold only stores aggregates, `AsteroidFactory` sets the summary directly and leaves `close_approach_history` absent.

## SentryRiskSignal

`SentryRiskSignal` is optional because Sentry coverage is sparse. It contains `sentry_flag`, `sentry_ip`, `sentry_ps_cum`, `sentry_ps_max`, `sentry_ts_max`, and `sentry_n_imp`.

`has_sentry_signal()` checks explicit or numeric Sentry evidence. `sentry_priority_indicator()` combines Sentry fields into a bounded indicator used for interpretation, not as an official impact probability.

## Protocols and interfaces

`src/neo_ange/domain/protocols.py` defines structural contracts:

- `SerializableDomainObject`: requires `to_dict()`.
- `FeatureExportable`: requires `to_feature_dict()`.
- `IdentifiableDomainObject`: requires `object_key()` and `display_name()`.
- `Summarizable`: requires `summarize()`.
- `RiskScoringStrategy`: requires `score_row()` and `score_dataframe()`.
- `SimulationStrategy`: requires `simulate_object()`.

The project uses protocols instead of a shared base-class hierarchy because structural typing documents expectations without forcing artificial inheritance across simple dataclasses.

## Factories and repositories

Factories and repositories are not pure domain entities.

`AsteroidFactory` in `src/neo_ange/domain/factories.py` is an application boundary. It handles missing values, type coercion, optional Sentry fields, aggregate close-approach summaries, detailed close-approach histories when present, risk-score objects, and simulation result objects.

Repositories in `src/neo_ange/domain/repositories.py` read Parquet/report outputs and return domain or analytical objects:

- `GoldFeatureRepository`
- `RiskScoreRepository`
- `SimulationResultRepository`

These classes isolate storage layout from callers.

## Process and infrastructure classes

Process classes coordinate workflows. They are domain-aware, but they are not pure domain entities:

- scoring: `RiskScorer`, `RiskRankingService`, `RiskExplanationService`, `RiskPipeline`;
- score simulation: `MonteCarloEngine`, `PerturbationEngine`, `SensitivityAnalyzer`;
- orbital simulation: `OrbitalMonteCarloEngine`, `OrbitalSimulationService`;
- ML/evidence: `BaselineExperimentRunner`, `ModelEvidenceBuilder`;
- GNN: `OrbitalGraphBuilder`, `OrbitalSimilarityCalculator`, `GNNExperimentRunner`, `GNNTrainer`;
- findings: `FindingsBuilder`.

Infrastructure classes connect to external or storage systems:

- clients: `SBDBObjectClient`, `SBDBQueryClient`, `CloseApproachClient`, `SentryClient`;
- ETL: `BronzeReader`, `SilverTransformers`, `GoldBuilder`, `ETLPipeline`;
- API: FastAPI routers under `src/neo_ange/api/routers/`.

## Analytical result objects

Objects such as `RiskScore`, `RiskExplanation`, `SimulationScenario`, `MonteCarloResult`, `OrbitalSimulationResult`, `OrbitalGraph`, `OrbitalGraphNode`, `OrbitalSimilarityEdge`, `GNNExperimentResult`, `ModelCard`, `PredictionRecord`, and findings payloads represent results of computations over the domain.

They are intentionally excluded from the pure entity diagram because they describe analyses, experiments, or report records rather than the NEO aggregate itself.

## UML diagrams

Diagram sources:

- Pure domain entities: [`docs/diagrams/class_diagram_entities.mmd`](diagrams/class_diagram_entities.mmd)
- Domain contracts: [`docs/diagrams/class_diagram_domain_contracts.mmd`](diagrams/class_diagram_domain_contracts.mmd)
- System architecture classes: [`docs/diagrams/class_diagram_system.mmd`](diagrams/class_diagram_system.mmd)
- README summary: [`docs/diagrams/class_diagram_readme_summary.mmd`](diagrams/class_diagram_readme_summary.mmd)

The pure entity diagram intentionally excludes factories, repositories, scorers, simulations, builders, pipelines, API clients, ML/GNN classes, evidence builders, findings builders, and analytical result objects.

## Design benefits

This design gives the project three useful boundaries:

- Domain: stable NEO concepts and behavior.
- Process: scoring, simulation, graph, evidence, findings, and orchestration.
- Infrastructure: APIs, storage, reports, Docker, and FastAPI.

The separation improves reviewability because a reader can see which classes represent the problem domain and which classes operate on the domain. It also keeps batch analytics efficient: the pipeline remains tabular where vectorized processing is the right tool, while POO is used for interpretation, API representation, documentation, and extensibility.

## Limitations

The current gold table stores close-approach aggregates for scoring efficiency. It does not always preserve every CAD row in the domain construction path. `CloseApproachHistory` is therefore populated when detailed close-approach records or a serialized `close_approaches` collection are available; otherwise `CloseApproachSummary` is the compatibility path.

The model uses structural protocols rather than a deep inheritance tree. This is intentional and keeps the simple value objects decoupled.

The domain model does not claim to be an official astronomical object model. It is an engineering model for this repository's ingestion, scoring, simulation, evidence, API, and presentation workflows.
