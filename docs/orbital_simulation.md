# Orbital Simulation

The orbital simulation module runs approximate heliocentric clone scenarios from available orbital elements. It is designed for inspection and prioritization, not authoritative orbit determination.

## Method

- Extracts `a`, `e`, `i`, `om`, `w`, `ma`, mean motion, MOID, and uncertainty context when available.
- Fills missing propagation inputs with conservative defaults and explicit warnings.
- Perturbs orbital elements using condition code, RMS, observation arc, and observation count.
- Propagates clones with a simplified two-body model and compares distance bands to an approximate circular Earth orbit.
- Reports p05, p50, and p95 minimum-distance bands, closest-day bands, dispersion index, uncertainty score, and scenario category.

## Outputs

- `data/gold/orbital_simulation/orbital_monte_carlo_results.parquet`
- `reports/orbital_simulation/orbital_simulation_summary.json`
- `reports/orbital_simulation/orbital_simulation_summary.md`
- `reports/orbital_simulation/top_orbital_uncertainty_objects.csv`
- `reports/orbital_simulation/orbital_scenario_findings.json`

## CLI

```bash
python -m neo_ange.cli orbital-sim status
python -m neo_ange.cli orbital-sim object A-001 --n-clones 500
python -m neo_ange.cli orbital-sim batch --limit 50 --n-clones 300
```

Batch API responses omit the full distance trace to keep frontend payloads small. Object-level runs retain the trace for the distance-band chart.
