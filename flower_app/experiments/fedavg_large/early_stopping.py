"""Federated rounds that stop when the global validation loss stops improving."""

import typing as t
from logging import INFO

from flwr.app import ArrayRecord, ConfigRecord, MetricRecord
from flwr.common.logger import log
from flwr.serverapp import Grid
from flwr.serverapp.strategy import Result, Strategy


def run_with_early_stopping(
    strategy: Strategy,
    grid: Grid,
    initial_arrays: ArrayRecord,
    train_config: ConfigRecord,
    max_rounds: int,
    patience: int,
) -> Result:
    """Run training and evaluation rounds until the validation loss stops improving.

    Each round trains on the clients, aggregates their models, evaluates the
    aggregated model on the clients and aggregates their metrics. The run stops after
    `patience` consecutive rounds without a strictly lower aggregated `"loss"`, or
    after `max_rounds` rounds.

    Args:
        strategy:
          Strategy that configures and aggregates the rounds.
        grid:
          Grid connecting the ServerApp to the SuperNodes.
        initial_arrays:
          Global model of the first round.
        train_config:
          Config sent to the clients in every training round.
        max_rounds:
          Maximum number of rounds.
        patience:
          Number of consecutive rounds without improvement after which the run stops.

    Returns:
        The metrics of every round, and under `arrays` the global model of the round
        with the lowest aggregated validation loss.
    """
    result = Result()
    arrays = initial_arrays
    best_loss = float("inf")
    rounds_without_improvement = 0

    # The round body follows `Strategy.start` of Flower 1.23 without its checks for
    # missing replies: the aggregates are `None` only if no client replied, and the
    # run then fails.
    for current_round in range(1, max_rounds + 1):
        train_replies = grid.send_and_receive(
            messages=strategy.configure_train(
                server_round=current_round,
                arrays=arrays,
                config=train_config,
                grid=grid,
            )
        )
        arrays, train_metrics = t.cast(
            tuple[ArrayRecord, MetricRecord],
            strategy.aggregate_train(server_round=current_round, replies=train_replies),
        )
        result.train_metrics_clientapp[current_round] = train_metrics

        evaluate_replies = grid.send_and_receive(
            messages=strategy.configure_evaluate(
                server_round=current_round,
                arrays=arrays,
                config=ConfigRecord(),
                grid=grid,
            )
        )
        evaluate_metrics = t.cast(
            MetricRecord,
            strategy.aggregate_evaluate(
                server_round=current_round, replies=evaluate_replies
            ),
        )
        result.evaluate_metrics_clientapp[current_round] = evaluate_metrics
        loss = t.cast(float, evaluate_metrics["loss"])
        log(INFO, f"Round {current_round}: validation loss {loss:.6g}.")

        if loss < best_loss:
            result.arrays, best_loss = arrays, loss
            rounds_without_improvement = 0
        else:
            rounds_without_improvement += 1
        if rounds_without_improvement >= patience:
            break

    return result
