# Frontend Observatory

## Visual Concept

The frontend is designed as a technical space-observatory console for Near-Earth Object risk analysis. The interface uses a deep blue-black background, subtle starfield/orbital motion, restrained cyan/green/amber/red risk colors, console panels, telemetry strips and radar-like cues. It avoids generic SaaS dashboard styling and avoids presenting the lab as an official alerting system.

## Pages

- Mission Control: system health, dataset readiness, risk distribution, top objects, telemetry and GNN/simulation status.
- Risk Ranking: searchable and filterable ranked object table.
- Asteroid Profile: object dossier with score gauge, component radar, explanation, domain JSON, latest simulation and graph neighbors.
- Monte Carlo Lab: object simulation controls and score-stability summary.
- ML & Leakage Lab: ML status from manifests, target distribution, baseline/leakage placeholders when metrics are insufficient.
- GNN Research Lab: graph status, graph preview, metrics and neighbor explorer.
- Domain Explorer: POO entity overview and domain aggregate JSON.
- Pipeline Monitor: Bronze/Silver/Gold, readiness, coverage, manifests and next commands.
- Methodology: source framing, score limitations, Monte Carlo limits, leakage and GNN caveats.

## Components

Key components include `OrbitalBackdrop`, `SystemStatusBeacon`, `RiskScoreGauge`, `RiskComponentsRadar`, `MonteCarloHistogram`, `GNNGraphPreview`, `ObjectSearch`, domain/object panels, simulation controls, GNN status and reusable loading/empty/error states.

## Endpoints Used

- Core: `GET /health`, `GET /status`
- Objects/domain: `GET /objects`, `GET /objects/{object_key}`, `GET /domain/objects/{object_key}`
- Rankings: `GET /rankings/top`, `GET /rankings/summary`, `GET /rankings/category/{category}`
- Risk: `POST /risk/build`, `GET /risk/status`, `GET /risk/explain/{object_key}`, `GET /risk/methodology`
- Simulations: `POST /simulations/object`, `POST /simulations/batch`, `GET /simulations/status`, `GET /simulations/object/{object_key}/latest`
- GNN: `GET /gnn/status`, `POST /gnn/build-graph`, `POST /gnn/run`, `GET /gnn/summary`, `GET /gnn/graph`, `GET /gnn/metrics`, `GET /gnn/object/{object_key}/neighbors`

## Limitations

The backend currently exposes ML/leakage status through `/status` manifests rather than a dedicated ML API router, so the ML page renders available manifest telemetry and clear insufficient-data states. GNN real-model results remain optional: if `torch-geometric` is absent, the frontend treats `skipped_missing_dependency` as expected research status.

## Final Phase Remaining

The final phase should handle Docker/Linux hardening, end-to-end reproducibility, final portfolio README, video demo, release packaging and final presentation polish.
