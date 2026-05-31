# Analytical Findings Summary

## Summary

- finding_count: 19
- dataset_rows: 1000
- risk_rows: 1000
- score_simulation_rows: 21
- orbital_simulation_rows: 50
- graph_nodes: 1000
- graph_edges: 6955

## Findings

### The current observatory dataset is analyzable

The active dataset contains 1,000 objects, with 280 PHA labels and 720 non-PHA labels.

- Basis: Counts are computed from the active gold/risk-score table.
- Importance: high
- Source: dataset

### Sentry signal is limited to a small subset

2 of 1,000 objects carry a Sentry signal in the current dataset.

- Basis: Sentry count is derived from the sentry_flag field.
- Importance: medium
- Source: dataset
- Caveat: Sentry fields are sparse and should not be interpreted as complete alerting.

### Most objects concentrate in moderate priority

The largest risk category is moderate; 909 objects fall there.

- Basis: Risk categories are counted from the current risk_scores table.
- Importance: high
- Source: risk

### Elevated priority objects are a focused review set

21 objects are currently elevated or above, keeping the highest-priority review list compact.

- Basis: Elevated objects are risk_category in elevated, high or critical.
- Importance: high
- Source: risk
- Related objects: 20152637, 20089958, 20067381, 20137108, 20031669, 20141495, 20143487, 20143651, 20016960, 20143649

### Top-ranked objects are driven by physical and orbital factors

Among the highest-ranked objects, physical size and orbital proximity are the dominant components.

- Basis: Dominant components are counted across the top 20 rows by risk_score_0_100.
- Importance: high
- Source: risk
- Related objects: 20152637, 20089958, 20067381, 20137108, 20031669, 20141495, 20143487, 20143651, 20016960, 20143649

### Most simulated top objects retain their priority band

14 of 21 simulated objects have category-shift probability at or below 20%.

- Basis: Category-shift probability is read from score Monte Carlo results.
- Importance: medium
- Source: score_simulation
- Related objects: 20004179, 20003122, 20000433, 20001685, 20002101

### Some objects show score sensitivity near category thresholds

The highest shift-probability objects should be inspected before treating their category as stable.

- Basis: Objects are ranked by category_shift_probability.
- Importance: medium
- Source: score_simulation
- Related objects: 20143487, 20141495, 20143649, 20101955, 20101955

### Approximate orbital scenarios are available for priority objects

50 objects have saved orbital perturbation results.

- Basis: Rows are read from orbital_monte_carlo_results.parquet.
- Importance: high
- Source: orbital_simulation

### Orbital uncertainty varies across the priority set

Objects with the highest dispersion index deserve closer review in the orbital simulation view.

- Basis: Objects are ranked by dispersion_index.
- Importance: medium
- Source: orbital_simulation
- Related objects: 20020425, 20101869, 20152685, 20163067, 20199801

### The orbital graph forms an analytical neighborhood

The graph contains 1,000 nodes and 6,955 similarity edges.

- Basis: Nodes and edges are counted from exported graph Parquet files.
- Importance: high
- Source: orbital_graph

### Graph neighborhoods support object-level comparison

Nearest-neighbor links can be used to inspect orbitally similar objects around a selected NEO.

- Basis: Edges are kNN orbital-similarity links built from scaled orbital and risk-context features.
- Importance: medium
- Source: orbital_graph
- Related objects: 20001580, 20001864, 20001915, 20002062, 20002100

### Best defensible evidence avoids definition-heavy leakage

random_forest on orbital_only is the current defensible model-evidence view.

- Basis: The evidence builder excludes definition-heavy feature sets from the best defensible pick. Model evidence supports interpretation; it does not define the priority ranking.
- Importance: high
- Source: model_evidence

### Model disagreements create an inspection queue

310 objects are flagged in disagreement outputs.

- Basis: Disagreements compare high-confidence predictions against observed labels or model families and remain secondary to the Risk Priority Score.
- Importance: medium
- Source: model_evidence
