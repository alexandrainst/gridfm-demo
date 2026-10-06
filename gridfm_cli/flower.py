"""Flower commands on the running federation."""

from .paths import REPO_ROOT
from .process import run


def run_experiment(experiment: str) -> None:
    """Submit an experiment to the federation at `local-deployment` and stream its logs.

    Args:
        experiment:
          Name of the experiment, passed as the run config key `experiment`.
    """
    run(
        command=[
            "flwr",
            "run",
            ".",
            "local-deployment",
            "--run-config",
            f"experiment='{experiment}'",
            "--stream",
        ],
        cwd=REPO_ROOT,
    )
