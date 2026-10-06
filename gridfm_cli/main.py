"""The `gridfm` command-line interface for running the demo."""

import logging
import typing as t

import typer

from .choices import choose_experiment, choose_federation
from .compose import compose
from .data import clients_without_data, delete_data, generate_data
from .flower import run_experiment
from .paths import OUTPUTS_DIR

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="Run federated learning experiments on local Flower federations.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_show_locals=False,
)

FederationArgument = t.Annotated[
    str | None,
    typer.Argument(
        help="Folder in federations/. Asked for if left out.", show_default=False
    ),
]
ExperimentArgument = t.Annotated[
    str | None,
    typer.Argument(
        help="Package in flower_app/experiments/. Asked for if left out.",
        show_default=False,
    ),
]


@app.callback()
def main() -> None:
    """Run federated learning experiments on local Flower federations."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


@app.command(help="Generate the synthetic data of each client in a federation.")
def data(
    federation: FederationArgument = None,
    force: t.Annotated[
        bool, typer.Option("--force", help="Regenerate data that already exists.")
    ] = False,
) -> None:
    """Generate the synthetic data of each client in a federation.

    Args:
        federation:
          Name of the federation, or `None` to ask the user.
        force:
          Whether to regenerate the data of clients that already have data.
    """
    generate_data(federation=choose_federation(federation=federation), force=force)


@app.command(help="Build the Docker images of a federation.")
def build(federation: FederationArgument = None) -> None:
    """Build the Docker images of a federation.

    Args:
        federation:
          Name of the federation, or `None` to ask the user.
    """
    compose(federation=choose_federation(federation=federation), args=["build"])


@app.command(help="Start a federation in the background.")
def up(federation: FederationArgument = None) -> None:
    """Start a federation in the background.

    Args:
        federation:
          Name of the federation, or `None` to ask the user.

    Raises:
        typer.Exit:
          With code 1 if a client of the federation has no generated data. The
          clients and the command that generates their data are logged.
    """
    chosen = choose_federation(federation=federation)
    missing = clients_without_data(federation=chosen)
    if missing:
        logger.error(
            f"The clients {', '.join(missing)} of {chosen} have no data. Generate it "
            f"with:\n\n    uv run gridfm data {chosen}\n"
        )
        raise typer.Exit(code=1)
    # Docker would create the mounted folder as root if it did not exist.
    OUTPUTS_DIR.mkdir(exist_ok=True)
    compose(federation=chosen, args=["up", "-d", "--build"])


@app.command(help="Run an experiment on the running federation and stream its logs.")
def run(experiment: ExperimentArgument = None) -> None:
    """Run an experiment on the running federation and stream its logs.

    Args:
        experiment:
          Name of the experiment, or `None` to ask the user.
    """
    run_experiment(experiment=choose_experiment(experiment=experiment))


@app.command(help="Stop a federation and remove its containers.")
def down(federation: FederationArgument = None) -> None:
    """Stop a federation and remove its containers.

    Args:
        federation:
          Name of the federation, or `None` to ask the user.
    """
    compose(federation=choose_federation(federation=federation), args=["down"])


@app.command(help="Delete the generated data of a federation.")
def clean(
    federation: FederationArgument = None,
    yes: t.Annotated[
        bool,
        typer.Option("--yes", "-y", help="Delete without asking for confirmation."),
    ] = False,
) -> None:
    """Delete the generated data of a federation.

    Args:
        federation:
          Name of the federation, or `None` to ask the user.
        yes:
          Whether to skip the confirmation.
    """
    delete_data(federation=choose_federation(federation=federation), confirm=not yes)
