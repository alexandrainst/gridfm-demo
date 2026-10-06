# GridFM Demo

Demonstration of how federated learning can train a foundation model for the power grid.
`README.md` covers usage and `docs/development.md` how the project works.

## Project

- `flower_app/` contains only the code shipped to the server and clients. Its root
  contains only the Flower driver. Code that does not run in the federation belongs in
  `scripts/`
- Experiments are packages in `flower_app/experiments/<name>/`, registered in
  `flower_app/experiments/__init__.py`. They import nothing from `flower_app/` except
  `interface.py`, and their configuration is Python code
- Run config defaults are in `[tool.flwr.app.config.<name>]` of `pyproject.toml`
- The `gridfm` command-line interface is the `gridfm_cli` package. Federations are in
  `federations/<name>/`, Dockerfiles in `build/`, scripts in `scripts/`, tests in
  `tests/` and example configs in `docs/examples/`
- Tests cannot import the experiments, since `torch_scatter` is only installed in the
  Docker images

## Workflow

- Run everything with `uv run`. Add packages to `pyproject.toml` with
  `uv add <package>`, or `uv add --group=dev <package>` for development dependencies,
  never with `requirements.txt`
- Do not read entire files. Find the relevant lines with command-line tools and read
  only those
- Run `make check` for formatters, linters and type checkers, and `make test` for the
  tests. `make tree` shows the directory structure

## Python

- Use established packages rather than reimplementing what they solve
- Prefer many small, focused modules over few large ones
- Fit code within 88 characters
- Put all imports at the top of the file, unless that causes a circular import, which a
  comment next to the import must state
- Use f-strings, never %-formatting, and a logger, never `print`
- Order functions and classes from high-level to low-level, with `main` first
- Import with relative imports inside a package, and absolute imports in scripts and
  tests
- Always call functions with keyword arguments
- Prefix protected functions and methods with a single underscore
- Fully type-annotate all functions, methods and variables with Python 3.12+ syntax:
  `list[T]`, `X | Y`, `X | None`
- Use `import typing as t` and `import collections.abc as c`, and take `Iterable`,
  `Generator` and `Callable` from `c`
- Avoid `Any`. Prefer a `t.TypeVar` with a meaningful name. `dict[str, t.Any]` is fine
  for mixed values, `list[t.Any]` is not
- Use the `None` return type, never `NoReturn`

## Documentation

- Docstrings are reference documentation. They describe the contract of the unit: what
  it does, its arguments, return value, raised exceptions, side effects and invariants.
  They do not describe the implementation, teach, give recipes, explain history or
  design reasons, or restate what the signature already says
- Implementation details and the reasons behind them go in inline comments next to the
  code. Tutorials and how-to guides go in Markdown files
- Use single backticks for code in docstrings, e.g., `x` or `None`
- Use ASCII rather than Unicode, e.g., `->` rather than an arrow
- Use Google-style docstrings for all public functions, classes and modules, with a
  newline after each argument and exception name:

    ```python
    def process_items(items: list[Item]) -> list[Result]:
        """Process items and return results.

        Args:
            items:
              List of items to process.

        Returns:
            List of processed results.

        Raises:
            ValueError:
              If items list is empty.
        """
    ```
