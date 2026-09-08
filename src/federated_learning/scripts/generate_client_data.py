"""Generate synthetic grid data for a single federated learning client."""

import argparse
import logging
from pathlib import Path

import yaml
from gridfm_datakit import generate_power_flow_data

logger = logging.getLogger(__name__)


def main() -> None:
    """Load a datakit YAML config and generate parquet output for one client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    with args.config.open() as f:
        config = yaml.safe_load(f)

    logger.info("Generating client data from %s", args.config)
    file_paths = generate_power_flow_data(config)
    logger.info(
        "Wrote %d artifacts to %s", len(file_paths), config["settings"]["data_dir"]
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    main()
