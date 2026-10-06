"""Docker Compose commands on a federation."""

from .paths import federation_dir
from .process import run


def compose(federation: str, args: list[str]) -> None:
    """Run `docker compose` with the Compose file of a federation.

    Args:
        federation:
          Name of the federation.
        args:
          Arguments after `docker compose -f <compose file>`.
    """
    directory = federation_dir(federation=federation)
    run(
        command=["docker", "compose", "-f", str(directory / "compose.yml"), *args],
        cwd=directory,
    )
