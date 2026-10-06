"""Generate a synthetic power flow dataset from a datakit YAML config."""

import argparse
import logging
from pathlib import Path

import yaml
from gridfm_datakit import generate_power_flow_data

logger = logging.getLogger(__name__)


def main() -> None:
    """Parse `--config` and generate the dataset it describes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    generate_data(config_path=args.config)


def generate_data(config_path: Path) -> dict[str, str]:
    """Generate a power flow dataset from a datakit YAML config.

    Args:
        config_path:
          Path to the datakit YAML config. Its `settings.data_dir` sets the output
          directory.

    Returns:
        The artifact mapping returned by `gridfm_datakit.generate_power_flow_data`.
    """
    with config_path.open() as f:
        config = yaml.safe_load(f)

    logger.info(f"Generating data from {config_path}")
    file_paths = generate_power_flow_data(config=config)
    logger.info(
        f"Wrote {len(file_paths)} artifacts to {config['settings']['data_dir']}"
    )
    return file_paths


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    main()
