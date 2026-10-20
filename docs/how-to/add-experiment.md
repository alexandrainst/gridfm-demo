# How to Add an Experiment

This guide shows you how to add an experiment, a training procedure that `gridfm run`
can train on any federation.

Prerequisites:

- The project dependencies, installed with `uv sync`
- A running federation to test on, started with `uv run gridfm up <federation>`

## Steps

1. Choose a name `<name>` for the experiment. It becomes the package name and the name
   passed to `gridfm run`, so use a valid Python identifier, such as `fedprox`.

2. Create the package `flower_app/experiments/<name>/` and define `EXPERIMENT` in its
   `__init__.py`, an `Experiment` from `flower_app/interface.py` with three entry
   points:
   - `server_main(grid, context, paths)` runs once per run on the server. Read your
     settings from `context.run_config` under the keys `<name>.<key>`, send messages to
     the clients through `grid`, for example with a Flower strategy, and write your
     results to `paths.output_dir`. That is `outputs/<federation>/<name>/<timestamp>/`
     on the host. If the experiment trains one shared model, save it as `final_model.pt`
     together with `graphkit_config.json`, the gridfm-graphkit configuration the model
     was built from, so that `gridfm predict` can rebuild it.
   - `client_train(msg, context, dataset, paths)` runs on a client for each train
     message and returns the reply. `dataset` holds the client's ID, its data directory,
     its networks and the maximum number of scenarios per network. Write training logs
     to `paths.log_dir`. Take the client's settings from `msg`, not from the run config.
   - `client_evaluate(msg, context, dataset, paths)` does the same for evaluate
     messages.

   Import nothing from `flower_app/` except `interface.py`, and keep the experiment's
   configuration as Python code. Refer to `flower_app/experiments/fedavg/` for a
   complete example.

3. Seed the random number generators from a `seed` run config key: on the server before
   building the initial model, and on each client from the seed, the round and the
   client ID that the server sends with each training message. This keeps runs with the
   same seed repeatable.

4. Register the experiment in `EXPERIMENTS` of `flower_app/experiments/__init__.py`
   under `<name>`.

5. Declare the experiment's run config keys with defaults in
   `[tool.flwr.app.config.<name>]` of `pyproject.toml`. `flwr run` rejects keys that are
   not declared there.

6. If the experiment needs a library that `build/client/pyproject.toml` or
   `build/server/pyproject.toml` does not list, add it there and rebuild the images:

   ```bash
   uv run gridfm build <federation>
   ```

7. Describe the experiment under `### Experiments` in `README.md`: what it trains, how,
   and its run config defaults.

## Confirm the Experiment Works

Run the experiment on the running federation:

```bash
uv run gridfm run <name>
```

You should see the run's logs stream until it ends, and its results appear in
`outputs/<federation>/<name>/<timestamp>/`.

To change a run config value for a single run, call `flwr run` directly:

```bash
uv run flwr run . local-deployment \
  --run-config "experiment='<name>' <name>.<key>=<value>" --stream
```
