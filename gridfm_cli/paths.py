"""Paths of the repository that the command-line interface works on."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FEDERATIONS_DIR = REPO_ROOT / "federations"
EXPERIMENTS_DIR = REPO_ROOT / "flower_app" / "experiments"
OUTPUTS_DIR = REPO_ROOT / "outputs"
PREDICTIONS_DIR = REPO_ROOT / "predictions"


def federation_dir(federation: str) -> Path:
    """Return the folder of a federation.

    Args:
        federation:
          Name of the federation.

    Returns:
        `FEDERATIONS_DIR / federation`.
    """
    return FEDERATIONS_DIR / federation
