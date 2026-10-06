"""Docker Compose commands on a federation."""

from .paths import federation_dir
from .process import capture, run


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


def is_up(federation: str) -> bool:
    """Return whether any container of a federation is running.

    Args:
        federation:
          Name of the federation.

    Returns:
        Whether `docker compose ps` lists a running container of the federation.
        `False` if `docker` is not installed or `docker compose ps` fails, such as
        when the Docker daemon is not running.
    """
    directory = federation_dir(federation=federation)
    container_ids = capture(
        command=[
            "docker",
            "compose",
            "-f",
            str(directory / "compose.yml"),
            "ps",
            "--status",
            "running",
            "--quiet",
        ],
        cwd=directory,
    )
    return bool(container_ids and container_ids.strip())
