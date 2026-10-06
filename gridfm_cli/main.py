"""The `gridfm` command-line interface for running the demo."""

import logging
import typing as t

import typer

from .choices import choose_experiment, choose_federation
from .compose import compose, is_up
from .data import clients_without_data, delete_data, generate_data
from .flower import run_experiment, superlink_address, superlink_is_reachable
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

    With `force`, exits with code 1 if the federation is up.

    Args:
        federation:
          Name of the federation, or `None` to ask the user.
        force:
          Whether to regenerate the data of clients that already have data.
    """
    chosen = choose_federation(federation=federation)
    if force:
        _require_down(federation=chosen)
    generate_data(federation=chosen, force=force)


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

    Raises:
        typer.Exit:
          With code 1 if no SuperLink accepts connections at the address of the
          Flower federation. The command that starts a federation is logged.
    """
    chosen = choose_experiment(experiment=experiment)
    if not superlink_is_reachable():
        logger.error(
            f"No federation is running at {superlink_address()}. Start one with:"
            "\n\n    uv run gridfm up <federation>\n"
        )
        raise typer.Exit(code=1)
    run_experiment(experiment=chosen)


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

    Exits with code 1 if the federation is up.

    Args:
        federation:
          Name of the federation, or `None` to ask the user.
        yes:
          Whether to skip the confirmation.
    """
    chosen = choose_federation(federation=federation)
    _require_down(federation=chosen)
    delete_data(federation=chosen, confirm=not yes)


def _require_down(federation: str) -> None:
    """Stop the command-line interface if a federation is up.

    Args:
        federation:
          Name of the federation.

    Raises:
        typer.Exit:
          With code 1 if a container of the federation is running. The command that
          stops the federation is logged.
    """
    if is_up(federation=federation):
        logger.error(
            f"{federation} is running and uses its data. Stop it first with:"
            f"\n\n    uv run gridfm down {federation}\n"
        )
        raise typer.Exit(code=1)
