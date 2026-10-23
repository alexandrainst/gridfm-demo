"""Notebook that compares the large models on the unseen `case300_ieee` grid."""

import marimo

__generated_with = "0.25.1"
app = marimo.App(app_title="case300 Comparison")

with app.setup(hide_code=True):
    import json

    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go
    import torch
    from plotly.subplots import make_subplots

    from gridfm_cli.clients import read_clients
    from gridfm_cli.predict import FEATURES, predict_client
    from gridfm_cli.runs import GRAPHKIT_CONFIG_FILE, MODEL_FILE, list_runs

    TRAINING_FEDERATION = "case500_2clients"
    TEST_FEDERATION = "case300_1client"
    CLIENT_MODEL_FILES: tuple[str, ...] = (
        "final_model_client_0.pt",
        "final_model_client_1.pt",
    )
    UNITS: dict[str, str] = {"Vm": "p.u.", "Va": "deg", "Pg": "MW", "Qg": "MVAr"}


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # case300 Comparison

    This notebook tests three models trained on `case500_2clients` on a grid none of
    them has seen, the 300-bus `case300_ieee` of the federation `case300_1client`:

    | Model | Trained by |
    | --- | --- |
    | FedAvg | `fedavg_large`, on the data of both clients |
    | Isolated client 0 | `isolated_large`, on client 0's `case500_goc` only |
    | Isolated client 1 | `isolated_large`, on client 1's `case588_sdet` only |

    ## Before You Start

    The notebook reads the case300 data and the models of two runs. Three commands
    write them, run from the repository root:

    1. `uv run gridfm data case300_1client` generates the case300 scenarios.
    2. `uv run gridfm run fedavg_large` on `case500_2clients` trains the FedAvg model.
    3. `uv run gridfm run isolated_large` on `case500_2clients` trains the two
       isolated models.

    The run dropdowns list the runs that saved their models. Predicting all scenarios
    with three models takes a while on the CPU.

    ## What Is Shown

    Each model predicts every case300 scenario. The table and the chart give the mean
    squared error of each model for Vm, Va, Pg and Qg, over the values the model had
    to predict. Values the model was given as input are left out. Lower is better.
    """)
    return


@app.cell(hide_code=True)
def _():
    test_client = read_clients(federation=TEST_FEDERATION)[0]
    _bus_data = (
        test_client.data_dir / test_client.networks[0] / "raw" / "bus_data.parquet"
    )
    mo.stop(
        not _bus_data.exists(),
        mo.md(
            "The case300 data is missing. Make it with "
            f"`uv run gridfm data {TEST_FEDERATION}`."
        ),
    )
    return (test_client,)


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
def _(fedavg_picker, isolated_picker, test_client):
    _model_files = {
        "FedAvg": fedavg_picker.value / MODEL_FILE,
        "Isolated client 0": isolated_picker.value / CLIENT_MODEL_FILES[0],
        "Isolated client 1": isolated_picker.value / CLIENT_MODEL_FILES[1],
    }
    with mo.status.spinner(title="Predicting the case300 scenarios"):
        predictions = {
            name: predict_client(
                graphkit_config=json.loads(
                    (path.parent / GRAPHKIT_CONFIG_FILE).read_text()
                ),
                state_dict=torch.load(path, weights_only=True),
                client=test_client,
            )
            for name, path in _model_files.items()
        }
    return (predictions,)


@app.cell(hide_code=True)
def _(predictions):
    errors = mse_table(predictions=predictions)
    mo.ui.table(
        errors.rename(columns={f: f"{f} ({UNITS[f]}²)" for f in FEATURES}),
        selection=None,
    )
    return (errors,)


@app.cell(hide_code=True)
def _(errors):
    error_figure = mse_figure(errors=errors)
    error_figure
    return


@app.function(hide_code=True)
def mse_table(predictions: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return the mean squared error of each model and feature.

    Args:
        predictions:
          Predictions per model name, as returned by `predict_client`.

    Returns:
        One row per model, indexed by its name, and one column per feature of
        `FEATURES`. Each value is the mean of `(pred - target) ** 2` over the rows
        where `<feature>_given` is `False`.
    """
    return pd.DataFrame(
        {
            feature: {
                name: float(
                    (
                        (frame[f"{feature}_pred"] - frame[f"{feature}_target"])[
                            ~frame[f"{feature}_given"]
                        ]
                        ** 2
                    ).mean()
                )
                for name, frame in predictions.items()
            }
            for feature in FEATURES
        }
    )


@app.function(hide_code=True)
def mse_figure(errors: pd.DataFrame) -> go.Figure:
    """Draw one bar chart of the mean squared errors per feature.

    Args:
        errors:
          Mean squared errors, as returned by `mse_table`.

    Returns:
        A figure with one panel per column of `errors`, each with its own y axis and
        one bar per model.
    """
    figure = make_subplots(
        rows=1, cols=len(errors.columns), subplot_titles=list(errors)
    )
    for index, feature in enumerate(errors.columns):
        figure.add_trace(
            go.Bar(
                x=errors.index,
                y=errors[feature],
                marker_color=["#4c78a8", "#f58518", "#54a24b"][: len(errors)],
                hovertemplate=f"%{{x}}<br>%{{y:.4g}} {UNITS[feature]}²<extra></extra>",
            ),
            row=1,
            col=index + 1,
        )
        figure.update_yaxes(title_text=f"MSE ({UNITS[feature]}²)", row=1, col=index + 1)
    figure.update_layout(height=450, showlegend=False)
    return figure


if __name__ == "__main__":
    app.run()
