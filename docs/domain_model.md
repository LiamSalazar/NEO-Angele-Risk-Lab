# Domain Model

Neo Angele Risk Lab has a dedicated domain layer under `src/neo_ange/domain`. Its purpose is to translate processed NASA/JPL data into objects that carry domain meaning instead of leaving every layer to work directly with loose table columns.

## Three Class Levels

The documentation separates three object-oriented levels:

- Pure domain entities and value objects: concepts from the NEO problem space, such as `Asteroid`, `AsteroidIdentity`, `Orbit`, `PhysicalProperties`, `CloseApproach`, `CloseApproachSummary`, and `SentryRiskSignal`.
- Analytical result objects: outputs derived from scoring, simulation, graph, model-evidence, and findings workflows, such as `RiskScore`, `MonteCarloResult`, `OrbitalGraph`, `ModelCard`, `PredictionRecord`, and `AnalyticalFinding`.
- Process and system classes: factories, repositories, scorers, simulation engines, graph builders, evidence builders, clients, storage adapters, and pipelines.

These levels are related, but they are not the same kind of abstraction. `Asteroid` represents a near-Earth object. `RiskScorer` represents a scoring process. `AsteroidFactory` represents a mapping rule from rows to objects. `GoldFeatureRepository` represents a read adapter over processed artifacts.

## Data Flow

The domain flow is:

```text
NASA/JPL API JSON
-> bronze raw record
-> silver normalized tables
-> gold analytical rows
-> AsteroidFactory
-> domain entities
-> analytical services
-> API, frontend, and reports
```

The tabular layers remain important because Spark and Pandas are efficient for large transformations. The domain layer is used where a conceptual object model improves readability, serialization, scoring, API access, reports, and tests.

## Aggregate Root

`Asteroid` is the aggregate root for the core NEO concept. It owns the coherent object view assembled from:

- `AsteroidIdentity`
- `Orbit`
- `PhysicalProperties`
- optional `CloseApproachSummary`
- optional `SentryRiskSignal`

It exposes behavior through `object_key()`, `display_name()`, `has_risk_relevant_data()`, `to_feature_dict()`, and `to_dict()`. This keeps lookup, display, feature flattening, and nested serialization close to the aggregate instead of scattering those rules across services.

## Value Objects

`Orbit`, `PhysicalProperties`, `CloseApproachSummary`, and `SentryRiskSignal` are value-oriented domain objects. They group related values and expose small pieces of domain behavior:

- `Orbit` calculates orbital vectors, proximity indicators, and uncertainty indicators.
- `PhysicalProperties` calculates size indicators and detects whether size information exists.
- `CloseApproachSummary` summarizes CAD-derived context and computes an approach priority indicator.
- `SentryRiskSignal` summarizes Sentry fields and computes a Sentry priority indicator.

`CloseApproachSummary` does not own a list of `CloseApproach` records in the current code. Its relationship to `CloseApproach` is therefore conceptual dependency, not strong composition.

## Analytical Output Entities

The project also models major analytical outputs:

- `RiskScore` stores score components, category, version, and scoring time.
- `RiskExplanation` stores explanation text, drivers, protective factors, and data limitations.
- `MonteCarloResult` summarizes score stability under input perturbation.
- `OrbitalSimulationResult` summarizes clone-based orbital scenario outputs.
- `OrbitalGraph`, `OrbitalGraphNode`, and `OrbitalSimilarityEdge` describe orbital similarity neighborhoods.
- `ModelCard` and `PredictionRecord` describe secondary model evidence.
- `AnalyticalFinding` stores presentation-ready conclusions.

Most of these outputs are associated with objects through `object_key`, not by directly owning an `Asteroid` instance.

## Factories and Repositories

`AsteroidFactory` maps processed rows into domain objects. Repositories use it but do not own it as part of their state:

- `GoldFeatureRepository ..> AsteroidFactory`
- `RiskScoreRepository ..> AsteroidFactory`
- `SimulationResultRepository ..> AsteroidFactory`

This is a dependency, not composition. The repositories isolate Parquet access and return domain objects. The factory centralizes row-to-object transformation.

## Diagrams

- [Entity class diagram](diagrams/class_diagram_entities.mmd)
- [System class diagram](diagrams/class_diagram_system.mmd)
- [README summary class diagram](diagrams/class_diagram_readme_summary.mmd)
- [Object-oriented design document](object_oriented_design.md)

The entity class diagram is the pure domain diagram. It contains only `Asteroid`, `AsteroidIdentity`, `Orbit`, `PhysicalProperties`, `CloseApproach`, `CloseApproachSummary`, and `SentryRiskSignal`. Analytical results and process/system classes are documented separately.

## Limitations

The model is intentionally hybrid. Spark and Pandas still handle bulk transformation. Some analytical outputs are dataclasses or DTO-style records rather than entities persisted in a relational database. This is appropriate for the current architecture because the project is a local data lab, not a transactional domain application.
