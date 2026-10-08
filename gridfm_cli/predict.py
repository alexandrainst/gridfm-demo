"""Prediction of a run's model on the client data of the run's federation."""

import json
import logging
import typing as t
from pathlib import Path

import lightning as L
import numpy as np
import pandas as pd
import torch
from gridfm_graphkit.datasets.globals import PG_H, QG_H, VA_H, VM_H
from gridfm_graphkit.datasets.hetero_powergrid_datamodule import LitGridHeteroDataModule
from gridfm_graphkit.io.param_handler import NestedNamespace, get_task
from torch_geometric.data import HeteroData
from torch_geometric.loader import DataLoader
from torch_scatter import scatter_max

from .clients import ClientData, read_clients
from .runs import GRAPHKIT_CONFIG_FILE, MODEL_FILE, Run

logger = logging.getLogger(__name__)

FEATURES: tuple[str, ...] = ("Vm", "Va", "Pg", "Qg")
# Columns of graphkit's `PowerFlowTask.predict_step` that the predictions keep.
PREDICT_STEP_COLUMNS: tuple[str, ...] = (
    "scenario",
    "bus",
    "PQ",
    "PV",
    "REF",
    "Pd",
    "Qd",
    *(f"{feature}_{kind}" for feature in FEATURES for kind in ("target", "pred")),
)
SPLITS: tuple[str, ...] = ("train", "val", "test")


def predict_run(run: Run) -> list[Path]:
    """Predict every scenario of every client of a run's federation.

    Args:
        run:
          A run that has `MODEL_FILE` and `GRAPHKIT_CONFIG_FILE`.

    Returns:
        The written files, `run.predictions_dir / "client_<id>.parquet"` per client.
        Existing files are replaced. Each holds one row per network, scenario and bus
        with the columns `network`, `split`, `PREDICT_STEP_COLUMNS` and
        `<feature>_given` for each of `FEATURES`. Values are in the units of the
        gridfm-datakit data.
    """
    graphkit_config = json.loads((run.output_dir / GRAPHKIT_CONFIG_FILE).read_text())
    state_dict = torch.load(run.output_dir / MODEL_FILE, weights_only=True)
    run.predictions_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for client in read_clients(federation=run.federation):
        logger.info(f"Predicting the scenarios of client {client.client_id}.")
        predictions = predict_client(
            graphkit_config=graphkit_config, state_dict=state_dict, client=client
        )
        path = run.predictions_dir / f"client_{client.client_id}.parquet"
        predictions.to_parquet(path, index=False)
        paths.append(path)
    return paths


def predict_client(
    graphkit_config: dict[str, t.Any],
    state_dict: dict[str, torch.Tensor],
    client: ClientData,
) -> pd.DataFrame:
    """Predict every scenario of one client.

    Args:
        graphkit_config:
          Graphkit configuration of the run, without `data.networks` and
          `data.scenarios`.
        state_dict:
          Weights of the run's model.
        client:
          The client's dataset.

    Returns:
        The client's predictions, as described in `predict_run`.
    """
    data = {
        **graphkit_config["data"],
        "networks": list(client.networks),
        "scenarios": list(client.scenarios),
    }
    config = NestedNamespace(**{**graphkit_config, "data": data})
    # `setup("fit")` splits the scenarios and fits the normalizers as the client did
    # during training, since the configuration, seed and data are the same.
    data_module = LitGridHeteroDataModule(args=config, data_dir=str(client.data_dir))
    data_module.setup(stage="fit")
    task = get_task(args=config, data_normalizers=data_module.data_normalizers)
    task.load_state_dict(state_dict)
    task.eval()

    frames = []
    for network_index, network in enumerate(client.networks):
        datasets = (
            data_module.train_datasets[network_index],
            data_module.val_datasets[network_index],
            data_module.test_datasets[network_index],
        )
        for split, dataset in zip(SPLITS, datasets, strict=True):
            loader = DataLoader(
                dataset, batch_size=config.training.batch_size, shuffle=False
            )
            for batch_index, batch in enumerate(loader):
                frame = _predict_batch(
                    task=task,
                    batch=batch,
                    batch_index=batch_index,
                    network_index=network_index,
                )
                frames.append(frame.assign(network=network, split=split))
    predictions = pd.concat(frames, ignore_index=True)
    # Graphkit works with Va in radians, while gridfm-datakit stores it in degrees.
    for column in ("Va_target", "Va_pred"):
        predictions[column] = np.degrees(predictions[column])
    columns = ["network", "split", *PREDICT_STEP_COLUMNS]
    columns += [f"{feature}_given" for feature in FEATURES]
    return predictions[columns].sort_values(["network", "scenario", "bus"])


def _predict_batch(
    task: L.LightningModule, batch: HeteroData, batch_index: int, network_index: int
) -> pd.DataFrame:
    """Predict one batch and return one row per bus.

    Args:
        task:
          The graphkit power flow task with the run's weights.
        batch:
          A batch of one network's scenarios.
        batch_index:
          Index of the batch in its loader.
        network_index:
          Index of the network, which selects the task's data normalizer.

    Returns:
        The columns `PREDICT_STEP_COLUMNS` and `<feature>_given` for each of
        `FEATURES`.
    """
    with torch.no_grad():
        # `predict_step` picks the data normalizer by its `dataloader_idx`.
        output = task.predict_step(
            batch=batch, batch_idx=batch_index, dataloader_idx=network_index
        )
    frame = pd.DataFrame({column: output[column] for column in PREDICT_STEP_COLUMNS})
    bus_mask = batch.mask_dict["bus"]
    # Pg is a bus value made from the bus's generators, so it is hidden when the mask
    # hides the Pg of any of them, as in graphkit's evaluation.
    _, gen_to_bus = batch.edge_index_dict[("gen", "connected_to", "bus")]
    pg_hidden, _ = scatter_max(
        batch.mask_dict["gen"][:, PG_H].long(),
        gen_to_bus,
        dim=0,
        dim_size=bus_mask.size(0),
    )
    hidden = {
        "Vm": bus_mask[:, VM_H],
        "Va": bus_mask[:, VA_H],
        "Pg": pg_hidden.bool(),
        "Qg": bus_mask[:, QG_H],
    }
    for feature, mask in hidden.items():
        frame[f"{feature}_given"] = ~np.asarray(mask.cpu())
    return frame
