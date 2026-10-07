"""Client side of the isolated training experiment."""

import lightning as L
import numpy as np
from flwr.app import ConfigRecord, Context, Message, MetricRecord, RecordDict

from ...interface import ClientDataset, ClientPaths
from .graphkit_config import GRAPHKIT_CONFIG
from .task import build_task_and_datamodule
from .trainer import make_trainer


def train(
    msg: Message, context: Context, dataset: ClientDataset, paths: ClientPaths
) -> Message:
    """Train the received model on this client's data and evaluate it on the same.

    Args:
        msg:
          Message with the initial model under `"arrays"`, and `"local-epochs"`
          and `"seed"` under `"config"`.
        context:
          Context of the ClientApp.
        dataset:
          Dataset of this client.
        paths:
          Log directory of this client.

    Returns:
        Reply with the validation `"loss"` of the trained model and `"num-examples"`
        under `"metrics"`.
    """
    config = msg.content.config_records["config"]
    local_epochs = _config_int(config=config, key="local-epochs")
    entropy = [_config_int(config=config, key="seed"), dataset.client_id]
    # `SeedSequence` mixes the run's seed and the client into one 32-bit seed, so each
    # client shuffles differently while runs repeat.
    client_seed = int(np.random.SeedSequence(entropy=entropy).generate_state(1)[0])
    L.seed_everything(seed=client_seed, workers=True, verbose=False)
    task, data_module = build_task_and_datamodule(
        graphkit_config=GRAPHKIT_CONFIG, dataset=dataset
    )
    task.load_state_dict(msg.content.array_records["arrays"].to_torch_state_dict())

    trainer = make_trainer(max_epochs=local_epochs, log_dir=paths.log_dir)
    trainer.fit(model=task, datamodule=data_module)
    results = trainer.validate(model=task, datamodule=data_module, verbose=False)
    val_loss = float(results[0].get("Validation loss", 0.0)) if results else 0.0
    num_examples = sum(len(d) for d in data_module.val_datasets)

    reply = RecordDict(
        {"metrics": MetricRecord({"loss": val_loss, "num-examples": num_examples})}
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
