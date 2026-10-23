"""Client side of the large isolated training experiment."""

from collections import OrderedDict
from logging import INFO

import lightning as L
import numpy as np
import torch
from flwr.app import (
    ArrayRecord,
    ConfigRecord,
    Context,
    Message,
    MetricRecord,
    RecordDict,
)
from flwr.common.logger import log
from lightning.pytorch.callbacks import EarlyStopping

from ...interface import ClientDataset, ClientPaths
from .graphkit_config import GRAPHKIT_CONFIG
from .task import build_task_and_datamodule
from .trainer import make_trainer


def train(
    msg: Message, context: Context, dataset: ClientDataset, paths: ClientPaths
) -> Message:
    """Train the received model on this client's data until it stops improving.

    Training stops after `"patience"` consecutive epochs without a lower validation
    loss, or after `"max-epochs"` epochs.

    Args:
        msg:
          Message with the initial model under `"arrays"`, and `"max-epochs"`,
          `"patience"` and `"seed"` under `"config"`.
        context:
          Context of the ClientApp.
        dataset:
          Dataset of this client.
        paths:
          Log directory of this client.

    Returns:
        Reply with the model of the epoch with the lowest validation loss under
        `"arrays"`, that loss as `"loss"` and `"num-examples"` under `"metrics"`, and
        `"client-id"` under `"config"`.
    """
    config = msg.content.config_records["config"]
    max_epochs = _config_int(config=config, key="max-epochs")
    patience = _config_int(config=config, key="patience")
    entropy = [_config_int(config=config, key="seed"), dataset.client_id]
    # `SeedSequence` mixes the run's seed and the client into one 32-bit seed, so each
    # client shuffles differently while runs repeat.
    client_seed = int(np.random.SeedSequence(entropy=entropy).generate_state(1)[0])
    L.seed_everything(seed=client_seed, workers=True, verbose=False)
    task, data_module = build_task_and_datamodule(
        graphkit_config=GRAPHKIT_CONFIG, dataset=dataset
    )
    task.load_state_dict(msg.content.array_records["arrays"].to_torch_state_dict())

    early_stopping = EarlyStopping(
        monitor="Validation loss", mode="min", patience=patience
    )
    keep_best_model = KeepBestModel()
    trainer = make_trainer(
        max_epochs=max_epochs,
        log_dir=paths.log_dir,
        callbacks=[early_stopping, LogValidationLoss(), keep_best_model],
    )
    trainer.fit(model=task, datamodule=data_module)
    best_loss = float(early_stopping.best_score)
    num_examples = sum(len(d) for d in data_module.val_datasets)

    reply = RecordDict(
        {
            "arrays": ArrayRecord.from_torch_state_dict(
                keep_best_model.best_state_dict
            ),
            "metrics": MetricRecord({"loss": best_loss, "num-examples": num_examples}),
            "config": ConfigRecord({"client-id": dataset.client_id}),
        }
    )
    return Message(content=reply, reply_to=msg)


def evaluate(
    msg: Message, context: Context, dataset: ClientDataset, paths: ClientPaths
) -> Message:
    """Reject evaluate messages, which isolated training does not send.

    Args:
        msg:
          Evaluate message.
        context:
          Context of the ClientApp.
        dataset:
          Dataset of this client.
        paths:
          Log directory of this client.

    Returns:
        Never returns.

    Raises:
        NotImplementedError:
          Always, since each client evaluates its model when it trains.
    """
    raise NotImplementedError(
        "The isolated experiment evaluates on the clients during training and does not "
        "send evaluate messages."
    )


class LogValidationLoss(L.Callback):
    """Callback that logs the validation loss after every validation run."""

    def on_validation_end(
        self, trainer: L.Trainer, pl_module: L.LightningModule
    ) -> None:
        """Log the epoch and its `"Validation loss"` to Flower's logger.

        Args:
            trainer:
              Trainer that ran the validation.
            pl_module:
              Module that was validated.
        """
        loss = float(trainer.callback_metrics["Validation loss"])
        log(INFO, f"Epoch {trainer.current_epoch + 1}: validation loss {loss:.6g}.")


class KeepBestModel(L.Callback):
    """Callback that keeps a copy of the model with the lowest validation loss.

    Attributes:
        best_loss:
          Lowest `"Validation loss"` seen so far, `inf` before the first validation.
        best_state_dict:
          State dict of the model at `best_loss`, on the CPU. Empty before the first
          validation.
    """

    def __init__(self) -> None:
        """Create the callback with no model kept."""
        self.best_loss = float("inf")
        self.best_state_dict: OrderedDict[str, torch.Tensor] = OrderedDict()

    def on_validation_end(
        self, trainer: L.Trainer, pl_module: L.LightningModule
    ) -> None:
        """Copy the model if its `"Validation loss"` is lower than `best_loss`.

        Args:
            trainer:
              Trainer that ran the validation.
            pl_module:
              Module that was validated.
        """
        loss = float(trainer.callback_metrics["Validation loss"])
        if loss < self.best_loss:
            self.best_loss = loss
            self.best_state_dict = OrderedDict(
                (key, value.detach().cpu().clone())
                for key, value in pl_module.state_dict().items()
            )


def _config_int(config: ConfigRecord, key: str) -> int:
    """Return an integer value of a config record.

    Args:
        config:
          Config record of a message.
        key:
          Key of the value.

    Returns:
        The value under `key`.

    Raises:
        TypeError:
          If the value is not an integer.
    """
    value = config[key]
    if not isinstance(value, int):
        raise TypeError(f"{key!r} must be an integer, got {value!r}.")
    return value
