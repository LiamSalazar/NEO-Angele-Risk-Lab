# Model Evidence

Model evidence is secondary support for the observatory. The product centers on risk scoring, simulations, graph neighborhoods, and findings; ML/GNN outputs are used to explain whether available patterns are internally consistent.

## Artifacts

- `reports/model_evidence/model_evidence_summary.json`
- `reports/model_evidence/model_evidence_summary.md`
- `reports/model_evidence/model_cards.json`
- `reports/model_evidence/model_predictions_eval.csv`
- `reports/model_evidence/model_predictions_eval.parquet`
- `reports/model_evidence/model_predictions_full.csv`
- `reports/model_evidence/model_predictions_full.parquet`
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

## Evaluation vs Full Inference

Evaluation and inference are separate artifacts. The eval files are produced from the holdout test split and are the source for accuracy, precision, recall, F1, ROC-AUC, PR-AUC, and false-negative-rate metrics. The full files are produced after that honest evaluation step by refitting the selected tabular evidence models on the active labeled dataset and predicting every active `object_key`.

`model_predictions.csv` and `model_predictions.parquet` are retained for compatibility and mirror the full inference outputs. API and frontend consumers should use the full inference view by default, or pass `mode=eval` when they explicitly need holdout rows.

## CLI

```bash
python -m neo_ange.cli model-evidence build
python -m neo_ange.cli model-evidence status
```
