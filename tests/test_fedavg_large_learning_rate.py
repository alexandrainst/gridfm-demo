"""Tests for the learning rate of the `fedavg_large` experiment."""

import typing as t
from unittest import mock

import pytest
from flwr.app import ArrayRecord, ConfigRecord, MetricRecord
from flwr.serverapp.strategy import Strategy

from flower_app.experiments.fedavg_large.early_stopping import run_with_early_stopping
from flower_app.experiments.fedavg_large.learning_rate import PlateauLearningRate


def test_learning_rate_starts_at_the_initial_value() -> None:
    """The learning rate is the initial one before any step."""
    learning_rate = PlateauLearningRate(initial=0.1, decay=0.5, patience=1)
    assert learning_rate.value == pytest.approx(0.1)


def test_learning_rate_is_kept_while_the_loss_improves() -> None:
    """The learning rate does not decay while every loss is lower than the last."""
    learning_rate = PlateauLearningRate(initial=0.1, decay=0.5, patience=1)
    for loss in (1.0, 0.9, 0.8, 0.7):
        learning_rate.step(loss=loss)
    assert learning_rate.value == pytest.approx(0.1)


def test_learning_rate_decays_after_the_patience_without_improvement() -> None:
    """With a patience of one, two steps without improvement decay the rate."""
    learning_rate = PlateauLearningRate(initial=0.1, decay=0.5, patience=1)
    learning_rate.step(loss=1.0)
    learning_rate.step(loss=1.0)
    assert learning_rate.value == pytest.approx(0.1)
    learning_rate.step(loss=1.0)
    assert learning_rate.value == pytest.approx(0.05)


def test_rounds_send_the_decayed_learning_rate_to_the_clients() -> None:
    """Each round's training config holds the learning rate for that round."""
    strategy = mock.MagicMock(spec=Strategy)
    strategy.aggregate_train.return_value = (ArrayRecord(), MetricRecord())
    losses = [1.0, 1.0, 1.0, 1.0]
    strategy.aggregate_evaluate.side_effect = [
        MetricRecord({"loss": loss}) for loss in losses
    ]
    grid = mock.MagicMock()
    grid.send_and_receive.return_value = []

    result = run_with_early_stopping(
        strategy=t.cast(Strategy, strategy),
        grid=grid,
        initial_arrays=ArrayRecord(),
        train_config=ConfigRecord({"local-epochs": 1, "seed": 0}),
        learning_rate=PlateauLearningRate(initial=0.1, decay=0.5, patience=1),
        max_rounds=4,
        patience=10,
    )

    sent = [
        call.kwargs["config"]["learning-rate"]
        for call in strategy.configure_train.call_args_list
    ]
    assert sent == pytest.approx([0.1, 0.1, 0.1, 0.05])
    # The config of the other keys is kept, and the metrics record the rate used.
    assert strategy.configure_train.call_args.kwargs["config"]["local-epochs"] == 1
    assert result.train_metrics_clientapp[4]["learning-rate"] == pytest.approx(0.05)
