"""Optional torch-geometric GNN model definitions."""

from __future__ import annotations

import importlib.util
from typing import Any

TORCH_AVAILABLE = importlib.util.find_spec("torch") is not None
TORCH_GEOMETRIC_AVAILABLE = (
    TORCH_AVAILABLE and importlib.util.find_spec("torch_geometric") is not None
)


if TORCH_GEOMETRIC_AVAILABLE:
    import torch
    from torch import nn
    from torch_geometric.nn import GCNConv, SAGEConv

    class GraphSAGEModel(nn.Module):
        """Small GraphSAGE classifier for node classification."""

        def __init__(
            self,
            in_channels: int,
            hidden_channels: int = 32,
            out_channels: int = 2,
            dropout: float = 0.2,
        ) -> None:
            super().__init__()
            self.conv1 = SAGEConv(in_channels, hidden_channels)
            self.conv2 = SAGEConv(hidden_channels, out_channels)
            self.dropout = float(dropout)

        def forward(self, x: Any, edge_index: Any) -> Any:
            x = self.conv1(x, edge_index).relu()
            x = torch.nn.functional.dropout(x, p=self.dropout, training=self.training)
            return self.conv2(x, edge_index)

    class GCNModel(nn.Module):
        """Small GCN classifier for node classification."""

        def __init__(
            self,
            in_channels: int,
            hidden_channels: int = 32,
            out_channels: int = 2,
            dropout: float = 0.2,
        ) -> None:
            super().__init__()
            self.conv1 = GCNConv(in_channels, hidden_channels)
            self.conv2 = GCNConv(hidden_channels, out_channels)
            self.dropout = float(dropout)

        def forward(self, x: Any, edge_index: Any) -> Any:
            x = self.conv1(x, edge_index).relu()
            x = torch.nn.functional.dropout(x, p=self.dropout, training=self.training)
            return self.conv2(x, edge_index)

else:

    class GraphSAGEModel:  # type: ignore[no-redef]
        """Placeholder used when torch-geometric is not installed."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("torch-geometric is required for GraphSAGEModel.")

    class GCNModel:  # type: ignore[no-redef]
        """Placeholder used when torch-geometric is not installed."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("torch-geometric is required for GCNModel.")
