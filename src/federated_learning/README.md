# Federated Learning with Flower

This subfolder deploys the "getting started" example from the federated learning
framework [Flower](https://flower.ai/). The full stack runs locally via `docker`.

> TODO: The current implementation is Flower's NumPy quickstart and serves as a simple
> starting point. This subfolder should train a GridFM in a federated setting using the
> open-source federated learning framework [Flower](https://flower.ai/). We should
> replace quickstart example with grid data generated using gridfm-datakit and train a
> model with gridfm-graphkit. It should be possible to preserve the overall structure of
> the deployment.

## Local Deployment

Deploy the Flower framework using `docker-compose`:

```bash
docker compose -f src/federated_learning/docker-compose.yml up -d --build   # start
docker compose -f src/federated_learning/docker-compose.yml down            # stop
```

Or via the `make` targets from the root of the project:

```bash
make flower-up
make flower-down
```

## Running an experiment

Run the flower experiment with the command:

```bash
uv run flwr run . local-deployment --stream
```

Or using the make target from the project root:

```bash
make flower-run
```

## Architecture

### Components

The deployment is composed of the following Flower components:

- [SuperLink](https://flower.ai/docs/framework/): The server-side long-running control
  plane container. This component is responsible for routing messages between the server
  and clients and storing run state.
- [SuperNode](https://flower.ai/docs/framework/): The client-side long-running daemon
  container. Owns a local data partition and dials into the SuperLink. The component is
  responsible for forwarding work to its ClientApp container.
- [SuperExec](https://flower.ai/docs/framework/): The executor process
  (`flower-superexec`) running in the `serverapp` and `clientapp` containers. This
  component is responsible for receiving the Flower App Bundle (FAB) from SuperLink or
  SuperNode and spawning the ServerApp or ClientApp as a subprocess. This is the
  container performing the actual work. For more information about the FAB refer to
  [flower.ai/docs/framework/how-to-configure-pyproject-toml.html](https://flower.ai/docs/framework/how-to-configure-pyproject-toml.html).
- [ServerApp](https://flower.ai/docs/framework/): This component contains the
  aggregation and strategy logic. Runs as a subprocess spawned by the `serverapp`
  container's SuperExec for the duration of a run.
- [ClientApp](https://flower.ai/docs/framework/): the client-side per-round logic
  responsible for data loading and model training. Runs as a subprocess spawned by each
  `clientapp` container's SuperExec on every incoming message.

The current implementation uses
[process isolation mode](https://flower.ai/docs/framework/), such that the `ServerApp`
and `ClientApp` do not run inside SuperLink or SuperNode but in separate containers.
This physically separates the runtime environment of the model training from the Flower
control plane.

The local deployment aims to mirror a production deployment with a control-plane
container coordinating multiple client-side worker containers. This should make it easy
to apply the current demo in a production setting.

### Run Lifecycle

When a Flower experiment is run with `uv run flwr run . local-deployment --stream` then
the following actions take place:

- The `flwr` CLI reads the `[tool.flwr.*]` sections of the root `pyproject.toml`
- The files `server_app.py` and `client_app.py` (plus any modules they import) are
  zipped into a Flower App Bundle (FAB)
- The FAB is uploaded to the SuperLink via the Exec API.
- The SuperLink sends the FAB to the connected SuperExec containers.
- The `serverapp` container installs the FAB and spawns a subprocess that runs the
  `ServerApp` for the duration of the run.
- The `ServerApp` sends messages to clients via the SuperLink which routes each message
  to the corresponding SuperNode which then forwards it to its `clientapp` container.
- Each `clientapp` container installs the FAB (once) and spawns a fresh subprocess per
  incoming message to run the `ClientApp`.
- The result of the `clientapp` is communated back to the `serverapp` via the SuperNode
  and SuperLink.
