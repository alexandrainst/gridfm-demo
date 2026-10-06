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
