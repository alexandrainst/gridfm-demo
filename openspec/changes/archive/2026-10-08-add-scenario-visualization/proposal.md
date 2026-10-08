# Proposal

## Why

The demo reports a trained model only as loss curves in `metrics.json`. Nothing shows
what the model actually predicts for a grid, so it is hard to judge or present how well
federated training works. We want to pick a scenario and see the network in 2D with the
model's inputs, the true power flow solution and the model's prediction side by side.

## What Changes

- The FedAvg experiment also writes `graphkit_config.json` next to `final_model.pt`: a
  snapshot of the graphkit configuration the model was built from. A run folder then
  holds everything needed to rebuild the model, even after `graphkit_config.py` changes.
- A new command, `gridfm predict [FEDERATION] [RUN]`, runs on the host. It loads a run's
  model, refits the data normalizer on each client's data the way the client did during
  training, and predicts every scenario of every client in the federation. It writes one
  Parquet file per client to `predictions/<federation>/<experiment>/<run>/`, a
  host-owned and gitignored tree that mirrors `outputs/`. It does not write into
  `outputs/`, whose run folders belong to `root` because the ServerApp container runs as
  root.
- A new marimo notebook, `notebooks/scenarios.py`, only plots. It offers a dropdown of
  runs that have predictions, a dropdown of clients, a number input for the scenario and
  a choice of bus feature (Vm, Va, Pg or Qg). It draws the network with a NetworkX
  layout four times, for the truth, the prediction, the input and the error, and shows a
  table with one row per bus. It shows the split of the chosen scenario, lists the
  scenarios of each split, and opens with text on its prerequisites and how to read it.
- `torch-scatter`, which graphkit imports, becomes a dependency of the project, built
  from source on the host. Until now only the Docker images installed it.
- The rule in `AGENTS.md` that tests cannot import code needing `torch_scatter`, and the
  matching comment on `testpaths` in `pyproject.toml`, are updated.
- Out of scope: branch flows and line loading, scenario presets from datakit's
  statistics, predictions on data outside the federation, and experiments that do not
  save a model, such as `isolated`.

## Capabilities

### New Capabilities

- `model-export`: what a training run writes so that its model can be rebuilt and used
  outside the federation.
- `scenario-prediction`: the `gridfm predict` command, which turns a run's exported
  model and the federation's client data into per-bus predictions.
- `scenario-visualization`: the notebook that plots one scenario's network with input,
  truth, prediction and error.

### Modified Capabilities

None. The project has no specs yet.

## Impact

- `flower_app/experiments/fedavg/server.py`: `save_outputs` also writes
  `graphkit_config.json`. Runs made before this change cannot be predicted and must be
  run again.
- `gridfm_cli/`: a new `predict` command and the modules behind it. They import
  gridfm-graphkit but still never import `flower_app`.
- `notebooks/`: a new top-level folder for the notebook.
- `pyproject.toml`: `torch-scatter` as a dependency with uv's build settings for it,
  `plotly` and `networkx` as direct dependencies, and `marimo` in the `dev` group.
  `uv sync` now compiles `torch-scatter`, which needs a C++ compiler on the host.
- `.gitignore`: ignores `/predictions/`.
- Documentation: `AGENTS.md`, `README.md`, `docs/architecture.md` and
  `docs/development.md`.
- Architectural decision records: `docs/adr/` has no records yet, so the change relies
  on none. It adds records for running inference on the host, for runs exporting a
  self-describing model and for keeping host-made results out of `outputs/` (see
  `design.md`).
