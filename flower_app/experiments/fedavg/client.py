"""Client side of the FedAvg experiment."""

from collections import OrderedDict

import lightning as L
import numpy as np
from flwr.app import (
    ArrayRecord,
    ConfigRecord,
    Context,
    Message,
    MetricRecord,
    RecordDict,
)

from ...interface import ClientDataset, ClientPaths
from .graphkit_config import GRAPHKIT_CONFIG
from .task import build_task_and_datamodule
from .trainer import make_trainer


def train(
    msg: Message, context: Context, dataset: ClientDataset, paths: ClientPaths
) -> Message:
    """Train the received model on this client's data.

    Args:
        msg:
          Message with the global model under `"arrays"`, and `"local-epochs"`,
          `"seed"` and `"server-round"` under `"config"`.
        context:
          Context of the ClientApp.
        dataset:
          Dataset of this client.
        paths:
          Log directory of this client.

    Returns:
        Reply with the updated model under `"arrays"` and `"num-examples"` under
        `"metrics"`.
    """
    config = msg.content.config_records["config"]
    local_epochs = _config_int(config=config, key="local-epochs")
    entropy = [
        _config_int(config=config, key="seed"),
        _config_int(config=config, key="server-round"),
        dataset.client_id,
    ]
    # `SeedSequence` mixes the run's seed, the round and the client into one 32-bit
    # seed, so each round and client shuffles differently while runs repeat.
    client_seed = int(np.random.SeedSequence(entropy=entropy).generate_state(1)[0])
    L.seed_everything(seed=client_seed, workers=True, verbose=False)
    task, data_module = build_task_and_datamodule(
        graphkit_config=GRAPHKIT_CONFIG, dataset=dataset
    )
    task.load_state_dict(msg.content.array_records["arrays"].to_torch_state_dict())

    trainer = make_trainer(max_epochs=local_epochs, log_dir=paths.log_dir)
    trainer.fit(model=task, datamodule=data_module)

    reply = RecordDict(
        {
            # Lightning annotates `state_dict()` as a `dict`, while Flower requires the
            # `OrderedDict` it returns at runtime.
            "arrays": ArrayRecord.from_torch_state_dict(OrderedDict(task.state_dict())),
            "metrics": MetricRecord(
                {"num-examples": len(data_module.train_dataset_multi)}
            ),
        }
    )
    return Message(content=reply, reply_to=msg)


def evaluate(
    msg: Message, context: Context, dataset: ClientDataset, paths: ClientPaths
) -> Message:
    """Evaluate the received model on this client's validation data.

    Args:
        msg:
          Message with the global model under `"arrays"`.
        context:
          Context of the ClientApp.
        dataset:
          Dataset of this client.
        paths:
          Log directory of this client.

    Returns:
        Reply with `"loss"` and `"num-examples"` under `"metrics"`.
    """
    task, data_module = build_task_and_datamodule(
        graphkit_config=GRAPHKIT_CONFIG, dataset=dataset
    )
    task.load_state_dict(msg.content.array_records["arrays"].to_torch_state_dict())

    trainer = make_trainer(max_epochs=1, log_dir=paths.log_dir)
    results = trainer.validate(model=task, datamodule=data_module, verbose=False)
    val_loss = float(results[0].get("Validation loss", 0.0)) if results else 0.0
    num_examples = sum(len(d) for d in data_module.val_datasets)

    reply = RecordDict(
        {"metrics": MetricRecord({"loss": val_loss, "num-examples": num_examples})}
    )
    return Message(content=reply, reply_to=msg)


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
