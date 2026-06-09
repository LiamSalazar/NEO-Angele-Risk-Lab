# Object-Oriented Design

## 1. Purpose

The object-oriented design in Neo Angele Risk Lab converts astronomical and analytical data into objects with explicit meaning. NASA/JPL APIs expose valuable records, but those records arrive as JSON payloads, nested fields, and tabular columns. The project uses classes to name the relevant concepts, group related values, and keep behavior close to the data it interprets.

The design is intentionally split into three levels. The pure domain model describes the NEO itself. Analytical result objects describe outputs derived from that domain. Process and system classes describe how data is loaded, transformed, scored, simulated, compared, and reported.

## 2. From API Data to Domain Model

The conceptual flow is:

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

The first part of the flow is data-engineering oriented. API clients retrieve SBDB Object, SBDB Query, CAD, and Sentry payloads. `BronzeStorage` wraps raw responses with metadata. `BronzeReader` and `SilverTransformers` normalize the records into silver tables. `GoldBuilder` joins and enriches those tables into `data/gold/neo_risk_features`.

The second part of the flow is object-oriented. `AsteroidFactory` reads processed rows and builds pure domain objects. Analytical services such as `RiskScorer`, `MonteCarloEngine`, `OrbitalSimulationService`, `OrbitalGraphBuilder`, `ModelEvidenceBuilder`, and `FindingsBuilder` then operate over rows, domain objects, and generated artifacts while keeping their responsibilities separate.

## Pure domain model

The PNG integrated in the README is the pure domain class diagram. It corresponds to the source Mermaid file at [`diagrams/class_diagram_entities.mmd`](diagrams/class_diagram_entities.mmd) and is rendered as:

![Pure domain class diagram](../artifacts/figures/class_diagram_entities.png)

This diagram focuses only on the domain abstraction: the NEO aggregate and its component value objects. It shows `Asteroid` as the aggregate root, with `AsteroidIdentity`, `Orbit`, `PhysicalProperties`, optional `CloseApproachSummary`, and optional `SentryRiskSignal` as the object model used to interpret NASA/JPL records.

`CloseApproachSummary` is related to `CloseApproach` through a conceptual dependency because it summarizes CAD-derived records. The current code does not store a list of `CloseApproach` instances inside the summary, so the UML relationship is not strong composition.

The complete system view is intentionally separate in the [System class diagram](diagrams/class_diagram_system.mmd). That diagram covers analytical results and process/infrastructure classes: factories, repositories, scoring services, simulations, ML/GNN components, findings, API clients, storage adapters, and pipelines. Keeping these concerns separate makes it clear which classes represent the pure domain and which classes execute or report on the workflow.

## 3. Pure Domain Object Reference

### Asteroid

`Asteroid` represents the coherent NEO aggregate used by the project. It comes from gold feature rows produced after NASA/JPL records are normalized and joined. Its main attributes are `identity`, `orbit`, `physical`, optional `close_approach_summary`, optional `sentry_signal`, `neo`, and `pha`.

Its methods are domain-facing:

- `object_key()` returns the stable lookup key.
- `display_name()` returns the human-readable label.
- `has_risk_relevant_data()` checks whether any relevant domain area is populated.
- `to_feature_dict()` flattens nested objects for scoring and modeling.
- `to_dict()` serializes the aggregate without losing the nested structure.

It composes `AsteroidIdentity`, `Orbit`, and `PhysicalProperties`, and aggregates optional `CloseApproachSummary` and `SentryRiskSignal`.

### AsteroidIdentity

`AsteroidIdentity` represents names and identifiers from SBDB-derived data. Its attributes include `object_key`, `spkid`, `des`, `full_name`, `name`, `orbit_class_code`, and `orbit_class_name`.

It encapsulates identifier behavior through `best_identifier()`, `display_name()`, and `to_dict()`. Other analytical outputs usually reference an asteroid by `object_key` instead of owning an `Asteroid` object.

### Orbit

`Orbit` represents orbital elements and uncertainty-related signals. It is built from fields such as `e`, `a`, `q`, `i`, `om`, `w`, `ma`, `n`, `per`, `ad`, `moid`, `moid_ld`, `condition_code`, `arc_length`, `n_obs_used`, and `rms`.

