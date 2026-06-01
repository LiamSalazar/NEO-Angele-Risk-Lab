# Risk Score Validation

## Objective

Make the deterministic Risk Priority Score explainable, testable, and honest about calibration limits.

## Methodology

The score keeps its default weights. Reports document each component formula, clipping, internal weights, monotonicity expectations, deterministic sensitivity, and component ablation.

## Files

- `src/neo_ange/risk/validation.py`
- `tests/test_risk_monotonicity.py`
- `reports/risk/risk_component_formulas.json`
- `reports/risk/risk_ablation_summary.json`
- `reports/risk/risk_component_sensitivity.csv`

## Limitations

Weights are not calibrated against impact outcomes. Ablation reports compare ranking stability only.
