# Model Evidence Summary

random_forest on orbital_only provides secondary evidence for pattern consistency; disagreements remain an inspection queue (104 rows).

## Best Evidence

- Best overall metric: {'model_name': 'random_forest', 'model_family': 'tabular', 'feature_set': 'full_features', 'target': 'pha', 'selection_metric': 1.0, 'metrics': {'n_samples': 250, 'positive_support': 70, 'negative_support': 180, 'accuracy': 1.0, 'precision': 1.0, 'recall': 1.0, 'f1': 1.0, 'false_negative_rate': 0.0, 'roc_auc': 1.0, 'pr_auc': 1.0, 'brier_score': 0.0004252713209455209, 'confusion_matrix': [[180, 0], [0, 70]], 'top_k_recall': {'10': 0.14285714285714285, '25': 0.35714285714285715, '50': 0.7142857142857143}, 'warnings': []}}
- Best defensible model: {'model_name': 'random_forest', 'model_family': 'tabular', 'feature_set': 'orbital_only', 'target': 'pha', 'selection_metric': 0.8267495676123587, 'metrics': {'n_samples': 250, 'positive_support': 70, 'negative_support': 180, 'accuracy': 0.856, 'precision': 0.8035714285714286, 'recall': 0.6428571428571429, 'f1': 0.7142857142857143, 'false_negative_rate': 0.35714285714285715, 'roc_auc': 0.9118253968253969, 'pr_auc': 0.8267495676123587, 'brier_score': 0.10931314530557805, 'confusion_matrix': [[169, 11], [25, 45]], 'top_k_recall': {'10': 0.14285714285714285, '25': 0.32857142857142857, '50': 0.5714285714285714}, 'warnings': []}}
- Best graph-based evidence: {'model_name': 'random_forest', 'model_family': 'graph', 'feature_set': 'graph_node_features', 'target': 'pha', 'selection_metric': 1.0, 'metrics': {'accuracy': 1.0, 'precision': 1.0, 'recall': 1.0, 'f1': 1.0, 'roc_auc': 1.0, 'pr_auc': 1.0, 'false_negative_rate': 0.0}}
- Disagreement rows: 104

## Model Cards

### random_forest / no_definition_features

- Family: tabular
- Target: pha
- Leakage risk: low
- Recommended use: Defensible support for pattern consistency without PHA definition variables.
- Interpretation: This model is useful as secondary evidence because it avoids direct definition-heavy features and focuses on orbital or contextual signals.

### logistic_regression / orbital_only

- Family: tabular
- Target: pha
- Leakage risk: low
- Recommended use: Defensible support for pattern consistency without PHA definition variables.
- Interpretation: This model is useful as secondary evidence because it avoids direct definition-heavy features and focuses on orbital or contextual signals.

### random_forest / orbital_only

- Family: tabular
- Target: pha
- Leakage risk: low
- Recommended use: Defensible support for pattern consistency without PHA definition variables.
- Interpretation: This model is useful as secondary evidence because it avoids direct definition-heavy features and focuses on orbital or contextual signals.

### random_forest / full_features

- Family: tabular
- Target: pha
- Leakage risk: high
- Recommended use: Internal diagnostic for leakage-sensitive behavior.
- Interpretation: High scores here validate that definition-related variables encode the label, but this is not the best user-facing evidence.

### random_forest / definition_features_only

- Family: tabular
- Target: pha
- Leakage risk: high
- Recommended use: Internal diagnostic for leakage-sensitive behavior.
- Interpretation: High scores here validate that definition-related variables encode the label, but this is not the best user-facing evidence.

### logistic_regression / no_definition_features

- Family: graph
- Target: pha
- Leakage risk: low
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### random_forest / no_definition_features

- Family: graph
- Target: pha
- Leakage risk: low
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### mlp / no_definition_features

- Family: graph
- Target: pha
- Leakage risk: low
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### label_propagation / no_definition_features

- Family: graph
- Target: pha
- Leakage risk: low
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### logistic_regression / orbital_only

- Family: graph
- Target: pha
- Leakage risk: low
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### random_forest / orbital_only

- Family: graph
- Target: pha
- Leakage risk: low
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### mlp / orbital_only

- Family: graph
- Target: pha
- Leakage risk: low
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### label_propagation / orbital_only

- Family: graph
- Target: pha
- Leakage risk: low
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### logistic_regression / graph_node_features

- Family: graph
- Target: pha
- Leakage risk: high
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### random_forest / graph_node_features

- Family: graph
- Target: pha
- Leakage risk: high
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### mlp / graph_node_features

- Family: graph
- Target: pha
- Leakage risk: high
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### label_propagation / graph_node_features

- Family: graph
- Target: pha
- Leakage risk: high
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### graphsage / graph

- Family: gnn
- Target: pha
- Leakage risk: low
- Recommended use: Dependency-readiness signal for advanced graph mode.
- Interpretation: Advanced GNN training was skipped and should not be compared as a metric.

### gcn / graph

- Family: gnn
- Target: pha
- Leakage risk: low
- Recommended use: Dependency-readiness signal for advanced graph mode.
- Interpretation: Advanced GNN training was skipped and should not be compared as a metric.
