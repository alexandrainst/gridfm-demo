"""ClientApp: local GridFM training over one federated round."""

import lightning as L
from flwr.app import ArrayRecord, Context, Message, MetricRecord, RecordDict
from flwr.clientapp import ClientApp
from gridfm_graphkit.datasets.hetero_powergrid_datamodule import LitGridHeteroDataModule
from gridfm_graphkit.io.param_handler import NestedNamespace, get_task
from lightning.pytorch.loggers import CSVLogger

from src.federated_learning.config.graphkit_config import GRAPHKIT_CONFIG

app = ClientApp()


def _build_task_and_datamodule(
    partition_id: int,
) -> tuple[L.LightningModule, LitGridHeteroDataModule]:
    config_args = NestedNamespace(**GRAPHKIT_CONFIG)

    data_module = LitGridHeteroDataModule(
        args=config_args, data_dir=f"/data/client_{partition_id}"
    )
    data_module.setup("fit")
    task = get_task(config_args, data_module.data_normalizers)
    return task, data_module


def _make_trainer(max_epochs: int) -> L.Trainer:
    return L.Trainer(
        max_epochs=max_epochs,
        accelerator="cpu",
        devices=1,
        logger=CSVLogger(save_dir="/tmp/flower_lightning_logs"),
        enable_checkpointing=False,
        enable_progress_bar=False,
        num_sanity_val_steps=0,
    )


@app.train()
def train(msg: Message, context: Context) -> Message:
    """Run one federated training round on this client's local data."""
    partition_id = int(context.node_config["partition-id"])
    local_epochs = int(msg.content["config"]["local-epochs"])

    task, data_module = _build_task_and_datamodule(partition_id=partition_id)
    task.load_state_dict(msg.content["arrays"].to_torch_state_dict())

    _make_trainer(max_epochs=local_epochs).fit(model=task, datamodule=data_module)

    reply = RecordDict(
        {
            "arrays": ArrayRecord.from_torch_state_dict(task.state_dict()),
            "metrics": MetricRecord(
                {"num-examples": len(data_module.train_dataset_multi)}
            ),
        }
    )
    return Message(content=reply, reply_to=msg)


@app.evaluate()
def evaluate(msg: Message, context: Context) -> Message:
    """Evaluate the global model on this client's local validation set."""
    partition_id = int(context.node_config["partition-id"])
    task, data_module = _build_task_and_datamodule(partition_id=partition_id)
    task.load_state_dict(msg.content["arrays"].to_torch_state_dict())

    results = _make_trainer(max_epochs=1).validate(
        model=task, datamodule=data_module, verbose=False
    )
    val_loss = float(results[0].get("Validation loss", 0.0)) if results else 0.0
    num_examples = sum(len(d) for d in data_module.val_datasets)

    reply = RecordDict(
        {"metrics": MetricRecord({"loss": val_loss, "num-examples": num_examples})}
    )
    return Message(content=reply, reply_to=msg)
