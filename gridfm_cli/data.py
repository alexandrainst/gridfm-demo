"""Generation and deletion of the synthetic data of a federation's clients."""

import dataclasses
import logging
import shutil
import typing as t
from pathlib import Path

import typer
import yaml
from gridfm_datakit import generate_power_flow_data

from .paths import REPO_ROOT, federation_dir

logger = logging.getLogger(__name__)


def generate_data(federation: str, force: bool) -> None:
    """Generate the data of each client of a federation.

    Each `datakit_config/client_*.yaml` of the federation is a gridfm-datakit config.
    Its `settings.data_dir` is the output folder, relative to the repository root.

    Args:
        federation:
          Name of the federation.
        force:
          Whether to regenerate the data of clients that already have data.
    """
    for client in _clients(federation=federation):
        if client.has_data and not force:
            logger.info(
                f"Skipping {client.name}: its data exists in {client.data_dir}."
            )
            continue
        logger.info(f"Generating the data of {client.name} in {client.data_dir}.")
        # gridfm-datakit resolves the folder against the working directory, which may
        # not be the repository root.
        config = {
            **client.config,
            "settings": {**client.config["settings"], "data_dir": str(client.data_dir)},
        }
        generate_power_flow_data(config=config)


def clients_without_data(federation: str) -> list[str]:
    """Return the clients of a federation that have no generated data.

    Args:
        federation:
          Name of the federation.

    Returns:
        Names of the clients without data, such as `client_0`, in sorted order.
    """
    return [
        client.name for client in _clients(federation=federation) if not client.has_data
    ]


def delete_data(federation: str, confirm: bool) -> None:
    """Delete the generated data of a federation.

    Args:
        federation:
          Name of the federation.
        confirm:
          Whether to ask the user before deleting.

    Raises:
        typer.Abort:
          If the user declines the deletion.
    """
    data_dir = federation_dir(federation=federation) / "data"
    if not data_dir.exists():
        logger.info(f"Nothing to delete: {data_dir} does not exist.")
        return
    if confirm and not typer.confirm(f"Delete {data_dir}?"):
        raise typer.Abort()
    shutil.rmtree(data_dir)
    logger.info(f"Deleted {data_dir}.")


@dataclasses.dataclass(frozen=True)
class _Client:
    """A client of a federation and the location of its data.

    Attributes:
        name:
          Stem of the client's config file, such as `client_0`.
        config:
          The client's gridfm-datakit config.
        data_dir:
          Absolute folder that the client's data is generated into.
        has_data:
          Whether the client's data has been generated.
    """

    name: str
    config: dict[str, t.Any]
    data_dir: Path
    has_data: bool


def _clients(federation: str) -> list[_Client]:
    """Return the clients of a federation, sorted by name.

    A client has data once `<data_dir>/<network.name>/raw/bus_data.parquet` exists.

    Args:
        federation:
          Name of the federation.

    Returns:
        One `_Client` per `datakit_config/client_*.yaml` of the federation.
    """
    clients: list[_Client] = []
    config_dir = federation_dir(federation=federation) / "datakit_config"
    for config_path in sorted(config_dir.glob("client_*.yaml")):
        with config_path.open() as file:
            config: dict[str, t.Any] = yaml.safe_load(file)
        data_dir = REPO_ROOT / config["settings"]["data_dir"]
        # gridfm-datakit creates the folder and its logs before it fails, so only the
        # data file shows that a previous run completed.
        bus_data = data_dir / config["network"]["name"] / "raw" / "bus_data.parquet"
        clients.append(
            _Client(
                name=config_path.stem,
                config=config,
                data_dir=data_dir,
                has_data=bus_data.exists(),
            )
        )
    return clients