Its behavior includes `has_minimum_orbital_data()`, `orbital_vector()`, `proximity_indicator()`, `uncertainty_indicator()`, and `to_dict()`. `RiskScorer`, `OrbitalSimulationResult`, and graph-related outputs depend conceptually on this orbital state.

### PhysicalProperties

`PhysicalProperties` represents physical signals such as absolute magnitude, diameter, albedo, and logarithmic diameter. It is built from SBDB-derived and gold-derived columns: `h`, `diameter`, `albedo`, and `log_diameter`.

Its methods are `size_indicator()`, `has_size_information()`, and `to_dict()`. It is a value object inside `Asteroid`.

### CloseApproach

`CloseApproach` represents one close-approach record with `close_approach_datetime`, `dist`, `dist_min`, `dist_max`, `v_rel`, `v_inf`, and `body`. It comes from CAD-style records. It exposes `distance_indicator()`, `velocity_indicator()`, and `to_dict()`.

The current aggregate does not store a list of `CloseApproach` objects. This matters for UML: `CloseApproachSummary` depends on CAD records conceptually, but it does not strongly compose `CloseApproach`.

### CloseApproachSummary

`CloseApproachSummary` represents the reduced close-approach context used by scoring and display. Its attributes include `min_close_approach_dist`, `min_close_approach_dist_min`, `max_close_approach_v_rel`, `next_close_approach_datetime`, and `close_approach_count`.

Its methods are `has_close_approach_data()`, `approach_priority_indicator()`, and `to_dict()`. It is optional inside `Asteroid` because not every row has close-approach context.

### SentryRiskSignal

`SentryRiskSignal` represents Sentry-derived signals when they are available. It includes `sentry_flag`, `sentry_ip`, `sentry_ps_cum`, `sentry_ps_max`, `sentry_ts_max`, and `sentry_n_imp`.

Its methods are `has_sentry_signal()`, `sentry_priority_indicator()`, and `to_dict()`. It is optional inside `Asteroid`. Missing Sentry data means no Sentry signal is available in the row; it does not mean zero official risk.

## Analytical result objects

Analytical result objects are separate from the pure domain model. They describe outputs produced after the NEO domain objects and tabular features have been scored, simulated, modeled, compared, or summarized. They are not shown in the pure domain class diagram because they do not define the NEO abstraction itself.

Classes such as `RiskScore`, `RiskExplanation`, `SimulationScenario`, `MonteCarloResult`, `OrbitalSimulationResult`, `ModelCard`, `PredictionRecord`, `AnalyticalFinding`, `OrbitalGraph`, and `GNNExperimentResult` belong to this analytical-output level. Most of them reference an asteroid by `object_key` instead of owning an `Asteroid` instance. This keeps the domain model focused while still documenting the result objects used by the application, reports, and API.

### RiskScore

`RiskScore` represents the analytical priority score produced by the lab. It stores `object_key`, raw and 0-100 score values, risk category, six component scores, score version, and scoring time.

Its methods are `component_breakdown()`, `dominant_components(top_n)`, and `to_dict()`. It references objects by `object_key`, so its relationship to `Asteroid` is a dependency, not composition.

### RiskExplanation

`RiskExplanation` represents an explanatory output: score, category, main drivers, protective factors, data limitations, short explanation, and technical explanation. The current `RiskExplanationService` returns dictionaries with this shape, while the dataclass documents the structured result entity.

It is associated with `RiskScore` because it explains a scored object.

### SimulationScenario

`SimulationScenario` represents a perturbed score scenario with `object_key`, `simulation_id`, `perturbed_values`, `risk_score_0_100`, and `risk_category`. It captures one possible score state generated during perturbation workflows.

It depends on the scoring context rather than owning the scored asteroid.

### MonteCarloResult

`MonteCarloResult` represents the score simulation summary for one object. It stores the number of simulations, base score, mean, standard deviation, percentiles, max score, threshold probabilities, category-shift probability, base category, p95 category, and simulation version.

Its methods are `stability_summary()` and `to_dict()`. It is associated with `RiskScore` by `object_key`.

### OrbitalSimulationResult

`OrbitalSimulationResult` represents clone-based approximate orbital scenario output. It comes from `OrbitalMonteCarloEngine` and includes clone counts, horizon settings, baseline and simulated minimum distances, closest-approach day statistics, dispersion index, orbital uncertainty score, scenario category, covariance availability, simulation method, fallback reason, propagator, CAD validation fields, warnings, simulation time, designation, score context, and version.

