"""Fixed paths inside the Flower containers."""

from pathlib import Path

from flwr.app import Context

CLIENT_LOG_DIR = Path("/tmp/flower_lightning_logs")
SERVER_OUTPUT_ROOT = Path("/outputs")


def server_output_dir(context: Context) -> Path:
    """Return the output directory of this run.

    Args:
        context:
          Context of the ServerApp. Its run config holds `"experiment"`.

    Returns:
        `SERVER_OUTPUT_ROOT / <experiment> / <run-id>`. The directory is not created.
    """
    experiment = str(context.run_config["experiment"])
    return SERVER_OUTPUT_ROOT / experiment / str(context.run_id)
