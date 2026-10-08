"""Discovery and selection of federations and experiments."""

import sys

import click
import typer

from .paths import EXPERIMENTS_DIR, FEDERATIONS_DIR
from .runs import Run, list_runs, missing_model_files


def choose_federation(federation: str | None) -> str:
    """Return a federation, asking the user to choose one if none is given.

    Fails with `typer.BadParameter` if the name is unknown, or if no name is given
    and stdin is not a terminal.

    Args:
        federation:
          Name of the federation, or `None` to ask the user.

    Returns:
        The name of an existing federation.
    """
    options = sorted(path.parent.name for path in FEDERATIONS_DIR.glob("*/compose.yml"))
    return _choose(kind="federation", value=federation, options=options)


def choose_experiment(experiment: str | None) -> str:
    """Return an experiment, asking the user to choose one if none is given.

    Experiments are the packages in `flower_app/experiments/`. A package that is not
    registered in `EXPERIMENTS` is offered as well, and fails when the run starts.
    Fails with `typer.BadParameter` if the name is unknown, or if no name is given
    and stdin is not a terminal.

    Args:
        experiment:
          Name of the experiment, or `None` to ask the user.

    Returns:
        The name of an existing experiment.
    """
    options = sorted(path.parent.name for path in EXPERIMENTS_DIR.glob("*/__init__.py"))
    return _choose(kind="experiment", value=experiment, options=options)


def choose_run(federation: str, run: str | None) -> Run:
    """Return a run of a federation, asking the user to choose one if none is given.

    A given name may be any run of the federation. The runs offered to the user are
    only those whose model can be rebuilt. Fails with `typer.BadParameter` if the
    name is unknown, if no name is given and stdin is not a terminal, or if no run
    can be offered.

    Args:
        federation:
          Name of the federation.
        run:
          Name of the run as `<experiment>/<timestamp>`, or `None` to ask the user.

    Returns:
        The chosen run.
    """
    runs = {candidate.name: candidate for candidate in list_runs(federation=federation)}
    if run is None:
        usable = [
            name
            for name, candidate in runs.items()
            if not missing_model_files(run=candidate)
        ]
        return runs[_choose(kind="run with a model", value=None, options=usable)]
    return runs[_choose(kind="run", value=run, options=list(runs))]


def _choose(kind: str, value: str | None, options: list[str]) -> str:
    """Validate a given name, or ask the user to choose one of the options.

    Args:
        kind:
          What is being chosen, used in prompts and errors.
        value:
          The given name, or `None` to ask the user.
        options:
          The valid names.

    Returns:
        A name from `options`.

    Raises:
        typer.BadParameter:
          If there are no options, if `value` is not one of them, or if `value` is
          `None` and stdin is not a terminal.
    """
    if not options:
        raise typer.BadParameter(f"No {kind}s found.")
    listing = ", ".join(options)
    if value is None:
        if not sys.stdin.isatty():
            raise typer.BadParameter(f"No {kind} given. Choose one of: {listing}.")
        return _prompt(kind=kind, options=options)
    if value not in options:
        raise typer.BadParameter(f"Unknown {kind} {value!r}. Choose one of: {listing}.")
    return value


def _prompt(kind: str, options: list[str]) -> str:
    """Ask the user to choose one of the options by number.

    Args:
        kind:
          What is being chosen, used in the prompt.
        options:
          The names to choose from.

    Returns:
        The chosen name.
    """
    for number, option in enumerate(options, start=1):
        typer.echo(f"{number}) {option}")
    number = typer.prompt(f"Choose a {kind}", type=click.IntRange(1, len(options)))
    return options[number - 1]
