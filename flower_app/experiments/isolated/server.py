"""Server side of the isolated training experiment."""

import json
import logging
import time
from collections import OrderedDict

from flwr.app import (
    ArrayRecord,
    ConfigRecord,
    Context,
    Message,
    MessageType,
    RecordDict,
)
from flwr.common.typing import UserConfig
from flwr.serverapp import Grid
from flwr.serverapp.strategy.strategy_utils import aggregate_metricrecords

from ...interface import ServerPaths
from .graphkit_config import GRAPHKIT_CONFIG
from .task import build_task

# FedAvg's default minimum, so that both experiments start with the same clients.
MIN_CLIENTS = 2

logger = logging.getLogger(__name__)


def main(grid: Grid, context: Context, paths: ServerPaths) -> None:
    """Train the initial model on each client's own data and save the averaged metrics.

    Every connected client receives the same initial model once, trains it for
    `local-epochs` epochs and evaluates it on its own validation data. The models are
    not aggregated. The clients' metrics are averaged as FedAvg averages them, weighted
    by `"num-examples"`.

    Args:
        grid:
          Grid connecting the ServerApp to the SuperNodes.
        context:
          Context of the ServerApp. Its run config holds `"experiment"`, and
          `"local-epochs"` in the experiment's table.
        paths:
          Output directory of this run. Receives `metrics.json`, with the averaged
          metrics under `"evaluate_clientapp"` and round `"1"` as in FedAvg's
          `metrics.json`, and `run_config.json`.

    Raises:
        RuntimeError:
          If a client replies with an error.
    """
    config = _experiment_config(run_config=context.run_config)
    local_epochs = int(config["local-epochs"])

    task = build_task(graphkit_config=GRAPHKIT_CONFIG, data_normalizers=[])
    # Lightning annotates `state_dict()` as a `dict`, while Flower requires the
    # `OrderedDict` it returns at runtime.
    initial_arrays = ArrayRecord.from_torch_state_dict(OrderedDict(task.state_dict()))
    content = RecordDict(
        {
            "arrays": initial_arrays,
            "config": ConfigRecord({"local-epochs": local_epochs}),
        }
    )
    messages = [
        Message(content=content, message_type=MessageType.TRAIN, dst_node_id=node_id)
        for node_id in _wait_for_clients(grid=grid, min_clients=MIN_CLIENTS)
    ]

    replies = list(grid.send_and_receive(messages))
    for reply in replies:
        if reply.has_error():
            raise RuntimeError(f"A client failed to train: {reply.error}")
    averaged = aggregate_metricrecords(
        records=[reply.content for reply in replies],
        weighting_metric_name="num-examples",
    )

    paths.output_dir.mkdir(parents=True, exist_ok=True)
    metrics = {"evaluate_clientapp": {"1": dict(averaged)}}
    (paths.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (paths.output_dir / "run_config.json").write_text(json.dumps(config, indent=2))


def _wait_for_clients(grid: Grid, min_clients: int) -> list[int]:
    """Wait until at least `min_clients` clients are connected.

    Args:
        grid:
          Grid connecting the ServerApp to the SuperNodes.
        min_clients:
          Minimum number of connected clients.

    Returns:
        The node IDs of all connected clients.
    """
    while len(node_ids := list(grid.get_node_ids())) < min_clients:
        logger.info(f"Waiting for clients: {len(node_ids)} of {min_clients} connected.")
        time.sleep(1)
    return node_ids


def _experiment_config(run_config: UserConfig) -> UserConfig:
    """Return the run config table of the experiment named in the run config.

    Args:
        run_config:
          Flattened run config. Holds `"experiment"` and the experiment's keys as
          `"<experiment>.<key>"`.

    Returns:
        The experiment's keys without the `"<experiment>."` prefix.
    """
    prefix = f"{run_config['experiment']}."
    return {
        key.removeprefix(prefix): value
        for key, value in run_config.items()
        if key.startswith(prefix)
    }
