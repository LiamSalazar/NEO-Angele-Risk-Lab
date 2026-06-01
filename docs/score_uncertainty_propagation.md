# Score Uncertainty Propagation

## Objective

Estimate how the deterministic Risk Priority Score moves when base input variables change.

## Methodology

The score is treated as `R = f(X)`, where `X` is the vector of base variables. Derived fields such as `log_diameter`, `inverse_moid`, `inverse_min_distance`, `size_proxy_score`, and risk components are recalculated after sampling.

Each sampled variable records:

- `distribution_type`
- `parameters`
- `source`
- `justification`
- `mode`

Modes include `reported_uncertainty`, `empirical_uncertainty`, `deterministic_sensitivity`, and `heuristic_fallback`.

## Files

- `src/neo_ange/simulation/uncertainty.py`
- `reports/simulation/score_uncertainty_summary.json`
- `reports/simulation/score_sensitivity_by_variable.csv`
- `reports/simulation/score_simulation_methodology.md`

## Limitations

When no reported uncertainty exists, results are not formal calibrated Monte Carlo. Fallback rows are explicitly marked.
