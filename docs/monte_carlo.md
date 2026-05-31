# Monte Carlo Simulation

The Monte Carlo simulation estimates stability of the experimental Risk Priority Score under approximate input perturbations. It is not orbital propagation, astrodynamics, or an official impact-probability calculation.

## Variables perturbed

- `diameter`
- `h`
- `moid`
- `moid_ld`
- `min_close_approach_dist`
- `min_close_approach_dist_min`
- `max_close_approach_v_rel`
- `sentry_ip`
- `sentry_ps_cum`
- `condition_code`
- `rms`
- `arc_length`
- `n_obs_used`

Positive physical quantities use lognormal-style perturbations. Bounded values are clipped so distances and diameters do not become negative and probabilities stay in `[0, 1]`.

## Interpretation

- `p95_score`: the 95th percentile of simulated score outcomes.
- `std_score`: spread of simulated scores around the mean.
- `category_shift_probability`: share of simulations where the category differs from the base score category.

These values describe score uncertainty, not predicted impact probability.

## Limitations

The simulation perturbs tabular score inputs, not orbital state vectors. Sparse source rows can produce less informative distributions. Results should be used as educational score-stability diagnostics in the current API and frontend views.
