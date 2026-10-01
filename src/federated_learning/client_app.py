"""ClientApp: simulated local training on a toy NumPy model."""

import numpy as np
from flwr.app import ArrayRecord, Context, Message, MetricRecord, RecordDict
from flwr.clientapp import ClientApp

app = ClientApp()


@app.train()
def train(msg: Message, context: Context) -> Message:
    """Simulate local training by perturbing the global arrays."""
    ndarrays = msg.content["arrays"].to_numpy_ndarrays()
    model = [m + np.random.rand(*m.shape) for m in ndarrays]

    content = RecordDict(
        {
            "arrays": ArrayRecord(model),
            "metrics": MetricRecord(
                {"random_metric": float(np.random.rand()), "num-examples": 1}
            ),
        }
    )
    return Message(content=content, reply_to=msg)


@app.evaluate()
def evaluate(msg: Message, context: Context) -> Message:
    """Return a dummy evaluation metric."""
    _ = msg.content["arrays"].to_numpy_ndarrays()

    content = RecordDict(
        {
            "metrics": MetricRecord(
                {"random_metric": np.random.rand(3).tolist(), "num-examples": 1}
            )
        }
    )
    return Message(content=content, reply_to=msg)
