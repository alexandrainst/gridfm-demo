"""ServerApp: FedAvg over the GridFM model state_dict."""

from pathlib import Path

import torch
from flwr.app import ArrayRecord, ConfigRecord, Context
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg
from gridfm_graphkit.io.param_handler import NestedNamespace, get_task

from src.federated_learning.config.graphkit_config import GRAPHKIT_CONFIG


app = ServerApp()


@app.main()
def main(grid: Grid, context: Context) -> None:
    """Run FedAvg for ``num-server-rounds`` and persist the aggregated weights."""
    num_rounds = int(context.run_config["num-server-rounds"])
    local_epochs = int(context.run_config["local-epochs"])

    config_args = NestedNamespace(**GRAPHKIT_CONFIG)
    task = get_task(config_args, data_normalizers=[])

    initial_arrays = ArrayRecord.from_torch_state_dict(task.state_dict())
    train_config = ConfigRecord({"local-epochs": local_epochs})

    strategy = FedAvg()
    result = strategy.start(
        grid=grid,
        initial_arrays=initial_arrays,
        num_rounds=num_rounds,
        train_config=train_config,
    )

    torch.save(result.arrays.to_torch_state_dict(), "final_model.pt")
