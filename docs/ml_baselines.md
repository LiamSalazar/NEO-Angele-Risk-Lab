# Baseline ML

The baseline ML layer trains transparent scikit-learn models on `data/gold/neo_risk_features/` when the dataset has enough rows and enough positive PHA examples.

## Target

The default target is `pha`. Boolean labels are converted to integer labels during training. If the target is missing, single-class, too small, or has too few positives, training is skipped and an insufficient-data report is written.

## Models

The baseline runner uses:

- `dummy_most_frequent`
- `logistic_regression` with balanced class weights
- `random_forest` with balanced class weights
- `hist_gradient_boosting` when the dataset is large enough
- `rule_based_pha`, a non-ML baseline using approximately `moid <= 0.05` and `h <= 22`

The rule-based baseline is reported as a definition/leakage reference, not as a general model.

## Feature Sets

Experiments compare:

- `full_features`
- `definition_features_only`
- `no_definition_features`
- `orbital_only`
- `approach_and_quality`
- `sentry_related`

Missing columns are omitted with warnings. Identifier, metadata, and target columns are never used as features.

## Metrics

Reports include accuracy, precision, recall, F1, false negative rate, ROC-AUC, PR-AUC, Brier score, confusion matrix, and top-k recall when probabilities are available. Metrics that do not apply to small or single-class test sets are set to null with warnings.

## Outputs

The ML pipeline writes:

```text
reports/ml/baseline_results.json
reports/ml/baseline_metrics.csv
reports/ml/experiment_summary.md
reports/ml/insufficient_data_report.md
artifacts/models/*.joblib
```

Model files are ignored by git.

## Class Imbalance

PHA is expected to be imbalanced. Baseline classifiers use balanced class weights where supported. The reports emphasize PR-AUC and false negatives because high accuracy can be misleading when positives are rare.

