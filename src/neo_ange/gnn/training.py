"""Training helpers for optional torch-geometric experiments."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np

from neo_ange.gnn.evaluation import evaluate_binary_classification
from neo_ange.gnn.models import (
    TORCH_GEOMETRIC_AVAILABLE,
    GCNModel,
    GraphSAGEModel,
)
from neo_ange.utils.serialization import to_jsonable


class GNNTrainer:
    """CPU-only trainer for small node-classification GNN experiments."""

    def train_graphsage(
        self,
        data: Any,
        epochs: int = 100,
        patience: int = 10,
        random_state: int = 42,
    ) -> dict[str, Any]:
        """Train GraphSAGE when torch-geometric is available."""
        if not TORCH_GEOMETRIC_AVAILABLE:
            return _missing_dependency_result("GraphSAGE")
        return self._train_model(
            data=data,
            model_name="GraphSAGE",
            model_factory=GraphSAGEModel,
            epochs=epochs,
            patience=patience,
            random_state=random_state,
        )

    def train_gcn(
        self,
        data: Any,
        epochs: int = 100,
        patience: int = 10,
        random_state: int = 42,
    ) -> dict[str, Any]:
        """Train GCN when torch-geometric is available."""
        if not TORCH_GEOMETRIC_AVAILABLE:
            return _missing_dependency_result("GCN")
        return self._train_model(
            data=data,
            model_name="GCN",
            model_factory=GCNModel,
            epochs=epochs,
            patience=patience,
            random_state=random_state,
        )

    def evaluate(self, model: Any, data: Any, mask_name: str = "test_mask") -> dict[str, Any]:
        """Evaluate a trained model on a named mask."""
        if not TORCH_GEOMETRIC_AVAILABLE:
            return _missing_dependency_result("GNN")
        import torch

        mask = getattr(data, mask_name)
        if int(mask.sum()) == 0:
            return {
                "status": "insufficient_data",
                "warnings": [f"Mask '{mask_name}' has no labeled nodes."],
            }
        model.eval()
        with torch.no_grad():
            logits = model(data.x, data.edge_index)
            proba = torch.softmax(logits, dim=1).cpu().numpy()
            pred = proba.argmax(axis=1)
        y_true = data.y[mask].cpu().numpy()
        y_pred = pred[mask.cpu().numpy()]
        y_proba = proba[mask.cpu().numpy()]
        return {
            "status": "success",
            "metrics": evaluate_binary_classification(y_true, y_pred, y_proba),
        }

    def predict_proba(self, model: Any, data: Any) -> np.ndarray | None:
        """Return node probabilities for a trained model."""
        if not TORCH_GEOMETRIC_AVAILABLE:
            return None
        import torch

        model.eval()
        with torch.no_grad():
            logits = model(data.x, data.edge_index)
            return torch.softmax(logits, dim=1).cpu().numpy()

    def _train_model(
        self,
        data: Any,
        model_name: str,
        model_factory: Any,
        epochs: int,
        patience: int,
        random_state: int,
    ) -> dict[str, Any]:
        import torch

        if isinstance(data, dict):
            return _missing_dependency_result(model_name)
        if data.x.shape[0] == 0 or data.x.shape[1] == 0:
            return {
                "status": "insufficient_data",
                "model_name": model_name,
                "warnings": ["The graph dataset has no usable node features."],
            }
        train_labels = data.y[data.train_mask]
        if train_labels.numel() == 0 or len(torch.unique(train_labels)) < 2:
            return {
                "status": "insufficient_data",
                "model_name": model_name,
                "warnings": ["Training mask has a single class or no labeled nodes."],
            }
        torch.manual_seed(random_state)
        model = model_factory(in_channels=int(data.x.shape[1]), out_channels=2)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
        best_state = deepcopy(model.state_dict())
        best_loss = float("inf")
        stale_epochs = 0
        epochs = max(min(int(epochs), 300), 1)
        patience = max(int(patience), 1)

        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            logits = model(data.x, data.edge_index)
            loss = torch.nn.functional.cross_entropy(logits[data.train_mask], train_labels)
            loss.backward()
            optimizer.step()

            eval_mask = data.val_mask if int(data.val_mask.sum()) else data.train_mask
            model.eval()
            with torch.no_grad():
                eval_logits = model(data.x, data.edge_index)
                eval_loss = torch.nn.functional.cross_entropy(
                    eval_logits[eval_mask],
                    data.y[eval_mask],
                ).item()
            if eval_loss < best_loss:
                best_loss = eval_loss
                best_state = deepcopy(model.state_dict())
                stale_epochs = 0
            else:
                stale_epochs += 1
            if stale_epochs >= patience:
                break

        model.load_state_dict(best_state)
        evaluation = self.evaluate(model, data, mask_name="test_mask")
        return to_jsonable(
            {
                "status": evaluation.get("status", "success"),
                "model_name": model_name,
                "epochs_trained": epoch + 1,
                "best_validation_loss": best_loss,
                "metrics": evaluation.get("metrics", {}),
                "warnings": evaluation.get("warnings", []),
            }
        )


def _missing_dependency_result(model_name: str) -> dict[str, Any]:
    return {
        "status": "skipped_missing_dependency",
        "model_name": model_name,
        "metrics": {},
        "warnings": ["torch-geometric is not installed; real GNN training was skipped."],
    }
