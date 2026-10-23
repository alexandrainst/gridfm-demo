"""FedAvg over the graphkit model at graphkit's default size."""

from ...interface import Experiment
from .client import evaluate, train
from .server import main

EXPERIMENT: Experiment = Experiment(
    server_main=main, client_train=train, client_evaluate=evaluate
)
