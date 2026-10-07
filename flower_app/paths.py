"""Fixed paths inside the Flower containers."""

from datetime import UTC, datetime
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
        `SERVER_OUTPUT_ROOT / <experiment> / <timestamp>`, where `<timestamp>` is the
        current UTC time as `YYYY-MM-DD_HH-MM-SS-mmmZ`. The directory is not created.
    """
    experiment = str(context.run_config["experiment"])
    return SERVER_OUTPUT_ROOT / experiment / run_timestamp(now=datetime.now(tz=UTC))


def run_timestamp(now: datetime) -> str:
    """Return the name of a run's output directory.

    Args:
        now:
          Timezone-aware start time of the run.

    Returns:
        `now` in UTC as `YYYY-MM-DD_HH-MM-SS-mmmZ`, with milliseconds.
    """
    utc = now.astimezone(tz=UTC)
    # `%f` gives microseconds, so the last three digits are dropped for milliseconds.
    return f"{utc.strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]}Z"
