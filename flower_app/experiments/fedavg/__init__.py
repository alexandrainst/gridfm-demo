"""FedAvg over the base graphkit model."""

from ...interface import Experiment
from .client import evaluate, train
from .server import main

EXPERIMENT: Experiment = Experiment(
    server_main=main, client_train=train, client_evaluate=evaluate
)
