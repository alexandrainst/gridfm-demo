# Architecture

This project demonstrates how federated learning can train a foundation model for the
power grid. Several clients each hold their own synthetic power grid data, and a power
flow model from the Python library
[gridfm-graphkit](https://github.com/gridfm/gridfm-graphkit) is trained across them with
the federated learning framework [Flower](https://flower.ai/), without the data leaving
the clients. The project separates what is trained, an experiment, from where it is
trained, a federation, so that any experiment runs on any federation.

## Bird's Eye View

A run passes through three stages, all started from the `gridfm` command-line interface
on the host. First, the Python library
[gridfm-datakit](https://github.com/gridfm/gridfm-datakit) generates each client's
dataset on the host from that client's datakit config in the federation. Second,
[Docker Compose](https://docs.docker.com/compose/) starts the federation's containers.
The server side runs the SuperLink, Flower's coordinating server, and the ServerApp,
which runs the server side of the project's code. Each client runs a SuperNode, Flower's
client process that connects to the SuperLink, and a ClientApp, which runs the client
side of the project's code. Each ClientApp container mounts only its own client's data.

Third, Flower's command `flwr run` bundles the folder `flower_app/` into a Flower App
Bundle (FAB), the archive of code that Flower ships with each run, and submits it to the
SuperLink, which passes it on to the SuperNodes. The ServerApp and every ClientApp load
the experiment named in the run config, the settings Flower passes to one run. The
server side of the experiment sends train and evaluate messages to the clients, each
client trains and evaluates on its own data, and the server writes the metrics of the
run to an output folder that is mounted from the host.

## Code Map

### `federations/`

The folder `federations/` holds one folder per federation. Each contains a
gridfm-datakit config per client, the data generated from those configs, and a Docker
Compose file that defines the federation's containers. In the Compose file, the node
config of each SuperNode, the settings Flower gives that SuperNode, tells its client
where its data is and which networks it contains.

Invariant: the Compose file sets no top-level project name, so Docker Compose names the
project after the federation's folder and the containers of different federations stay
apart.

### `gridfm_cli/`

The folder `gridfm_cli/` holds the `gridfm` command-line interface, built with the
Python library [Typer](https://typer.tiangolo.com/). It generates and deletes client
data with gridfm-datakit, wraps `docker compose`, submits runs with `flwr run`, and
finds and prompts for federations, experiments and runs. Its `predict` command rebuilds
a finished run's model with gridfm-graphkit from the run's `graphkit_config.json` and
`final_model.pt`, and predicts the scenarios of the federation's clients on the host. It
writes the predictions to `predictions/`, never to `outputs/`, whose run folders belong
to the containers' root user.

Boundary: `gridfm_cli` runs on the host and is not part of the FAB. It controls the
federation only by running the `docker compose` and `flwr` commands.

Invariant: `gridfm_cli` never imports `flower_app`. It finds experiments by listing the
packages in `flower_app/experiments/`.

### `build/`

The folder `build/` holds the Dockerfiles and dependency lists of the ServerApp and
ClientApp images.

Invariant: the images contain no project code. They install only dependencies, and the
code arrives with each run in the FAB.

### `flower_app/`

The code shipped to the server and clients in the FAB. Its root holds only the Flower
driver: the ServerApp and ClientApp entry points, which look up the experiment named in
the run config and call its entry points, the conversion of a SuperNode's node config
into the client's dataset description, and the fixed paths inside the containers. Key
types: `Experiment`, which bundles an experiment's entry points, the protocols
`ServerMain` and `ClientHandler` that those entry points follow, and `ServerPaths`,
`ClientPaths` and `ClientDataset`, which the driver passes to them.

Boundary: these types are the contract between the Flower driver and the experiments. A
change to them changes every experiment.

Boundary: the FAB carries only `*.py`, `*.toml` and `*.md` files, so everything an
experiment needs at run time, including its configuration, is Python code.

Invariant: `flower_app` imports no project code outside the package, such as
`gridfm_cli` or `scripts/`.

### `flower_app/experiments/`

One package per experiment, registered by name in `EXPERIMENTS`. Each package defines an
`EXPERIMENT` with a server main, run once per run, and client train and evaluate
handlers, run once per message. `fedavg` trains the model with Flower's FedAvg strategy,
which averages the client models weighted by their number of training examples, and
`isolated` trains it on each client's own data only, as a baseline. Each package holds
its gridfm-graphkit configuration as `GRAPHKIT_CONFIG` and builds the gridfm-graphkit
task, the data module and the trainer of the deep learning framework
[Lightning](https://lightning.ai/docs/pytorch/stable/).

Invariant: an experiment imports nothing from `flower_app` except the contract types
above, and nothing from other experiments. Experiments that need the same helper each
keep their own copy.

Invariant: an experiment makes no assumption about the data it trains on. It learns the
client's networks and data location from the `ClientDataset` it receives.

Invariant: a client reads its settings from the server's messages, never from the run
config. Only the server side reads the experiment's run config keys.

### `scripts/`

The folder `scripts/` holds standalone scripts that run outside the federation, such as
builders of custom grids in the [MATPOWER](https://matpower.org/) case format and of
load profiles. Nothing in `flower_app` or `gridfm_cli` imports them.

### `notebooks/`

The folder `notebooks/` holds [marimo](https://marimo.io/) notebooks that look at the
results of runs. `scenarios.py` draws one scenario of one client as a network, with the
model's input, the power flow solution, the prediction and the error, using the files
that `gridfm predict` writes to `predictions/`.

Boundary: the notebooks only read files and plot. They never build or run a model, and
they import only the parts of `gridfm_cli` that do not import gridfm-graphkit.

### `tests/`

The folder `tests/` holds [pytest](https://docs.pytest.org/) tests of the code that runs
without the Docker images.

The Python library [torch_scatter](https://github.com/rusty1s/pytorch_scatter), which
gridfm-graphkit imports, is installed on the host as well as in the images, so tests can
import the experiments.

### `docs/`

The folder `docs/` holds background material on power flow data formats and example
configs for gridfm-datakit and gridfm-graphkit.

## Cross-Cutting Concerns

### Configuration

A run combines four layers of configuration. The run config, declared with defaults in
the project's manifest, names the experiment and holds the experiment's keys in a table
named after it. The node config of each SuperNode, set in the federation's Compose file,
describes the client's data. The gridfm-datakit configs in the federation decide what
data is generated. The gridfm-graphkit configuration of each experiment is Python code
in the experiment's package.

### Reproducibility

Each experiment seeds its random number generators from its `seed` run config key. The
server seeds before it builds the initial model and sends the seed with each training
message. Each client seeds from that seed, the round and its client ID, so the client ID
of a client must stay the same across runs.

### Outputs and Logging

The server side of an experiment writes its results, such as its metrics, to the
directory in `ServerPaths`, which is mounted from the host. An experiment that trains
one shared model also writes the model, `final_model.pt`, and the graphkit configuration
it was built from, `graphkit_config.json`, so the run's folder alone is enough to
rebuild the model. Clients write training logs inside their own containers. The logs of
the ServerApp and ClientApp containers show what happened in a run.

### Testing

The tests run on the host and cover only code that runs without the Docker images. The
experiments are checked by running them in a federation.
