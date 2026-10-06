# Federated Learning with Flower

This subfolder trains a GridFM model in a federated setting using
[Flower](https://flower.ai/). Two clients each hold a private synthetic power-grid
dataset generated locally by
[`gridfm-datakit`](https://github.com/gridfm/gridfm-datakit) and a server coordinates
the federated learning such that the clients cooperatively train a
[`gridfm-graphkit`](https://github.com/gridfm/gridfm-graphkit) model.

## Quickstart

### Generate Synthetic Dataset

Generate one synthetic dataset per client under
`data/federated_learning/client_{0,1}/case14_ieee/raw/*.parquet` with:

```bash
make flower-data
```

The difference between the two synthetic datasets originates from their different seeds,
see `settings.seed` in `src/federated_learning/config/datakit_client_{0,1}.yaml`.

### Deploy Federated Learning Framework

Deploy the federated learning framework with:

```bash
make flower-up
```

This command binds and mounts each client's data directory into its `clientapp`
container, then brings up the full Flower stack (`SuperLink`, two `SuperNode`s, one
`ServerApp`, two `ClientApp`s). See [Architecture](./README.md#architecture) for further
information about the different components in the flower stack.

### Run Experiment

Run a flower experiment with:

```bash
make flower-run
```

This command submits the run defined by the settings in
[`pyproject.toml`](./../../pyproject.toml) of the form `[tool.flwr.*]`.

### Clean Up

Remove the deployed flower framework with:

```bash
make flower-down
```

This command will remove the running containers.

Remove the generated data with:

```bash
make flower-clean-data
```

This command will remove all files in the folder
[`data/federated_learning`](./../../data/federated_learning/)

## Architecture

This section servers as a brief summary of the flower architecture. It provides users of
this project with an overview of the different components in the flower stack. Refer to
the flower documentation
[flower.ai/docs/framework/explanation-flower-architecture](https://flower.ai/docs/framework/explanation-flower-architecture.html)
for further information.

### Components

- SuperLink: control-plane container responsible for routing messages between the server
  and clients. This container also stores the run state.
- SuperNode: client-side long-running daemon. Owns a local data partition and dials into
  the SuperLink. Forwards work to its ClientApp container.
- SuperExec: the executor process (`flower-superexec`) running in the `serverapp` and
  `clientapp` containers. Receives the Flower App Bundle (FAB) from SuperLink or
  SuperNode and spawns the ServerApp or ClientApp as a subprocess.
- ServerApp: aggregation + strategy. Runs as a subprocess spawned by the `serverapp`
  container's SuperExec for the duration of a run.
- ClientApp: per-round data-loading + model training. Runs as a subprocess spawned by
  each `clientapp` container's SuperExec on every incoming message.

The deployment uses [process isolation mode](https://flower.ai/docs/framework/):
`ServerApp` and `ClientApp` do not run inside `SuperLink`/`SuperNode`, but in separate
containers. This physically separates the training runtime from the Flower control plane
and mirrors a production deployment.

### Run Lifecycle

Submitting `uv run flwr run . local-deployment --stream`:

- The `flwr` CLI reads the `[tool.flwr.*]` sections of the root `pyproject.toml`.
- `server_app.py` and `client_app.py` (plus imports) are zipped into a Flower App Bundle
  (FAB) and uploaded to the SuperLink via the Exec API.
- The SuperLink ships the FAB to the connected SuperExec containers.
- The `serverapp` container installs the FAB and spawns a subprocess that runs the
  `ServerApp` for the duration of the run.
- The `ServerApp` sends messages to clients via the SuperLink, which routes each message
  to the corresponding SuperNode, which then forwards it to its `clientapp` container.
- Each `clientapp` container installs the FAB (once) and spawns a fresh subprocess per
  incoming message to run the `ClientApp`.
- Each `ClientApp` reads its local data partition from the bind-mounted volume, performs
  `local-epochs` of Lightning training, and returns the updated weights.
- Results are communicated back to the `serverapp` via the SuperNode and SuperLink.
