<!-- This disables the "First line in file should be a top level heading" rule -->
<!-- markdownlint-disable MD041 -->
<a href="https://github.com/alexandrainst/gridfm_demo">
<img
 src="https://filedn.com/lRBwPhPxgV74tO0rDoe8SpH/alexandra/alexandra-logo.jpeg"
 width="239"
 height="175"
 align="right"
 alt="Alexandra Institute Logo"
/>
</a>

# GridFM Demo

Proof-of-concept showcasing the training process of a foundation model for the electric
grid (GridFM), and an example use case for the trained model within Power-to-X
positioning optimisation.

The repo builds on top of several existing open source initiatives aimed at building
general-purpose AI models for the grid, adapting them to datasets, training scenarios
and use cases relevant for the danish energy sector. To avoid issues related to data
privacy, this PoC generates its own synthetic data from purely fictional grid
topologies.

---

[![Code Coverage](https://img.shields.io/badge/Coverage-0%25-red.svg)](https://github.com/alexandrainst/gridfm_demo/tree/main/tests)

Developer:

- Étienne Bourbeau (<27770178+bourdeet@users.noreply.github.com>)

## Setup

### Nix development shell

A `flake.nix` is provided for developers using [Nix](https://nixos.org/). It supplies
all the programs needed to work on the project without any manual installation:

```bash
nix develop
```

Once inside the shell, continue with the installation steps below.

### Installation

1. Run `make install`, which sets up a virtual environment and all Python dependencies
   therein.
2. Run `source .venv/bin/activate` to activate the virtual environment.

### Adding and Removing Packages

To install new PyPI packages, run:

```bash
uv add <package-name>
```

To remove them again, run:

```bash
uv remove <package-name>
```

To show all installed packages, run:

```bash
uv pip list
```

### Formatting Markdown

To format all Markdown files (wraps prose at 88 characters and fixes linting issues),
run:

```bash
make format-markdown
```

This requires `prettier` and `markdownlint-cli2`.

## Repository Content

The project is structured intot he following subcomponents:

- `data_generation` handles the creation of synthetic grid data for training gridFM and
  test its performance. It relies on
  [gridfm-datakit](https://github.com/gridfm/gridfm-datakit) for generating the graph
  objects.
- `model_training` handles the centralized training process of gridFM and is based on
  [gridFM-graphkit](https://github.com/gridfm/gridfm-graphkit)
- `federated_learning` is an alternative way of training gridFM, using a federated
  learning framework called [APPFL](https://github.com/APPFL/APPFL). It adapts the
  graphkit training tools for use within the federated learning framework.
- `use_cases` includes various analyses of the trained model performance, showing how
  the model's accuracy and latency compares with standard power flow solvers. It also
  includes an example use of the final model within an optimisation task inspired by
  real challenges faced by TSO's.
