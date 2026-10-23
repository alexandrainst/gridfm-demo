"""Registry of the Flower experiments."""

from ..interface import Experiment
from .fedavg import EXPERIMENT as FEDAVG
from .fedavg_large import EXPERIMENT as FEDAVG_LARGE
from .isolated import EXPERIMENT as ISOLATED
from .isolated_large import EXPERIMENT as ISOLATED_LARGE

EXPERIMENTS: dict[str, Experiment] = {
    "fedavg": FEDAVG,
    "fedavg_large": FEDAVG_LARGE,
    "isolated": ISOLATED,
    "isolated_large": ISOLATED_LARGE,
}


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
