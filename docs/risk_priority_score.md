# Risk Priority Score

The Risk Priority Score is an experimental, explainable ranking signal for Neo Angele Risk Lab. It is designed to prioritize review and follow-up inside this project, not to issue official alerts or replace NASA/JPL CNEOS, Sentry, or professional orbital analysis.

## Components

- `physical_risk_component`: estimated diameter, absolute magnitude `h`, and size proxies.
- `orbital_risk_component`: MOID, lunar-distance MOID, perihelion, eccentricity, and inclination.
- `approach_risk_component`: minimum close-approach distance, relative velocity, and approach count.
- `sentry_risk_component`: Sentry presence and available Sentry probability, Palermo, Torino, and virtual-impact fields.
- `uncertainty_risk_component`: condition code, RMS, observation arc, observation count, and uncertainty proxies.
- `data_quality_component`: missingness and limited observation coverage as a small score moderator.

## Weights

- physical: 0.22
- orbital: 0.25
- approach: 0.18
- sentry: 0.17
- uncertainty: 0.13
- data quality: 0.05

All components are clipped to `[0, 1]`; the final score is clipped to `[0, 100]`.

## Categories

- low: score < 20
- moderate: 20 <= score < 40
- elevated: 40 <= score < 60
- high: 60 <= score < 80
- critical: score >= 80

## Limitations

The score is feature-based and educational. Sparse rows can still be scored, but explanations flag limited data coverage. Absence of Sentry fields is treated as a low Sentry component, not proof of no risk. The score should be interpreted as experimental follow-up priority only.
