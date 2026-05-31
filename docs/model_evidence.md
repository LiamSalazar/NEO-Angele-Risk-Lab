# Model Evidence

Model evidence is secondary support for the observatory. The product centers on risk scoring, simulations, graph neighborhoods, and findings; ML/GNN outputs are used to explain whether available patterns are internally consistent.

## Artifacts

- `reports/model_evidence/model_evidence_summary.json`
- `reports/model_evidence/model_evidence_summary.md`
- `reports/model_evidence/model_cards.json`
- `reports/model_evidence/model_predictions.csv`
- `reports/model_evidence/model_predictions.parquet`
- `reports/model_evidence/model_disagreements.csv`
- `reports/model_evidence/high_confidence_predictions.csv`
- `reports/model_evidence/low_confidence_predictions.csv`
- `reports/model_evidence/false_positives.csv`
- `reports/model_evidence/false_negatives.csv`

## Evidence Policy

Feature sets such as `full_features`, `definition_features_only`, `risk_score_features`, and `graph_node_features` are leakage-sensitive for PHA interpretation. They remain useful diagnostics, but the best defensible model excludes high-leakage feature sets.

The current evidence builder prefers low-leakage tabular signals for user-facing support and reports GNN readiness or graph metrics separately.

## CLI

```bash
python -m neo_ange.cli model-evidence build
python -m neo_ange.cli model-evidence status
```
