# Orbital Simulation Methodology

The orbital simulator is covariance-aware when SBDB covariance data is present. For objects without a valid covariance matrix, it uses explicitly marked heuristic scenario analysis and does not present those clones as formal covariance propagation.

## Methods

- `covariance_based`: sample orbital clones from `x ~ N(mu, Sigma)` after covariance validation and label alignment.
- `heuristic_fallback`: perturb orbital elements from orbit-quality proxies when no valid covariance is available.
- Propagator: `two_body_kepler_approximation`.

## Validation

Covariance matrices are checked for square shape, finite values, symmetry, non-negative diagonal entries, and positive-semidefinite behavior. Near-PSD matrices can receive minimal jitter, which is reported.

CAD validation compares the simplified nominal minimum distance with available CAD aggregate distance fields and should be treated as a coarse consistency check.

## Limitations

- No n-body propagation is implemented.
- Temporal resolution can miss close approaches between time steps.
- Fallback clones are low-quality scenario stress tests, not calibrated uncertainty.
