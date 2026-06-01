# Orbital Covariance Simulation

## Objective

Use SBDB covariance matrices for orbital clone generation when available and mark fallback scenario analysis when unavailable.

## Methodology

For valid covariance:

`x ~ N(mu, Sigma)`

where `mu` is the nominal orbital element vector and `Sigma` is the aligned covariance matrix.

Matrices are checked for square shape, finite values, symmetry, non-negative diagonal entries, and positive-semidefinite behavior. Small jitter is reported if required.

## Files

- `src/neo_ange/orbital_simulation/covariance.py`
- `reports/orbital_simulation/orbital_covariance_status.json`
- `reports/orbital_simulation/orbital_simulation_methodology.md`
- `reports/orbital_simulation/cad_validation.csv`

## Limitations

Propagation remains a simplified two-body Kepler approximation. It is not n-body propagation and can miss events between time steps.
