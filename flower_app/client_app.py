"""The ClientApp: client side of the experiment named in the run config."""

from flwr.app import Context, Message
from flwr.clientapp import ClientApp

from .experiments import get_experiment
from .interface import ClientPaths
from .node_config import client_dataset
from .paths import CLIENT_LOG_DIR

app = ClientApp()


@app.train()
def train(msg: Message, context: Context) -> Message:
    """Handle a train message with the experiment's client.

    Args:
        msg:
          Train message from the server.
        context:
          Context of the ClientApp. Its run config holds `"experiment"` and its node
          config holds the keys read by `client_dataset`.

    Returns:
        The experiment's reply.
    """
    experiment = get_experiment(name=str(context.run_config["experiment"]))
    return experiment.client_train(
        msg=msg,
        context=context,
        dataset=client_dataset(context=context),
        paths=ClientPaths(log_dir=CLIENT_LOG_DIR),
    )


@app.evaluate()
def evaluate(msg: Message, context: Context) -> Message:
    """Handle an evaluate message with the experiment's client.

    Args:
        msg:
          Evaluate message from the server.
        context:
          Context of the ClientApp. Its run config holds `"experiment"` and its node
          config holds the keys read by `client_dataset`.

    Returns:
        The experiment's reply.
    """
    experiment = get_experiment(name=str(context.run_config["experiment"]))
    return experiment.client_evaluate(
        msg=msg,
        context=context,
        dataset=client_dataset(context=context),
        paths=ClientPaths(log_dir=CLIENT_LOG_DIR),
    )
