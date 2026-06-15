# Object-Oriented Design

## 1. Purpose

Neo Angele Risk Lab uses object-oriented design to make the Near-Earth Object domain explicit. The project still uses dataframe and Parquet processing for efficient analytics, but the domain layer gives names and behavior to the concepts that the API, reports, ranking, simulations, and documentation interpret.

The goal is not to wrap every column in a class. The goal is to represent a NEO as an aggregate with identity, orbit, physical properties, close-approach context, and Sentry signals.

## 2. From NASA/JPL records to domain objects

NASA/JPL data arrives as JSON responses and tabular records from SBDB, CAD, and Sentry APIs. The bronze layer stores raw wrapped payloads. The silver layer normalizes source-specific fields, including SBDB object details, CAD close approaches, and Sentry records. The gold layer builds analytical rows used by scoring, ML, GNN, simulation, and API workflows.

`AsteroidFactory` is the boundary between analytical rows and domain objects. It converts gold or risk-score rows into an `Asteroid` aggregate and its component objects while preserving the existing flattened feature contract.

## 3. Pure domain model

The pure domain model is:

```text
Asteroid
|-- AsteroidIdentity
|-- Orbit / OrbitalElements
|-- PhysicalProperties
|-- CloseApproachHistory
|   `-- CloseApproach
|-- CloseApproachSummary
`-- SentryRiskSignal
```

`Orbit` is the concrete class name used by the codebase. `OrbitalElements` is a conceptual alias for documentation and import clarity.

## 4. Asteroid as aggregate root

`Asteroid` is the aggregate root because it represents one NEO as the rest of the system understands it. It exposes stable behaviors such as `object_key()`, `display_name()`, `has_risk_relevant_data()`, `to_feature_dict()`, and `to_dict()`.

The aggregate owns references to component objects and decides how to export flattened features without exposing callers to the internal composition. This preserves compatibility with scoring, frontend, reports, ML, GNN, and simulations.

## 5. Value objects and domain components

`AsteroidIdentity` is separated from `Asteroid` because identifiers have their own rules. The best stable key and display name are not always the same field, and the priority order is domain behavior rather than raw storage.

`Orbit` is separated because orbital elements and observation-quality metadata have their own behavior: minimum orbital completeness, fixed-width orbital vectors, MOID proximity signals, and uncertainty indicators.

`PhysicalProperties` is separated because size-related evidence may come from direct diameter, logarithmic diameter, albedo, or absolute magnitude. It encapsulates size availability and size-priority signals.

`SentryRiskSignal` is separated because Sentry evidence is optional and has specialized behavior around impact probability, Palermo/Torino scales, and virtual impact counts.

## 6. CloseApproachHistory and CloseApproachSummary

`CloseApproachHistory` models the real CAD relationship: one object can have many close-approach records. It contains `CloseApproach` objects and can answer domain questions such as count, closest approach, fastest approach, next known approach, and summary derivation.

`CloseApproachSummary` remains in the model because it is the stable analytical view already used by risk scoring, API responses, reports, frontend panels, and simulations. When detailed CAD records are available, `CloseApproachHistory.summarize()` can derive a `CloseApproachSummary`. When the gold dataset only contains aggregate fields, `AsteroidFactory` keeps using `CloseApproachSummary` directly and leaves `close_approach_history` as `None`.

This keeps the current outputs stable while preparing the domain model for richer CAD detail.

## 7. Protocols and interfaces

`src/neo_ange/domain/protocols.py` defines structural contracts:

- `SerializableDomainObject`
- `FeatureExportable`
- `IdentifiableDomainObject`
- `Summarizable`
- `RiskScoringStrategy`
- `SimulationStrategy`

These protocols document behavior without requiring artificial inheritance. The project intentionally avoids base classes for every domain object because structural typing is enough for the current coupling points and keeps existing classes simple.

## 8. Factories

Factories are not domain entities. `AsteroidFactory` is an application boundary that translates gold, risk, and simulation records into domain objects. It handles missing values, type coercion, optional Sentry data, aggregate close-approach summaries, and detailed close-approach histories when present.

## 9. Repositories

Repositories are infrastructure-facing readers. `GoldFeatureRepository`, `RiskScoreRepository`, and `SimulationResultRepository` load Parquet outputs and return domain entities or analytical result objects. They isolate storage layout from callers and preserve the public data paths.

## 10. Domain services and process classes

Scorers, simulations, graph builders, model-evidence builders, pipelines, API clients, and findings builders are process or application classes. They use domain objects and domain concepts, but they are not pure entities because they coordinate workflows, IO, batch processing, or external systems.

This distinction keeps the pure domain diagram small and prevents mixing NEO concepts with orchestration mechanics.

## 11. Analytical result objects

Objects such as `RiskScore`, `RiskExplanation`, `MonteCarloResult`, `SimulationScenario`, `OrbitalGraph`, `OrbitalGraphNode`, `OrbitalSimilarityEdge`, and `GNNExperimentResult` represent analytical outputs or experiment structures. They are important domain-adjacent objects, but they are documented separately from the pure asteroid aggregate because they describe computations over the domain rather than the NEO itself.

## 12. UML diagrams

Diagram sources:

- Pure domain entities: [`docs/diagrams/class_diagram_entities.mmd`](diagrams/class_diagram_entities.mmd)
- Domain contracts: [`docs/diagrams/class_diagram_domain_contracts.mmd`](diagrams/class_diagram_domain_contracts.mmd)
- README summary: [`docs/diagrams/class_diagram_readme_summary.mmd`](diagrams/class_diagram_readme_summary.mmd)
- System architecture classes: [`docs/diagrams/class_diagram_system.mmd`](diagrams/class_diagram_system.mmd)

The pure entity diagram intentionally excludes factories, repositories, scorers, simulations, builders, pipelines, API clients, ML/GNN classes, evidence, and findings.

## 13. Design benefits

This architecture improves testability because each component has focused behavior that can be tested without running the full ETL or API stack. It improves extensibility because richer CAD histories, alternate scoring strategies, and simulation engines can be added behind existing contracts. It improves traceability because the path from NASA/JPL records to domain concepts and analytical outputs is explicit.

The model also improves presentation quality: a reviewer can see aggregate root, value objects, domain components, protocols, factories, repositories, and process classes as separate responsibilities.

## 14. Limitations

The current gold dataset stores close-approach aggregates for scoring efficiency. It does not always preserve multiple CAD records per object in the domain construction path. `CloseApproachHistory` is therefore populated when detailed close-approach records or a serialized `close_approaches` collection are available, and `CloseApproachSummary` remains the compatibility path for existing gold rows.

The project uses protocols instead of a shared domain base-class hierarchy. This is intentional: the current model benefits more from structural contracts than from inheritance that would add coupling without adding behavior.
