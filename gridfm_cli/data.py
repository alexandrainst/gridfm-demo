"""Generation and deletion of the synthetic data of a federation's clients."""

import logging
import shutil

import typer
import yaml
from gridfm_datakit import generate_power_flow_data

from .paths import REPO_ROOT, federation_dir

logger = logging.getLogger(__name__)


def generate_data(federation: str, force: bool) -> None:
    """Generate the data of each client of a federation.

    Each `datakit_config/client_*.yaml` of the federation is a gridfm-datakit config.
    Its `settings.data_dir` is the output folder, relative to the repository root. A
    client has data once `<data_dir>/<network.name>/raw/bus_data.parquet` exists.

    Args:
        federation:
          Name of the federation.
        force:
          Whether to regenerate the data of clients that already have data.
    """
    config_dir = federation_dir(federation=federation) / "datakit_config"
    for config_path in sorted(config_dir.glob("client_*.yaml")):
        with config_path.open() as file:
            config = yaml.safe_load(file)
        data_dir = REPO_ROOT / config["settings"]["data_dir"]
        # gridfm-datakit creates the folder and its logs before it fails, so only the
        # data file shows that a previous run completed.
        bus_data = data_dir / config["network"]["name"] / "raw" / "bus_data.parquet"
        if bus_data.exists() and not force:
            logger.info(f"Skipping {config_path.stem}: its data exists in {data_dir}.")
            continue
        logger.info(f"Generating the data of {config_path.stem} in {data_dir}.")
        # gridfm-datakit resolves the folder against the working directory, which may
        # not be the repository root.
        config["settings"]["data_dir"] = str(data_dir)
        generate_power_flow_data(config=config)


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
