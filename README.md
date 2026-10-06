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

[![Code Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen.svg)](https://github.com/alexandrainst/gridfm_demo/tree/main/tests)

Developers:

- Étienne Bourbeau (<27770178+bourdeet@users.noreply.github.com>)
- Michael Iversen (<michael.iversen@alexandra.dk>)

## Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Docker](https://docs.docker.com/get-docker/) with Docker Compose
- [tree](https://oldmanprogrammer.net/source.php?dir=projects/tree)
- [Prettier](https://prettier.io/)
- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2)

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

## Repository Content

- `gridfm_demo/` is the Python package. Flower ships the project folder to the
  federation as is, so the package sits at the repo root rather than in `src/`.
  - `client_app.py` and `server_app.py` are the Flower ClientApp and ServerApp. They
      run the experiment named in the run config.
  - `interface.py` defines the entry points an experiment provides. `paths.py` holds
      the fixed container paths, and `node_config.py` reads each client's dataset from
      its SuperNode's node config.
  - `experiments/` holds one package per Flower experiment. `experiments/fedavg/`
      trains a [gridfm-graphkit](https://github.com/gridfm/gridfm-graphkit) model with
      FedAvg. The package holds only the code that Flower ships to the server and
      clients.
- `federations/` holds one folder per federation: the datakit configs of its clients
  (`datakit_config/`), their generated data (`data/`) and its Docker Compose file
  (`compose.yml`).
- `scripts/` holds the entry points run with `uv run`, such as dataset generation with
  [gridfm-datakit](https://github.com/gridfm/gridfm-datakit).
- `build/` holds the Dockerfiles of the Flower ServerApp and ClientApp images.
- `docs/` holds background material and example configs.

## Federated Learning

[Flower](https://flower.ai/) trains the model in a federated setting. Generate a
dataset, start the federation, run an experiment and stop the federation with:

```bash
make flower-data FEDERATION=case14_2clients
make flower-up FEDERATION=case14_2clients
make flower-run EXPERIMENT=fedavg
make flower-down FEDERATION=case14_2clients
```

The values shown are the defaults. See [`federations/README.md`](federations/README.md)
for the deployment, the run outputs and how to add an experiment.
