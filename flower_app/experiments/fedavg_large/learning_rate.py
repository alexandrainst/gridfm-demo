"""Learning rate that decays when a monitored loss stops improving."""

import torch
from torch.optim.lr_scheduler import ReduceLROnPlateau


class PlateauLearningRate:
    """Learning rate that decays when the loss has not improved for several steps.

    It follows torch's `ReduceLROnPlateau` in `"min"` mode, with one step per call of
    `step`.
    """

    def __init__(self, initial: float, decay: float, patience: int) -> None:
        """Create the learning rate at its initial value.

        Args:
            initial:
              Learning rate before the first step.
            decay:
              Factor that the learning rate is multiplied by on a plateau.
            patience:
              Number of consecutive steps without improvement that are tolerated. The
              learning rate decays after the step that follows them.
        """
        # The scheduler keeps its state in an optimizer, which here has one dummy
        # parameter since only the learning rate is used.
        self._optimizer = torch.optim.SGD(
            params=[torch.nn.Parameter(torch.zeros(1))], lr=initial
        )
        self._scheduler = ReduceLROnPlateau(
            optimizer=self._optimizer, mode="min", factor=decay, patience=patience
        )

    @property
    def value(self) -> float:
        """The current learning rate."""
        return float(self._optimizer.param_groups[0]["lr"])

    def step(self, loss: float) -> None:
        """Record a loss and decay the learning rate if it has plateaued.

        Args:
            loss:
              The monitored loss. Lower is better.
        """
        self._scheduler.step(metrics=loss)
