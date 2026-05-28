# Leakage Audit

The leakage audit checks whether baseline models are simply reproducing the approximate PHA definition instead of learning broader risk context.

## Why H and MOID Are Sensitive

PHA labels are closely tied to absolute magnitude `h` and Earth minimum orbit intersection distance `moid`. Diameter and derived features such as `inverse_moid`, `size_proxy_score`, and `proximity_proxy_score` can also act as strong proxies. High performance from these variables is useful as a sanity check, but it should not be presented as independent hazard intelligence.

## Compared Feature Sets

The audit compares:

- `full_features`
- `definition_features_only`
- `no_definition_features`
- `orbital_only`
- `approach_and_quality`
- `sentry_related`

The most important contrast is between `definition_features_only` and `no_definition_features`.

## Interpretation

Possible leakage signals include:

- `definition_features_only` performs very well.
- `full_features` greatly outperforms `no_definition_features`.
- Metrics drop sharply when H, MOID, diameter, and their proxies are removed.

Those patterns suggest the model is recovering the label definition. If definition-free features still perform above simple baselines, that may indicate additional contextual signal, but the conclusion should remain cautious.

## Outputs

The audit writes:

```text
reports/ml/leakage_audit.json
reports/ml/leakage_audit.md
```

If there are no completed baseline experiments, the audit still writes a report explaining that comparison results are insufficient.

## Limitations

Small datasets, few positives, single-class splits, and source-selection effects can dominate metrics. The audit does not prove that a model is leakage-free; it provides evidence to guide safer feature design for later phases.

