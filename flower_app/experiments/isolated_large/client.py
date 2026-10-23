"""Client side of the large isolated training experiment."""

import lightning as L
import numpy as np
from flwr.app import ConfigRecord, Context, Message, MetricRecord, RecordDict
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
        Reply with the lowest validation `"loss"` of any epoch and `"num-examples"`
        under `"metrics"`.
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
    trainer = make_trainer(
        max_epochs=max_epochs, log_dir=paths.log_dir, callbacks=[early_stopping]
    )
    trainer.fit(model=task, datamodule=data_module)
    best_loss = float(early_stopping.best_score)
    num_examples = sum(len(d) for d in data_module.val_datasets)

    reply = RecordDict(
        {"metrics": MetricRecord({"loss": best_loss, "num-examples": num_examples})}
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
