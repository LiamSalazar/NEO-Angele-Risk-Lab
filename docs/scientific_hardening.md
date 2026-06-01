# Scientific Hardening

This phase raises methodological rigor without changing the product into a formal hazard system.

## Scope

- Risk ranking remains based on the deterministic Risk Priority Score.
- Score Simulation is documented as uncertainty propagation plus deterministic sensitivity.
- Orbital Simulation uses SBDB covariance when available and explicit fallback scenarios otherwise.
- ML and GNN outputs are secondary evidence and remain leakage-audited.

## Generated Reports

- `reports/simulation/score_uncertainty_summary.json`
- `reports/simulation/score_sensitivity_summary.json`
- `reports/orbital_simulation/orbital_covariance_status.json`
- `reports/orbital_simulation/cad_validation_summary.json`
- `reports/risk/risk_component_formulas.json`
- `reports/risk/risk_ablation_summary.json`
- `reports/model_evidence/cross_validation_summary.json`
- `reports/model_evidence/calibration_summary.json`
- `reports/gnn/graph_k_ablation.csv`
- `reports/gnn/gnn_vs_tabular_benchmark.csv`

## Limitations

The project does not claim calibrated impact probabilities, n-body propagation, or GNN superiority unless current reports demonstrate it.
