"""Server side of the FedAvg experiment."""

import json
from collections import OrderedDict
from pathlib import Path

import torch
from flwr.app import ArrayRecord, ConfigRecord, Context, MetricRecord
from flwr.common.typing import UserConfig
from flwr.serverapp import Grid
from flwr.serverapp.strategy import FedAvg, Result

from ...interface import ServerPaths
from .graphkit_config import GRAPHKIT_CONFIG
from .task import build_task


def main(grid: Grid, context: Context, paths: ServerPaths) -> None:
    """Run FedAvg for `num-server-rounds` rounds and save the outputs.

    Args:
        grid:
          Grid connecting the ServerApp to the SuperNodes.
        context:
          Context of the ServerApp. Its run config holds `"experiment"`, and
          `"num-server-rounds"` and `"local-epochs"` in the experiment's table.
        paths:
          Output directory of this run.
    """
    config = _experiment_config(run_config=context.run_config)
    num_rounds = int(config["num-server-rounds"])
    local_epochs = int(config["local-epochs"])

    task = build_task(graphkit_config=GRAPHKIT_CONFIG, data_normalizers=[])
    # Lightning annotates `state_dict()` as a `dict`, while Flower requires the
    # `OrderedDict` it returns at runtime.
    initial_arrays = ArrayRecord.from_torch_state_dict(OrderedDict(task.state_dict()))
    train_config = ConfigRecord({"local-epochs": local_epochs})

    result = FedAvg().start(
        grid=grid,
        initial_arrays=initial_arrays,
        num_rounds=num_rounds,
        train_config=train_config,
    )
    save_outputs(result=result, config=config, output_dir=paths.output_dir)


def save_outputs(result: Result, config: UserConfig, output_dir: Path) -> None:
    """Write the final model, metrics and run config of a run.

    Args:
        result:
          Result returned by the strategy.
        config:
          Run config of the experiment, written to `run_config.json`.
        output_dir:
          Directory to write to. Created if missing. Receives `final_model.pt` (state
          dict), `metrics.json` (metrics per round) and `run_config.json`.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    torch.save(result.arrays.to_torch_state_dict(), output_dir / "final_model.pt")
    metrics = {
        "train_clientapp": _metrics_per_round(metrics=result.train_metrics_clientapp),
        "evaluate_clientapp": _metrics_per_round(
            metrics=result.evaluate_metrics_clientapp
        ),
        "evaluate_serverapp": _metrics_per_round(
            metrics=result.evaluate_metrics_serverapp
        ),
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (output_dir / "run_config.json").write_text(json.dumps(config, indent=2))


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


def _metrics_per_round(metrics: dict[int, MetricRecord]) -> dict[str, dict]:
    """Convert per-round metric records to JSON-serialisable dictionaries.

    Args:
        metrics:
          Metric records indexed by round number.

    Returns:
        The same metrics, keyed by round number as a string.
    """
    return {str(round_): dict(record) for round_, record in metrics.items()}
