# ML Statistical Validation

## Objective

Strengthen ML evidence while keeping it secondary to the deterministic Risk Priority Score.

## Methodology

The validation module generates stratified cross-validation, ROC/PR curve points, calibration bins, Brier score, threshold analysis, and permutation importance for a defensible feature set.

## Files

- `src/neo_ange/ml/validation.py`
- `reports/model_evidence/cross_validation_metrics.csv`
- `reports/model_evidence/roc_curve_points.csv`
- `reports/model_evidence/pr_curve_points.csv`
- `reports/model_evidence/calibration_summary.json`
- `reports/model_evidence/permutation_importance.csv`
- `reports/model_evidence/threshold_analysis.csv`

## Limitations

Definition-derived feature sets are marked leakage-sensitive. ML is not used as the ranking source.
