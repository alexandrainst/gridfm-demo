# Tasks

## 1. Host dependencies

- [x] 1.1 Add `torch-scatter` to `pyproject.toml` with `uv add`, and configure
      `[tool.uv]` with `no-build-isolation-package` and `extra-build-dependencies`
      (`match-runtime = true`) and a CPU-only build (D1). Verify with `uv sync` followed
      by `uv run python -c "import torch_scatter; import gridfm_graphkit.tasks.pf_task"`
- [x] 1.2 Add `plotly` and `networkx` with `uv add`, and `marimo` with
      `uv add --group=dev`. Verify that
      `uv run python -c "import plotly, networkx, marimo"` succeeds
- [x] 1.3 Update the rule about `torch_scatter` in `AGENTS.md` and the comment on
      `testpaths` in `pyproject.toml`. Decide whether `flower_app` can now join
      `testpaths` for its doctests, and verify with `uv run pytest`
- [x] 1.4 Write `docs/adr/0001-run-inference-on-the-host.md` from `docs/adr/template.md`
      for D1, and verify it names the rejected container and graphkit-patch options

## 2. Model export

- [x] 2.1 Make `save_outputs` in `flower_app/experiments/fedavg/server.py` write
      `graphkit_config.json` from `GRAPHKIT_CONFIG` and update its docstring (D2).
      Verify with a one-off call of `save_outputs` on a temporary folder that the file
      loads with `json.load` and equals `GRAPHKIT_CONFIG`
- [x] 2.2 Update the outputs listed in `docs/development.md` and the Outputs and Logging
      section of `docs/architecture.md`, and verify that both name
      `graphkit_config.json`
- [x] 2.3 Write `docs/adr/0002-runs-export-a-self-describing-model.md` for D2, and
      verify it states the rule for future experiments that save a model
- [x] 2.4 Ask the user to run `gridfm run fedavg` on `case14_2clients`, and verify that
      the new run folder holds `graphkit_config.json`

## 3. Prediction command

- [x] 3.1 Add `PREDICTIONS_DIR` to `gridfm_cli/paths.py` and `/predictions/` to
      `.gitignore`. Verify with `git check-ignore predictions/x`
- [x] 3.2 Write `gridfm_cli/runs.py` to list a federation's run folders and report a
      missing `final_model.pt` or `graphkit_config.json`. Verify with a one-off call
      against `outputs/case14_2clients` that isolated runs and the pre-change FedAvg
      runs are reported as unusable
- [x] 3.3 Write the node config reader in `gridfm_cli/clients.py`, using
      `flwr.common.config.parse_config_args` on the SuperNode commands of `compose.yml`
      (D3). Verify that it returns client IDs 0 and 1, network `case14_ieee` and 40
      scenarios for `case14_2clients`
- [x] 3.4 Write the prediction of one client in `gridfm_cli/predict.py`: data module,
      normalizer, task, weights, `predict_step` over all splits, `<feature>_given` flags
      from the masks and the `split` column (D3, D4). Verify on the run from 2.4 that
      client 0 gives 40 x 14 rows and that `Vm_target` equals `Vm` in its
      `bus_data.parquet`
- [x] 3.5 Write the Parquet output to `predictions/<federation>/<experiment>/<run>/`,
      replacing existing files (D5). Verify that nothing under `outputs/` changes, using
      `find outputs -newer` before and after
- [x] 3.6 Add the `predict` command to `gridfm_cli/main.py`, prompting for the
      federation and run through `gridfm_cli/choices.py` and offering only usable runs.
      Report a root-owned `processed/` folder with a clear message. Verify by running
      `uv run gridfm predict` with no arguments, with an isolated run and with the run
      from 2.4
- [x] 3.7 Document `gridfm predict` in `README.md` (usage, plus a C++ compiler as a
      prerequisite) and in the `gridfm_cli/` section of `docs/architecture.md`. Verify
      that the documented command runs as written
- [x] 3.8 Write `docs/adr/0003-host-results-live-outside-outputs.md` for D5, and verify
      it states that only the federation writes `outputs/`

## 4. Notebook

- [x] 4.1 Create `notebooks/scenarios.py` with the run, client, scenario and feature
      controls. List only runs with predictions, and limit the scenario input to the
      client's scenarios. Verify with `uv run marimo check notebooks/scenarios.py` and
      by opening it with `uv run marimo edit`
- [x] 4.2 Add the NetworkX layout from the union of all branches of the client's network
      (D7). Verify that the positions stay the same when switching scenarios
- [x] 4.3 Add the four Plotly network panels: input with hidden buses in grey, truth and
      prediction on one color scale, and absolute error. Mark bus type by symbol and
      draw out-of-service branches dashed. Verify for Vm that PQ bus 13 is grey in the
      input panel and PV bus 1 is colored
- [x] 4.4 Add the per-bus table below the panels, and verify that it has 14 rows for
      `case14_ieee`
- [x] 4.5 Show a message when no run has predictions, and verify by temporarily renaming
      `predictions/`
- [x] 4.6 Add `notebooks/` to the layout in `AGENTS.md`, the Code Map in
      `docs/architecture.md` and the usage in `README.md`. Verify that the documented
      command opens the notebook
- [x] 4.7 Show the chosen scenario's split next to the scenario input, and list the
      scenarios of each split for the chosen client. Verify in the running notebook with
      marimo-pair: client 0 lists 24, 25, 30 and 31 as test, and setting the scenario to
      24 and then 2 changes the label from test to train
- [x] 4.8 Replace the notebook's opening text with the prerequisites, what is shown, the
      bus symbols and the four plots. Verify in the running notebook that it renders and
      names the four `gridfm` commands in order

## 5. Integration

- [x] 5.1 Run `ruff`, `ty` and `prettier --print-width=88` on the changed files and
      `uv run pytest`, and verify that all pass
- [x] 5.2 Walk through the flow in `README.md` from `gridfm run fedavg` (run by the
      user) to the notebook, and verify that the notebook shows a scenario of each
      client

## Workflow follow-up

- Recommit the branch into atomic commits before handing it over.
- Archive the change after review.
