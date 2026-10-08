"""Discovery of the experiment runs of a federation in `outputs/`."""

from dataclasses import dataclass
from pathlib import Path

from .paths import OUTPUTS_DIR, PREDICTIONS_DIR

MODEL_FILE = "final_model.pt"
GRAPHKIT_CONFIG_FILE = "graphkit_config.json"
# The files a run needs for its model to be rebuilt on the host.
MODEL_FILES = (MODEL_FILE, GRAPHKIT_CONFIG_FILE)


@dataclass(frozen=True)
class Run:
    """One run of an experiment on a federation.

    Attributes:
        federation:
          Name of the federation.
        experiment:
          Name of the experiment.
        timestamp:
          Name of the run's folder, the UTC start time of the run.
    """

    federation: str
    experiment: str
    timestamp: str

    @property
    def name(self) -> str:
        """`<experiment>/<timestamp>`, unique within the federation."""
        return f"{self.experiment}/{self.timestamp}"

    @property
    def output_dir(self) -> Path:
        """Folder the federation wrote the run's outputs to."""
        return OUTPUTS_DIR / self.federation / self.experiment / self.timestamp

    @property
    def predictions_dir(self) -> Path:
        """Folder for the run's predictions, mirroring `output_dir`."""
        return PREDICTIONS_DIR / self.federation / self.experiment / self.timestamp


def list_runs(federation: str) -> list[Run]:
    """Return the runs of a federation, sorted by name.

    Args:
        federation:
          Name of the federation.

    Returns:
        One `Run` per folder `outputs/<federation>/<experiment>/<timestamp>/`. Empty if
        the federation has no outputs.
    """
    return sorted(
        (
            Run(federation=federation, experiment=path.parent.name, timestamp=path.name)
            for path in (OUTPUTS_DIR / federation).glob("*/*/")
        ),
        key=lambda run: run.name,
    )


def missing_model_files(run: Run) -> list[str]:
    """Return the files of `MODEL_FILES` that a run lacks.

    Args:
        run:
          The run to check.

    Returns:
        The names of the missing files, in the order of `MODEL_FILES`. Empty if the
        run's model can be rebuilt.
    """
    return [name for name in MODEL_FILES if not (run.output_dir / name).is_file()]
