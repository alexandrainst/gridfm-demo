"""Notebook that scores the large models on the test data of three grids."""

import marimo

__generated_with = "0.25.1"
app = marimo.App(app_title="Model Evaluation")

with app.setup(hide_code=True):
    import json
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go
    import torch
    from plotly.subplots import make_subplots

    from gridfm_cli.clients import read_clients
    from gridfm_cli.predict import FEATURES, predict_client
    from gridfm_cli.runs import GRAPHKIT_CONFIG_FILE, MODEL_FILE, list_runs

    TRAINING_FEDERATION = "case500_2clients"
    UNSEEN_FEDERATION = "case300_1client"
    CLIENT_MODEL_FILES: tuple[str, ...] = (
        "final_model_client_0.pt",
        "final_model_client_1.pt",
    )
    UNITS: dict[str, str] = {"Vm": "p.u.", "Va": "deg", "Pg": "MW", "Qg": "MVAr"}
    # Where the notebook writes the errors that the slides read.
    ERRORS_FILE = Path("docs/presentations/2026-11-19/public/model_errors.csv")


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Model Evaluation

    This notebook scores three models trained on `case500_2clients` on the test data of
    three grids:

    | Model | Trained by |
    | --- | --- |
    | FedAvg | `fedavg_large`, on the data of both clients |
    | Isolated client 0 | `isolated_large`, on `case500_goc` data of client 0 only |
    | Isolated client 1 | `isolated_large`, on `case588_sdet` data of client 1 only |

    | Test data | Source |
    | --- | --- |
    | `case500_goc` | The test split of client 0 |
    | `case588_sdet` | The test split of client 1 |
    | `case300_ieee` | Every scenario of `case300_1client`, a grid no model has seen |

    ## Before You Start

    The notebook reads the models of two runs and the data of both federations. Run
    from the repository root:

    1. `uv run gridfm data case500_2clients` and
       `uv run gridfm data case300_1client` generate the scenarios.
    2. `uv run gridfm run fedavg_large` and `uv run gridfm run isolated_large` on
       `case500_2clients` train the models.

    The run dropdowns list the runs that saved their models.

    ## What Is Shown

    The table and the charts give the mean squared error of each model for Vm, Va, Pg
    and Qg, over the values the model had to predict. Values the model was given as
    input are left out. Lower is better.
    """)
    return


@app.cell(hide_code=True)
def _():
    training_clients = read_clients(federation=TRAINING_FEDERATION)
    unseen_client = read_clients(federation=UNSEEN_FEDERATION)[0]
    _missing = [
        client.data_dir
        for client in (*training_clients, unseen_client)
        if not (
            client.data_dir / client.networks[0] / "raw" / "bus_data.parquet"
        ).exists()
    ]
    mo.stop(
        bool(_missing),
        mo.md(
            "The data of these clients is missing. Make it with `uv run gridfm data "
            f"<federation>`: {', '.join(f'`{path}`' for path in _missing)}"
        ),
    )
    return training_clients, unseen_client


@app.cell(hide_code=True)
def _():
    _runs = list_runs(federation=TRAINING_FEDERATION)
    fedavg_runs = {
        run.timestamp: run.output_dir
        for run in _runs
        if run.experiment == "fedavg_large" and (run.output_dir / MODEL_FILE).is_file()
    }
    isolated_runs = {
        run.timestamp: run.output_dir
        for run in _runs
        if run.experiment == "isolated_large"
        and all((run.output_dir / name).is_file() for name in CLIENT_MODEL_FILES)
    }
    mo.stop(
        not fedavg_runs or not isolated_runs,
        mo.md(
            "A `fedavg_large` run and an `isolated_large` run on "
            f"`{TRAINING_FEDERATION}` that saved their models are needed."
        ),
    )
    fedavg_picker = mo.ui.dropdown(
        options=fedavg_runs, value=next(reversed(fedavg_runs)), label="fedavg_large run"
    )
    isolated_picker = mo.ui.dropdown(
        options=isolated_runs,
        value=next(reversed(isolated_runs)),
        label="isolated_large run",
    )
    mo.hstack([fedavg_picker, isolated_picker], justify="start", gap=2)
    return fedavg_picker, isolated_picker


@app.cell(hide_code=True)
def _(fedavg_picker, isolated_picker, training_clients, unseen_client):
    _model_files = {
        "FedAvg": fedavg_picker.value / MODEL_FILE,
        "Isolated client 0": isolated_picker.value / CLIENT_MODEL_FILES[0],
        "Isolated client 1": isolated_picker.value / CLIENT_MODEL_FILES[1],
    }
    _clients = {
        "case500_goc": training_clients[0],
        "case588_sdet": training_clients[1],
        "case300_ieee": unseen_client,
    }
    with mo.status.spinner(title="Predicting the scenarios of three grids"):
        predictions = {
            (model, grid): predict_client(
                graphkit_config=json.loads(
                    (path.parent / GRAPHKIT_CONFIG_FILE).read_text()
                ),
                state_dict=torch.load(path, weights_only=True),
                client=client,
            )
            for model, path in _model_files.items()
            for grid, client in _clients.items()
        }
    return (predictions,)


@app.cell(hide_code=True)
def _(predictions):
    errors = mse_table(predictions=predictions)
    mo.ui.table(errors.round(6), selection=None)
    return (errors,)


@app.cell(hide_code=True)
def _(errors):
    error_figure = mse_figure(errors=errors)
    error_figure
    return


@app.cell(hide_code=True)
def _(errors):
    ERRORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    errors.to_csv(ERRORS_FILE)
    mo.md(f"The errors are saved to `{ERRORS_FILE}` for the slides.")
    return


@app.function(hide_code=True)
def mse_table(predictions: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    """Return the mean squared error of each model, grid and feature.

    Args:
        predictions:
          Predictions per model name and grid name, as returned by `predict_client`.

    Returns:
        One row per model, indexed by its name, and one column per grid and feature,
        indexed by `(grid, feature)`. Each value is the mean of
        `(pred - target) ** 2` over the rows where `<feature>_given` is `False`. The
        grids `case500_goc` and `case588_sdet` use only the rows of the test split,
        and any other grid uses every row.
    """
    columns: dict[tuple[str, str], dict[str, float]] = {}
    for (model, grid), frame in predictions.items():
        if grid in ("case500_goc", "case588_sdet"):
            frame = frame[frame["split"] == "test"]
        for feature in FEATURES:
            hidden = frame[~frame[f"{feature}_given"]]
            error = (hidden[f"{feature}_pred"] - hidden[f"{feature}_target"]) ** 2
            columns.setdefault((grid, feature), {})[model] = float(error.mean())
    return pd.DataFrame(columns)


@app.function(hide_code=True)
def mse_figure(errors: pd.DataFrame) -> go.Figure:
    """Draw one bar chart per feature, with the grids on the x axis.

    Args:
        errors:
          Mean squared errors, as returned by `mse_table`.

    Returns:
        A figure with one panel per feature, each with its own y axis, one group of
        bars per grid and one bar per model.
    """
    colors = ["#4c78a8", "#f58518", "#54a24b"]
    grids = list(dict.fromkeys(grid for grid, _ in errors.columns))
    figure = make_subplots(rows=1, cols=len(FEATURES), subplot_titles=list(FEATURES))
    for column, feature in enumerate(FEATURES, start=1):
        for model, color in zip(errors.index, colors, strict=False):
            figure.add_trace(
                go.Bar(
                    name=model,
                    x=grids,
                    y=[errors.loc[model, (grid, feature)] for grid in grids],
                    marker_color=color,
                    showlegend=column == 1,
                    legendgroup=model,
                    hovertemplate=(
                        f"{model}<br>%{{x}}<br>%{{y:.4g}} {UNITS[feature]}²"
                        "<extra></extra>"
                    ),
                ),
                row=1,
                col=column,
            )
        figure.update_yaxes(
            title_text=f"MSE ({UNITS[feature]}²)", type="log", row=1, col=column
        )
    figure.update_layout(height=450, barmode="group")
    return figure


if __name__ == "__main__":
    app.run()
