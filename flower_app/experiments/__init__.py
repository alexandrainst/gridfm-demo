"""Registry of the Flower experiments."""

from ..interface import Experiment
from .fedavg import EXPERIMENT as FEDAVG
from .local import EXPERIMENT as LOCAL

EXPERIMENTS: dict[str, Experiment] = {"fedavg": FEDAVG, "local": LOCAL}


def get_experiment(name: str) -> Experiment:
    """Return the experiment registered under `name`.

    Args:
        name:
          Name of the experiment, as in the run config key `"experiment"`.

    Returns:
        The registered experiment.

    Raises:
        KeyError:
          If no experiment is registered under `name`.
    """
    if name not in EXPERIMENTS:
        raise KeyError(
            f"Unknown experiment {name!r}. Registered experiments: "
            f"{', '.join(sorted(EXPERIMENTS))}"
        )
    return EXPERIMENTS[name]
