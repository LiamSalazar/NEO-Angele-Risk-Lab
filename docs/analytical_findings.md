# Analytical Findings

The Findings layer turns generated artifacts into concise conclusions for the frontend. It does not create new scientific claims; it summarizes the current gold/risk table, score simulations, orbital simulations, orbital graph, and model-evidence reports.

## Outputs

- `reports/findings/findings_summary.json`
- `reports/findings/findings_summary.md`
- `reports/findings/risk_findings.json`
- `reports/findings/score_simulation_findings.json`
- `reports/findings/orbital_simulation_findings.json`
- `reports/findings/graph_findings.json`
- `reports/findings/model_evidence_findings.json`
- `reports/findings/object_findings_sample.json`

## API

- `GET /findings/summary`
- `GET /findings/risk`
- `GET /findings/score-simulation`
- `GET /findings/orbital-simulation`
- `GET /findings/orbital-graph`
- `GET /findings/model-evidence`
- `GET /findings/object/{object_key}`

## CLI

```bash
python -m neo_ange.cli findings build
python -m neo_ange.cli findings status
```

Findings are intentionally caveated. Risk scores are analytical review priorities, not official impact warnings.
