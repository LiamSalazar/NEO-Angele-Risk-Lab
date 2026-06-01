# GNN Validation

## Objective

Evaluate the orbital graph and GNN experiments as honest research evidence.

## Methodology

Reports include k-ablation over `k=5,10,15,30`, comparison against tabular baselines, leakage-sensitive feature-set markings, and a transductive-setting warning.

## Files

- `src/neo_ange/gnn/experiments.py`
- `src/neo_ange/gnn/reporting.py`
- `reports/gnn/graph_k_ablation.csv`
- `reports/gnn/gnn_vs_tabular_benchmark.csv`

## Limitations

GNN results are not presented as superior unless metrics beat tabular baselines in the generated reports.
