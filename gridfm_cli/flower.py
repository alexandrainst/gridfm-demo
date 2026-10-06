"""Flower commands on the running federation."""

import socket
import tomllib

from .paths import REPO_ROOT
from .process import run

# Name of the Flower federation in `pyproject.toml` that experiments are submitted to.
FLOWER_FEDERATION = "local-deployment"


def run_experiment(experiment: str) -> None:
    """Submit an experiment to `FLOWER_FEDERATION` and stream its logs.

    Args:
        experiment:
          Name of the experiment, passed as the run config key `experiment`.
    """
    run(
        command=[
            "flwr",
            "run",
            ".",
            FLOWER_FEDERATION,
            "--run-config",
            f"experiment='{experiment}'",
            "--stream",
        ],
        cwd=REPO_ROOT,
    )


def superlink_address() -> str:
    """Return the address of the SuperLink that experiments are submitted to.

    Returns:
        The `address` of `FLOWER_FEDERATION` in `pyproject.toml`, as `host:port`.
    """
    with (REPO_ROOT / "pyproject.toml").open("rb") as file:
        pyproject = tomllib.load(file)
    return pyproject["tool"]["flwr"]["federations"][FLOWER_FEDERATION]["address"]


def superlink_is_reachable() -> bool:
    """Return whether the SuperLink of `superlink_address` accepts connections.

    Returns:
        Whether a TCP connection to the address succeeds within one second.
    """
    host, port = superlink_address().rsplit(":", maxsplit=1)
    try:
        with socket.create_connection(address=(host, int(port)), timeout=1.0):
            return True
    except OSError:
        return False