It depends conceptually on `Orbit` because it simulates orbital state. It may also carry `risk_score_0_100` and `risk_category` as context.

### OrbitalGraph

`OrbitalGraph` represents the graph artifact used by the GNN lab. It owns `nodes`, `edges`, and `graph_version`. It exposes `node_count()`, `edge_count()`, `density()`, `to_networkx()`, and `to_dict()`.

`OrbitalGraphNode` stores node id, object key, numeric feature dictionary, label, score, and category. `OrbitalSimilarityEdge` stores source node id, target node id, similarity, distance, and edge type. `OrbitalGraph` strongly composes nodes and edges because they are stored as lists inside the graph object.

### ModelCard

`ModelCard` represents model-evidence metadata: model name, model family, feature set, target, metrics, strengths, weaknesses, leakage risk, recommended use, not recommended use, interpretation, and status.

It is an analytical output entity, not the ranking source. Models provide secondary evidence and diagnostic context.

### PredictionRecord

`PredictionRecord` represents one model prediction row. It includes object key, designation, actual label, predicted label, probability, model metadata, correctness, confidence bucket, score context, notes, and optional graph-context fields.

It depends on `ModelCard` through model context and on `RiskScore` through score fields.

### AnalyticalFinding

`AnalyticalFinding` represents a presentation-ready conclusion. Its attributes include title, short text, technical basis, related objects, importance, source module, values, and caveat.

Findings can reference risk scores, simulations, graph outputs, and model evidence, but they do not own those artifacts.

## 4. Aggregate Root

`Asteroid` is the aggregate root because it is the main object through which the project represents a NEO. It groups identity, orbit, physical properties, close-approach summary, and Sentry signal into one coherent object. This avoids spreading the definition of an asteroid across unrelated dictionaries.

The aggregate root is also responsible for safe boundary behavior:

- Stable lookup through `object_key()`.
- User-facing naming through `display_name()`.
- Completeness checks through `has_risk_relevant_data()`.
- Flattening for scoring and modeling through `to_feature_dict()`.
- Nested serialization through `to_dict()`.

This makes the domain model understandable even though the data pipeline remains tabular internally.

## 5. Value Objects

The project uses value objects to group related signals that do not need independent lifecycle management. `Orbit`, `PhysicalProperties`, `CloseApproachSummary`, and `SentryRiskSignal` are good examples.

They are not services and they are not pipeline phases. They represent meaningful slices of the NEO domain:

- Orbital geometry and uncertainty.
- Size and brightness.
- Close-approach context.
- Sentry-related signal.

Their methods calculate indicators and serialization output from their own values. This is encapsulation: behavior lives with the data it interprets.

## 6. Factories

`AsteroidFactory` translates processed tabular rows into objects. It builds:

- `Asteroid` from gold rows.
- `(Asteroid, RiskScore | None)` from risk rows.
- lists of asteroids from DataFrames.
- `RiskScore` from scored rows.
- `MonteCarloResult` from simulation result dictionaries.

This avoids duplicating row-cleaning and conversion rules in repositories, API routers, or services. It also makes the mapping from NASA/JPL-derived fields to object-oriented concepts explicit.

The factory relationship is a dependency. Repositories call `AsteroidFactory` methods, but they do not hold a factory instance as part of their state.

## 7. Repositories

The domain repositories isolate processed artifact access:

- `GoldFeatureRepository` reads `data/gold/neo_risk_features` and returns `Asteroid` objects.
- `RiskScoreRepository` reads `data/gold/risk_scores` and returns `RiskScore` objects.
- `SimulationResultRepository` reads `data/gold/simulation_results` and returns `MonteCarloResult` objects.

This shields callers from path details and Parquet layout. It also creates a clean seam between file-based persistence and domain-oriented access.

## Process and system classes

Process and system classes express how the project executes the workflow around the domain model. They are not part of the pure domain diagram, but they are part of the complete object-oriented architecture.

`RiskScorer` calculates the Risk Priority Score from gold features or an `Asteroid` aggregate. It owns a `RiskCategoryAssigner`, uses `RiskExplanationService` to build explanatory text, and returns derived score fields.

`MonteCarloEngine` evaluates score stability. It owns `RiskScorer`, `PerturbationEngine`, `SensitivityAnalyzer`, `RiskCategoryAssigner`, and `RiskRankingService`. It perturbs score inputs, recalculates scores, and summarizes score distributions.

