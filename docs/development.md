# Development

This guide explains how this project works and how to extend it. It starts with the
parts of Flower that it relies on and the two ideas it is built around, experiments and
federations. It then describes what each part of the repository does and what a new
experiment or federation must contain, and it ends with the tools used during
development.

## Brief Introduction To Flower

Federated learning with [Flower](https://flower.ai/) uses a single server and one or
more clients. Each client trains on its own data, and the server combines the results
into a shared model. This repository runs the server and the clients as Docker
containers on the same machine. In production, they run on different machines.

Flower separates a federation into long-running infrastructure components and
short-lived apps
([Flower architecture](https://flower.ai/docs/framework/explanation-flower-architecture.html)).

The infrastructure components are long-running. They start with the federation and keep
running until the federation is stopped, across any number of runs:

- The SuperLink runs on the server. It accepts runs and routes messages between the
  server and the clients.
- A SuperNode runs on each client. It connects to the SuperLink and contains the
  client's node config, such as the location of its data.

The apps are short-lived. They contain the code of this project, start when a run starts
and stop when it ends:

- The ServerApp runs on the server next to the SuperLink and coordinates the training.
- A ClientApp runs on each client next to its SuperNode and trains on that client's
  data.

`flwr run` bundles the code of this project into a
[Flower App Bundle (FAB)](https://flower.ai/docs/framework/ref-api-cli.html) and uploads
it to the SuperLink, which passes it on to the SuperNodes. This project uses Flower's
[Docker deployment](https://flower.ai/docs/framework/docker/tutorial-quickstart-docker-compose.html),
where the ServerApp and each ClientApp run the FAB in their own container.

## Experiments and Federations

This project separates what is trained from where it is trained, and calls the two parts
experiments and federations. An experiment is the model together with the way it is
trained. It contains the code that the ServerApp and the ClientApps run, from the
strategy on the server to the local training and evaluation on the clients, but it makes
no assumptions about the data it trains on. Each experiment is a package in
`flower_app/experiments/` and is chosen by name in `uv run gridfm run`.

A federation describes where the training happens. It consists of the clients, the data
each of them contains and the Flower infrastructure components that connect them to the
server. Flower uses the word for the SuperLink and its SuperNodes only, so a federation
in this project is a wider idea that also includes the data. Each federation is a folder
in `federations/` and is chosen by name in the other `gridfm` commands. Because
experiments and federations are independent of each other, a run can train any
experiment on any federation.

## Project Components

- `flower_app/` contains the code in the FAB. The entry points `server_app.py` and
  `client_app.py` are set in `[tool.flwr.app.components]` of `pyproject.toml`. They are
  thin scaffolding: each looks up the experiment named in the run config and runs that
  experiment's server or client code. `interface.py` defines the interface between
  `server_app.py` and `client_app.py` and what an experiment provides.
- `flower_app/experiments/<name>/` contains one experiment. Each experiment must conform
  to the interface from `interface.py`.
- `federations/<name>/` contains one federation. `datakit_config/` contains one
  [gridfm-datakit](https://github.com/gridfm/gridfm-datakit) config per client, `data/`
  the data generated from them, and `compose.yml` the containers. Each SuperNode's node
  config tells its client where its data is.
- `build/` contains the Dockerfiles of the ServerApp and ClientApp images. They only
  install the dependencies, since the code arrives with each run in the FAB.
- `pyproject.toml` contains the run config defaults in `[tool.flwr.app.config]`, such as
  the number of rounds.
- `gridfm_cli/` contains the `gridfm` command-line interface. It generates the data,
  runs `docker compose` with a federation's `compose.yml` and submits experiments with
  `flwr run`.
- `docs/` contains background material and example configs.

## Adding an Experiment

An experiment is a package `flower_app/experiments/<name>/`. Its `__init__.py` defines
`EXPERIMENT`, an `Experiment` from `flower_app/interface.py` with three entry points:

- `server_main(grid, context, paths)` runs once per run on the server. It reads its
  settings from `context.run_config` under the keys `<name>.<key>`, sends messages to
  the clients through `grid`, for example with a Flower strategy, and writes its results
  to `paths.output_dir`. That is `outputs/<name>/<run-id>/` on the host.
- `client_train(msg, context, dataset, paths)` runs on a client for each train message
  and returns the reply. `dataset` contains the client's data directory, its networks
  and the maximum number of scenarios per network. `paths.log_dir` is for training logs.
  The client gets its settings from the server in `msg`, not from the run config.
- `client_evaluate(msg, context, dataset, paths)` does the same for evaluate messages.

The experiment imports nothing from `flower_app/` except `interface.py`. Its
configuration is Python code, because the FAB only contains `*.py`, `*.toml` and `*.md`
files. Any library it needs beyond those in `build/client/pyproject.toml` and
`build/server/pyproject.toml` must be added there, and the images rebuilt with
`uv run gridfm build <federation>`.

To make the experiment available:

1. Add it to `EXPERIMENTS` in `flower_app/experiments/__init__.py` under `<name>`.
2. Declare its run config keys with defaults in `[tool.flwr.app.config.<name>]` of
   `pyproject.toml`. `flwr run` only accepts keys declared there.
3. Run it with `uv run gridfm run <name>`.

To change a run config value for a single run, call `flwr run` directly:

```bash
uv run flwr run . local-deployment \
  --run-config "experiment='fedavg' fedavg.local-epochs=2" --stream
```

## Adding a Federation

A federation is a folder `federations/<name>/` with one datakit config per client and a
Docker Compose file. `federations/case14_2clients/` is an example with two clients.

- `datakit_config/client_<i>.yaml` is the
  [gridfm-datakit](https://github.com/gridfm/gridfm-datakit) config of client `<i>`,
  counting from 0. `network.name` selects the grid, and `settings.data_dir` must be
  `federations/<name>/data/client_<i>`. `uv run gridfm data <name>` generates the data
  of every client into `data/`.
- `compose.yml` starts one `superlink`, one `serverapp` built from `../../build/server`
  with `../../outputs` mounted at `/outputs`, and two services per client:
  - a SuperNode with its own ClientAppIO port and the node config
      `data-dir='/data/client_<i>' networks='<network.name>' scenarios='<count>'`.
      Several networks and their scenario counts are comma-separated.
  - a ClientApp built from `../../build/client` that connects to that SuperNode and
      mounts `./data/client_<i>` at `/data/client_<i>`.

Start the federation with `uv run gridfm up <name>`. FedAvg waits for at least two
clients, so a federation with one client never starts a FedAvg run.

## Tools

The development tools are
[tree](https://oldmanprogrammer.net/source.php?dir=projects/tree),
[Prettier](https://prettier.io/) and
[markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2). For users of
[Nix](https://nixos.org/), `flake.nix` provides uv and the development tools, but not
Docker. Start its shell with `nix develop`.

Set up the environment, then run the formatters, linters and type checkers, the tests
and the Markdown formatter:

```bash
make install
source .venv/bin/activate
make check
make test
make format-markdown
```
