# Model Evidence Summary

graphsage on graph provides secondary evidence for pattern consistency; disagreements remain an inspection queue (1367 rows).

## Best Evidence

- Best overall metric: {'model_name': 'random_forest', 'model_family': 'tabular', 'feature_set': 'full_features', 'target': 'pha', 'leakage_risk': 'high', 'selection_metric': 1.0, 'metrics': {'n_samples': 1000, 'positive_support': 245, 'negative_support': 755, 'accuracy': 0.996, 'precision': 0.9839357429718876, 'recall': 1.0, 'f1': 0.9919028340080972, 'false_negative_rate': 0.0, 'roc_auc': 1.0, 'pr_auc': 1.0, 'brier_score': 0.0028024268932087654, 'confusion_matrix': [[751, 4], [0, 245]], 'top_k_recall': {'10': 0.04081632653061224, '25': 0.10204081632653061, '50': 0.20408163265306123}, 'warnings': []}, 'recommended_use': 'Internal diagnostic for leakage-sensitive behavior.', 'not_recommended_use': 'Do not treat this as an official impact-risk or alerting model.', 'interpretation': 'High scores here validate that definition-related variables encode the label, but this is not the best user-facing evidence.', 'strengths': ['Produces probabilistic ranking evidence.', 'Provides a measurable check on positive-label retrieval.'], 'limitations': ['Definition-adjacent inputs can make PHA metrics look stronger than they are.'], 'status': 'success'}
- Best defensible model: {'model_name': 'graphsage', 'model_family': 'gnn', 'feature_set': 'graph', 'target': 'pha', 'leakage_risk': 'low', 'selection_metric': 0.9760233191710436, 'metrics': {'accuracy': 0.96625, 'precision': 0.9246231155778896, 'recall': 0.9387755102040816, 'f1': 0.9316455696202532, 'roc_auc': 0.9923131504257332, 'pr_auc': 0.9760233191710436, 'false_negative_rate': 0.0612244897959183}, 'recommended_use': 'Evidence of consistency between orbital neighborhoods and observed labels.', 'not_recommended_use': 'Do not treat this as an official impact-risk or alerting model.', 'interpretation': 'The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.', 'strengths': ['Produces probabilistic ranking evidence.', 'Provides a measurable check on positive-label retrieval.', 'Avoids direct PHA definition variables.'], 'limitations': ['Graph baselines are sensitive to graph construction choices.'], 'status': 'success'}
- Best graph-based evidence: {'model_name': 'random_forest', 'model_family': 'graph', 'feature_set': 'graph_node_features', 'target': 'pha', 'leakage_risk': 'high', 'selection_metric': 0.9998240179016884, 'metrics': {'accuracy': 0.9975, 'precision': 0.9899328859060402, 'recall': 1.0, 'f1': 0.9949409780775716, 'roc_auc': 0.999943814963948, 'pr_auc': 0.9998240179016884, 'false_negative_rate': 0.0}, 'recommended_use': 'Evidence of consistency between orbital neighborhoods and observed labels.', 'not_recommended_use': 'Do not treat this as an official impact-risk or alerting model.', 'interpretation': 'The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.', 'strengths': ['Produces probabilistic ranking evidence.', 'Provides a measurable check on positive-label retrieval.'], 'limitations': ['Graph baselines are sensitive to graph construction choices.'], 'status': 'success'}
- Disagreement rows: 1367

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

- Family: tabular
- Target: pha
- Leakage risk: low
- Recommended use: Defensible support for pattern consistency without PHA definition variables.
- Interpretation: This model is useful as secondary evidence because it avoids direct definition-heavy features and focuses on orbital or contextual signals.

### random_forest / no_definition_features

- Family: tabular
- Target: pha
- Leakage risk: low
- Recommended use: Defensible support for pattern consistency without PHA definition variables.
- Interpretation: This model is useful as secondary evidence because it avoids direct definition-heavy features and focuses on orbital or contextual signals.

### mlp / no_definition_features

- Family: tabular
- Target: pha
- Leakage risk: low
- Recommended use: Defensible support for pattern consistency without PHA definition variables.
- Interpretation: This model is useful as secondary evidence because it avoids direct definition-heavy features and focuses on orbital or contextual signals.

### label_propagation / no_definition_features

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

### mlp / orbital_only

- Family: tabular
- Target: pha
- Leakage risk: low
- Recommended use: Defensible support for pattern consistency without PHA definition variables.
- Interpretation: This model is useful as secondary evidence because it avoids direct definition-heavy features and focuses on orbital or contextual signals.

### label_propagation / orbital_only

- Family: tabular
- Target: pha
- Leakage risk: low
- Recommended use: Defensible support for pattern consistency without PHA definition variables.
- Interpretation: This model is useful as secondary evidence because it avoids direct definition-heavy features and focuses on orbital or contextual signals.

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
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.

### gcn / graph

- Family: gnn
- Target: pha
- Leakage risk: low
- Recommended use: Evidence of consistency between orbital neighborhoods and observed labels.
- Interpretation: The graph model checks whether neighboring orbital contexts support the observed label pattern; it should not be read as impact prediction.