`OrbitalSimulationService` coordinates approximate orbital simulations. It owns `OrbitalMonteCarloEngine` and `OrbitalSimulationReportWriter`. The engine itself creates `OrbitalSimulationResult` payloads. Covariance parsing, clone sampling, element extraction, propagation, and metrics are implemented as module functions in `src/neo_ange/orbital_simulation`, not as classes.

`OrbitalGraphBuilder` builds an `OrbitalGraph` from scored objects. It owns an `OrbitalSimilarityCalculator`, builds graph nodes, computes kNN similarity edges, exports graph artifacts, and summarizes graph metrics.

`GNNExperimentRunner` coordinates graph construction, dataset building, baselines, optional `GraphSAGEModel` and `GCNModel` training, and reports. `GraphSAGEModel` and `GCNModel` are conditional classes: when `torch-geometric` is installed they are neural network modules, otherwise placeholders raise an import error.

`ModelEvidenceBuilder` builds model cards, prediction records, disagreements, and evidence summaries. It uses model-validation helpers and prediction functions, but there is no separate `ModelEvidenceReporter` class in the current code.

`FindingsBuilder` reads generated risk, simulation, graph, and evidence artifacts and writes interpretable findings. The specialized dataset, risk, simulation, graph, and model finding entry points are module functions, not separate builder classes.

The ingestion and ETL classes form the lower system layer. `BaseJPLClient` is the actual base client class for `SBDBObjectClient`, `SBDBQueryClient`, `CloseApproachClient`, and `SentryClient`. `BronzeStorage`, `SilverStorage`, and `GoldStorage` isolate storage paths. `IngestionPipeline`, `ETLPipeline`, `RiskPipeline`, `SimulationPipeline`, and `MLPipeline` orchestrate larger workflows and save `RunManifest` records.

## 9. UML Diagrams

- [Pure domain class diagram image](../artifacts/figures/class_diagram_entities.png)
- [Entity class diagram](diagrams/class_diagram_entities.mmd)
- [System class diagram](diagrams/class_diagram_system.mmd)
- [README summary class diagram](diagrams/class_diagram_readme_summary.mmd)

The pure domain diagram contains only the NEO aggregate and its domain component objects. It deliberately excludes analytical result objects, factories, repositories, clients, builders, services, trainers, pipelines, routers, and frontend components.

The system diagram expands the view to include factories, repositories, scoring services, simulations, ML/GNN components, findings, API clients, storage adapters, and pipelines. Those classes are part of the object-oriented system design, but they are process or infrastructure classes rather than pure domain entities.

The system diagram includes process and infrastructure classes and uses UML relationship types carefully:

- `*--` only where a class stores another object as part of its state or lifecycle.
- `o--` for optional aggregate components.
- `..>` for dependency, row mapping, conceptual reference, or artifact reading.
- `-->` for creation, return, or production relationships.
- `<|--` for real inheritance.

## 10. Design Benefits

The design provides:

- Separation of concerns between domain concepts and execution mechanics.
- Encapsulation of identifier, orbital, physical, approach, Sentry, score, and graph behavior.
- Traceability from NASA/JPL API records to gold rows, domain objects, scores, simulations, evidence, findings, API responses, and frontend views.
- Lower coupling because file paths, row mapping, scoring, simulation, graph construction, and reporting are isolated in different classes.
- Reuse across API routes, reports, tests, and documentation.
- Clearer tests because factories, repositories, scoring, simulation, and graph construction can be exercised separately.
- A stronger domain language for explaining the project in a presentation.

## 11. Limitations

The project is intentionally hybrid rather than purely object-oriented.

- A large part of the pipeline remains tabular because Spark and Pandas are the right tools for bulk data processing.
- Domain entities are used mainly for interpretation, API access, reports, documentation, and conceptual access rather than as objects persisted in a relational database.
- Some analytical outputs are dataclasses or DTO-style records, not long-lived entities with independent persistence.
- `RiskExplanationService` currently returns dictionaries shaped like `RiskExplanation` rather than directly instantiating the dataclass.
- Some requested conceptual pieces are implemented as module functions instead of classes. For example, orbital element extraction, covariance parsing, clone sampling, and specialized finding builders are functions in the current code.
- Model evidence is secondary evidence. It supports interpretation and disagreement analysis, but it does not define the Risk Priority Score.
