"""Execution of external commands."""

import logging
import shutil
import subprocess
from pathlib import Path

import typer

logger = logging.getLogger(__name__)


def run(command: list[str], cwd: Path) -> None:
    """Run an external command and stop the command-line interface if it fails.

    Args:
        command:
          The program followed by its arguments.
        cwd:
          Working directory of the command.

    Raises:
        typer.Exit:
          If the program is not installed, with exit code 1, or if the command fails,
          with the exit code of the command.
    """
    if shutil.which(command[0]) is None:
        logger.error(f"'{command[0]}' is not installed or not on the PATH.")
        raise typer.Exit(code=1)
    # The command prints its own errors, so a failure ends the CLI without a traceback.
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


def capture(command: list[str], cwd: Path) -> str | None:
    """Run an external command and return its standard output.

    The standard error of the command is logged at debug level.

    Args:
        command:
          The program followed by its arguments.
        cwd:
          Working directory of the command.

    Returns:
        The standard output of the command, or `None` if the program is not installed
        or the command fails.
    """
    if shutil.which(command[0]) is None:
        logger.debug(f"'{command[0]}' is not installed or not on the PATH.")
        return None
    result = subprocess.run(
        command, cwd=cwd, check=False, capture_output=True, text=True
    )
    if result.stderr:
        logger.debug(result.stderr)
    if result.returncode != 0:
        return None
    return result.stdout
