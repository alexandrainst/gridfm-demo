"""Construction of the graphkit task and data module."""

import typing as t

import lightning as L
from gridfm_graphkit.datasets.hetero_powergrid_datamodule import LitGridHeteroDataModule
from gridfm_graphkit.datasets.normalizers import Normalizer
from gridfm_graphkit.io.param_handler import NestedNamespace, get_task

from ...interface import ClientDataset


def build_task_and_datamodule(
    graphkit_config: dict[str, t.Any], dataset: ClientDataset
) -> tuple[L.LightningModule, LitGridHeteroDataModule]:
    """Build the graphkit task together with a data module over `dataset`.

    Args:
        graphkit_config:
          Graphkit configuration of the task and data module, without
          `data.networks` and `data.scenarios`.
        dataset:
          Dataset of this client. Sets `data.networks` and `data.scenarios`.

    Returns:
        The task, and the data module after `setup("fit")`. The task uses the data
        module's normalizers.
    """
    config_args = NestedNamespace(
        **_with_data(
            graphkit_config=graphkit_config,
            networks=list(dataset.networks),
            scenarios=list(dataset.scenarios),
        )
    )
    data_module = LitGridHeteroDataModule(
        args=config_args, data_dir=str(dataset.data_dir)
    )
    data_module.setup(stage="fit")
    task = get_task(args=config_args, data_normalizers=data_module.data_normalizers)
    return task, data_module


def build_task(
    graphkit_config: dict[str, t.Any], data_normalizers: list[Normalizer]
) -> L.LightningModule:
    """Build the graphkit task without a dataset.

    Args:
        graphkit_config:
          Graphkit configuration of the task, without `data.networks` and
          `data.scenarios`.
        data_normalizers:
          Normalizers passed to the task. May be empty.

    Returns:
        The configured task, with no networks.
    """
    # Graphkit's tasks read `data.networks` on construction but only use the names in
    # test and validation steps, which a task without a dataset never runs.
    config_args = NestedNamespace(
        **_with_data(graphkit_config=graphkit_config, networks=[], scenarios=[])
    )
    return get_task(args=config_args, data_normalizers=data_normalizers)


def _with_data(
    graphkit_config: dict[str, t.Any], networks: list[str], scenarios: list[int]
) -> dict[str, t.Any]:
    """Return a copy of `graphkit_config` with the networks and scenarios set.

    Args:
        graphkit_config:
          Graphkit configuration. Not modified.
        networks:
          Value of `data.networks`.
        scenarios:
          Value of `data.scenarios`.

    Returns:
        The configuration with `data.networks` and `data.scenarios` set.
    """
    data = {**graphkit_config["data"], "networks": networks, "scenarios": scenarios}
    return {**graphkit_config, "data": data}
