"""Lightning trainer configuration for the graphkit task."""

from pathlib import Path

import lightning as L
from lightning.pytorch.loggers import CSVLogger


def make_trainer(max_epochs: int, log_dir: Path) -> L.Trainer:
    """Create a single-device CPU trainer without checkpointing.

    Args:
        max_epochs:
          Maximum number of training epochs.
        log_dir:
          Directory the CSV logger writes to.

    Returns:
        The configured trainer.
    """
    return L.Trainer(
        max_epochs=max_epochs,
        accelerator="cpu",
        devices=1,
        logger=CSVLogger(save_dir=log_dir),
        enable_checkpointing=False,
        enable_progress_bar=False,
        num_sanity_val_steps=0,
    )
