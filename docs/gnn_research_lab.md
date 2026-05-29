# GNN research lab

The GNN lab evaluates whether orbital similarity relationships add useful signal beyond tabular models.
It does not assume the GNN is better.

## Graph construction

`python -m neo_ange.cli gnn build-graph --k 10 --min-nodes 100`

Nodes are asteroids from risk-score rows. Edges are k-nearest-neighbor orbital similarity links built from
scaled numeric features such as eccentricity, semi-major axis, perihelion distance, inclination, MOID,
H magnitude, diameter, and experimental risk score. Identifiers and the target label are excluded.

## Datasets

`GNNDatasetBuilder` returns a PyTorch Geometric `Data` object when `torch-geometric` is installed. Without
that optional dependency it returns NumPy arrays and masks, so baselines and reports still run.

## Models and baselines

Baselines:

- logistic regression
- random forest
- MLP
- label propagation where applicable

GNN models when available:

- GraphSAGE
- GCN

## Metrics

The lab reports accuracy, precision, recall, F1, ROC-AUC when defined, PR-AUC when defined, confusion
matrix, false-negative rate, and top-k recall when probabilities are available.

## Outputs

- `reports/gnn/graph_summary.json`
- `reports/gnn/gnn_experiment_results.json`
- `reports/gnn/gnn_metrics.csv`
- `reports/gnn/gnn_summary.md`
- `reports/manifests/gnn_*.json`

## Limitations

Small datasets, single-class targets, missing orbital features, or missing `torch-geometric` produce honest
skipped or insufficient-data statuses instead of fabricated metrics.
