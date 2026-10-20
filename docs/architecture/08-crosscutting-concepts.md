# 8. Cross-cutting Concepts

Five concepts cut across the gridfm CLI, the Flower driver, the experiments and the
federations:

- Configuration decides what a run does and comes from four places.
- Reproducibility ties the server's seed to every client.
- Data locality is what the demo exists to show, and the mounts and messages enforce it.
- Outputs and logs are split between the host and the containers.
- Testing covers the host side only.

## 8.1 Configuration

A run combines four layers of configuration, each owned by a different building block.

| Layer                         | Where                                               | Owner         | Decides                                                             |
| ----------------------------- | --------------------------------------------------- | ------------- | ------------------------------------------------------------------- |
| Run config                    | `[tool.flwr.app.config]` of `pyproject.toml`        | Flower driver | The experiment, and the experiment's keys in a table named after it |
| Node config                   | `--node-config` of each SuperNode in `compose.yml`  | Federations   | The client's ID, data directory, networks and scenario counts       |
| gridfm-datakit configs        | `federations/<name>/datakit_config/client_<i>.yaml` | Federations   | What data is generated for each client                              |
| gridfm-graphkit configuration | `GRAPHKIT_CONFIG` in the experiment's package       | Experiments   | The model and the task                                              |

`flwr run --run-config` only overrides keys declared with a default in `pyproject.toml`,
and Flower flattens each experiment's table to `<experiment>.<key>`. The Flower driver
turns the node config into a `ClientDataset` and hands it to the experiment. The
gridfm-graphkit configuration is Python code because the FAB carries only `*.py`,
`*.toml` and `*.md` files.

## 8.2 Reproducibility

Each experiment seeds its random number generators from its `seed` run config key. The
server seeds before it builds the initial model and sends the seed with each training
message. Each client seeds from that seed, the round and its client ID, so every round
and client shuffles differently while runs with the same seed repeat. The client ID of a
client must therefore stay the same across runs, and a new experiment should seed the
same way.

## 8.3 Data Locality

A client's data never leaves its container. Each ClientApp container mounts only its own
client's folder under `federations/<name>/data/`. A client replies to the server with
model weights and metrics only. The server side writes the shared model and the metrics
to the run folder, which is the only path from the federation back to the host.

## 8.4 Outputs and Logging

The server side of an experiment writes its results, such as its metrics, to the
directory in `ServerPaths`, which is mounted from the host as
`outputs/<federation>/<experiment>/<timestamp>/`. An experiment that trains one shared
model also writes the model, `final_model.pt`, and the gridfm-graphkit configuration it
was built from, `graphkit_config.json`, so the run's folder alone is enough to rebuild
the model. In `metrics.json`, the last round under `evaluate_clientapp` holds the
validation loss of the final model on the clients' own data, averaged over clients.

Only the federation writes to `outputs/`. Results the host computes from a run, such as
predictions, go to their own top-level folder with the same
`<federation>/<experiment>/<timestamp>/` layout.

Clients write training logs inside their own containers, to the directory in
`ClientPaths`. The logs of the ServerApp and ClientApp containers show what happened in
a run.

## 8.5 Testing

The tests run on the host with pytest and cover only code that runs without the Docker
images, such as the conversion of a node config into a `ClientDataset`. The experiments
are checked by running them in a federation.
