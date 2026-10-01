"""ServerApp: FedAvg over a toy NumPy model."""

import numpy as np
from flwr.app import ArrayRecord, Context
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg

app = ServerApp()


@app.main()
def main(grid: Grid, context: Context) -> None:
    """Run FedAvg for `num-server-rounds`."""
    num_rounds: int = context.run_config["num-server-rounds"]

    model = [np.ones((1, 1))]
    arrays = ArrayRecord(model)

    strategy = FedAvg()
    result = strategy.start(grid=grid, initial_arrays=arrays, num_rounds=num_rounds)

    ndarrays = result.arrays.to_numpy_ndarrays()
    np.savez("final_model", *ndarrays)
