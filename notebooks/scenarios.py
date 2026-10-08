"""Notebook that plots the predictions of a run on the network of one scenario."""

import marimo

__generated_with = "0.25.1"
app = marimo.App(app_title="Scenarios")

with app.setup(hide_code=True):
    import typing as t
    from pathlib import Path

    import marimo as mo
    import networkx as nx
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    from gridfm_cli.clients import read_clients
    from gridfm_cli.paths import PREDICTIONS_DIR

    UNITS: dict[str, str] = {"Vm": "p.u.", "Va": "deg", "Pg": "MW", "Qg": "MVAr"}
    SYMBOLS: dict[str, str] = {"PQ": "circle", "PV": "square", "REF": "diamond"}
    SPLITS: dict[str, str] = {"train": "train", "val": "validation", "test": "test"}
    # Panel title -> column of `bus_table`, filled row by row in a 2 x 2 grid, so that
    # truth and prediction sit side by side.
    PANELS: dict[str, str] = {
        "Truth": "truth",
        "Prediction": "prediction",
        "Input": "input",
        "Absolute error": "error",
    }


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Scenarios

    This notebook plots a trained model's power flow predictions on the grid of one
    client, one scenario at a time.

    ## Before You Start

    The notebook only reads files. Four commands write them, run from the repository
    root in this order:

    1. `uv run gridfm data <federation>` generates the scenarios of each client.
    2. `uv run gridfm up <federation>` starts the federation.
    3. `uv run gridfm run fedavg` trains a model. Only experiments that save a model,
       such as `fedavg`, can be shown.
    4. `uv run gridfm predict <federation> <run>` predicts every scenario of every
       client with the model of that run.

    The run dropdown lists the runs that have predictions.

    ## What Is Shown

    The notebook shows every scenario of the chosen client: those the model trained
    on, and the validation and test scenarios it never trained on. The label next to
    the scenario number gives its split, and the line below the controls lists the
    scenarios of each split. Judge the model on validation and test scenarios.

    Each point is a bus and each line a branch. The shape of a point gives the bus
    type, and dashed lines are branches out of service in the scenario.

    | Shape | Bus type | Role in the power flow |
    | --- | --- | --- |
    | Circle | PQ | Load bus with fixed active and reactive power |
    | Square | PV | Generator bus with fixed active power and voltage |
    | Diamond | REF | Reference bus that sets the voltage angle |

    The grid is drawn four times for the chosen feature (Vm, Va, Pg or Qg).

    | Plot | What the colors show |
    | --- | --- |
    | Truth | The power flow solution computed by gridfm-datakit |
    | Prediction | The model's prediction |
    | Input | The values the model receives. Grey buses are values it must predict |
    | Absolute error | The difference between prediction and truth, ignoring sign |

    Truth, prediction and input share one color scale. The error has its own. The
    table below the plots lists the exact values of every bus.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## The Four Features

    A power flow solution describes each bus with four values. Vm and Va describe the
    voltage at the bus. Pg and Qg describe the power the generators at the bus inject.

    | Feature | Quantity | Unit |
    | --- | --- | --- |
    | Vm | Voltage magnitude | per unit (p.u.) |
    | Va | Voltage angle | degrees |
    | Pg | Active power generation | MW |
    | Qg | Reactive power generation | MVAr |

    Vm is the size of the voltage relative to the bus's nominal voltage, so 1.0 p.u.
    is exactly the nominal voltage. Grids are kept close to it, typically between
    0.94 and 1.06 p.u., because equipment is built for its rated voltage.

    Va is how far the bus's AC voltage wave is shifted relative to the reference bus,
    whose angle is 0 by definition. Active power flows from buses with larger angles to
    buses with smaller ones, so angles drop with distance from the generators.

    Pg is the real power the generators produce, the power that does work. It is 0 at
    buses without a generator. At the reference bus it covers whatever the other
    generators leave of the load and the line losses.

    Qg is reactive power: power that oscillates between generators and the grid and
    sustains the electric and magnetic fields in lines, transformers and machines.
    Generators raise or lower it to hold their bus voltage, and it can be negative.

    The model predicts Vm and Va where they are hidden. Pg and Qg follow from the
    predicted voltages through the power balance at each bus, so an error in Pg or Qg
    comes from an error in the voltages. The loads Pd and Qd are always given to the
    model and are not plotted.
    """)
    return


@app.cell(hide_code=True)
def _():
    run_dirs = {
        str(path.relative_to(PREDICTIONS_DIR)): path
        for path in sorted(PREDICTIONS_DIR.glob("*/*/*/"))
        if any(path.glob("client_*.parquet"))
    }
    mo.stop(
        not run_dirs,
        mo.md(
            "No run has predictions. Make them with "
            "`uv run gridfm predict <federation> <run>`."
        ),
    )
    run_picker = mo.ui.dropdown(
        options=run_dirs, value=next(reversed(run_dirs)), label="Run"
    )
    run_picker
    return (run_picker,)


@app.cell(hide_code=True)
def _(run_picker):
    run_dir: Path = run_picker.value
    clients = {
        client.client_id: client
        for client in read_clients(
            federation=run_dir.relative_to(PREDICTIONS_DIR).parts[0]
        )
    }
    predictions = {
        int(path.stem.removeprefix("client_")): pd.read_parquet(path)
        for path in sorted(run_dir.glob("client_*.parquet"))
    }
    return clients, predictions


@app.cell(hide_code=True)
def _(predictions):
    # One option per client and network, since scenario numbers restart per network.
    datasets = {
        f"client {client_id} / {network}": (client_id, network)
        for client_id, frame in predictions.items()
        for network in frame["network"].unique()
    }
    dataset_picker = mo.ui.dropdown(
        options=datasets, value=next(iter(datasets)), label="Client"
    )
    feature_picker = mo.ui.radio(
        options=list(UNITS), value="Vm", label="Feature", inline=True
    )
    return dataset_picker, feature_picker


@app.cell(hide_code=True)
def _(dataset_picker, predictions):
    client_id, network = dataset_picker.value
    client_predictions = predictions[client_id].query("network == @network")
    scenario_picker = mo.ui.number(
        start=int(client_predictions["scenario"].min()),
        stop=int(client_predictions["scenario"].max()),
        value=int(client_predictions["scenario"].min()),
        label="Scenario",
    )
    return client_id, client_predictions, network, scenario_picker


@app.cell
def _(client_predictions, dataset_picker, feature_picker, scenario_picker):
    _scenario_splits = client_predictions.groupby("split")["scenario"].unique()
    _split = client_predictions.loc[
        client_predictions["scenario"] == scenario_picker.value, "split"
    ].iloc[0]
    _numbers = {
        name: ", ".join(str(number) for number in sorted(scenarios))
        for name, scenarios in _scenario_splits.items()
    }
    _overview = " | ".join(
        f"{label}: {_numbers[name]}"
        for name, label in SPLITS.items()
        if name in _numbers
    )
    _split_label = mo.md(f"**{SPLITS[_split]}**")
    mo.vstack(
        [
            mo.hstack(
                [dataset_picker, scenario_picker, _split_label, feature_picker],
                justify="start",
                align="center",
                gap=2,
            ),
            mo.md(f"Scenarios per split: {_overview}"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(client_id, clients, network):
    branches = pd.read_parquet(
        clients[client_id].data_dir / network / "raw" / "branch_data.parquet",
        columns=["scenario", "from_bus", "to_bus", "br_status"],
    )
    positions = layout(branches=branches)
    return branches, positions


@app.cell(hide_code=True)
def _(branches, client_predictions, feature_picker, positions, scenario_picker):
    # Filter in Python, not in a `query` string: marimo only sees references in code, so
    # a string mention of `scenario_picker` would not rerun this cell.
    _scenario = scenario_picker.value
    buses = bus_table(
        predictions=client_predictions[client_predictions["scenario"] == _scenario],
        feature=feature_picker.value,
    )
    network_figure = scenario_figure(
        buses=buses,
        branches=branches[branches["scenario"] == _scenario],
        positions=positions,
        feature=feature_picker.value,
    )
    network_figure
    return (buses,)


@app.cell(hide_code=True)
def _(buses):
    bus_view = mo.ui.table(buses, selection=None, pagination=False)
    bus_view
    return


@app.function(hide_code=True)
def layout(branches: pd.DataFrame) -> dict[int, tuple[float, float]]:
    """Return the 2D position of every bus of a network.

    Args:
        branches:
          Branches of all scenarios of the network, with `from_bus` and `to_bus`.

    Returns:
        Position per bus. The same branches give the same positions.
    """
    # The union of all scenarios' branches keeps the positions fixed when a branch is
    # out of service in some scenarios.
    graph = nx.Graph()
    graph.add_edges_from(
        branches[["from_bus", "to_bus"]].drop_duplicates().itertuples(index=False)
    )
    positions = nx.kamada_kawai_layout(graph)
    return {int(bus): (float(x), float(y)) for bus, (x, y) in positions.items()}


@app.function(hide_code=True)
def bus_table(predictions: pd.DataFrame, feature: str) -> pd.DataFrame:
    """Return one row per bus with the input, truth, prediction and error of a feature.

    Args:
        predictions:
          Predictions of one scenario, as written by `gridfm predict`.
        feature:
          One of `UNITS`.

    Returns:
        The columns `bus`, `type`, `input` (missing where the model is not given the
        feature), `truth`, `prediction` and `error` (absolute), sorted by bus.
    """
    truth = predictions[f"{feature}_target"]
    prediction = predictions[f"{feature}_pred"]
    bus_type = predictions[list(SYMBOLS)].idxmax(axis="columns")
    return pd.DataFrame(
        {
            "bus": predictions["bus"],
            "type": bus_type,
            "input": truth.where(predictions[f"{feature}_given"]),
            "truth": truth,
            "prediction": prediction,
            "error": (prediction - truth).abs(),
        }
    ).sort_values("bus", ignore_index=True)


@app.function(hide_code=True)
def scenario_figure(
    buses: pd.DataFrame,
    branches: pd.DataFrame,
    positions: dict[int, tuple[float, float]],
    feature: str,
) -> go.Figure:
    """Draw the input, truth, prediction and error of a scenario on its network.

    Args:
        buses:
          Rows of `bus_table` for the scenario.
        branches:
          Branches of the scenario, with `from_bus`, `to_bus` and `br_status`.
        positions:
          Position per bus, from `layout`.
        feature:
          One of `UNITS`.

    Returns:
        A figure with one panel per entry of `PANELS`. Input, truth and prediction
        share one color scale, and the error has its own.
    """
    unit = UNITS[feature]
    figure = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=list(PANELS),
        horizontal_spacing=0.02,
        vertical_spacing=0.08,
    )
    for index, column in enumerate(PANELS.values()):
        row, col = divmod(index, 2)
        for trace in branch_traces(branches=branches, positions=positions):
            figure.add_trace(trace, row=row + 1, col=col + 1)
        for trace in bus_traces(
            buses=buses,
            values=buses[column],
            positions=positions,
            coloraxis="coloraxis2" if column == "error" else "coloraxis",
            unit=unit,
        ):
            figure.add_trace(trace, row=row + 1, col=col + 1)
    values = pd.concat([buses["truth"], buses["prediction"]])
    figure.update_layout(
        height=800,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis={
            "colorscale": "Viridis",
            "cmin": float(values.min()),
            "cmax": float(values.max()),
            "colorbar": {
                "title": f"{feature} ({unit})",
                "x": 1.0,
                "len": 0.45,
                "y": 0.78,
            },
        },
        coloraxis2={
            "colorscale": "Reds",
            "cmin": 0.0,
            "colorbar": {
                "title": f"|error| ({unit})",
                "x": 1.0,
                "len": 0.45,
                "y": 0.22,
            },
        },
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    # Each panel's y-axis must be anchored to its own x-axis (`x`, `x2`, ...) to keep
    # the network's aspect ratio in every panel.
    for index in range(len(PANELS)):
        row, col = divmod(index, 2)
        figure.update_yaxes(
            scaleanchor=f"x{index + 1}" if index else "x",
            scaleratio=1,
            row=row + 1,
            col=col + 1,
        )
    return figure


@app.function(hide_code=True)
def branch_traces(
    branches: pd.DataFrame, positions: dict[int, tuple[float, float]]
) -> list[go.Scatter]:
    """Return line traces for the branches in and out of service.

    Args:
        branches:
          Branches of one scenario, with `from_bus`, `to_bus` and `br_status`.
        positions:
          Position per bus.

    Returns:
        A solid trace for branches in service and a dashed one for the others.
    """
    traces = []
    for in_service, dash in ((True, "solid"), (False, "dash")):
        selected = branches[(branches["br_status"] > 0) == in_service]
        xs: list[float | None] = []
        ys: list[float | None] = []
        for from_bus, to_bus in selected[["from_bus", "to_bus"]].itertuples(
            index=False
        ):
            (x0, y0), (x1, y1) = positions[from_bus], positions[to_bus]
            xs += [x0, x1, None]
            ys += [y0, y1, None]
        traces.append(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                line={"color": "grey", "width": 1.5, "dash": dash},
                hoverinfo="skip",
            )
        )
    return traces


@app.function(hide_code=True)
def bus_traces(
    buses: pd.DataFrame,
    values: pd.Series,
    positions: dict[int, tuple[float, float]],
    coloraxis: str,
    unit: str,
) -> list[go.Scatter]:
    """Return marker traces for the buses, colored by value.

    Args:
        buses:
          Rows of `bus_table`, with `bus` and `type`.
        values:
          Value per row of `buses`. Missing values are drawn grey.
        positions:
          Position per bus.
        coloraxis:
          Name of the layout color axis that maps the values to colors.
        unit:
          Unit of the values, shown on hover.

    Returns:
        One trace for the buses with a value and one for those without.
    """
    has_value = values.notna()
    traces = []
    for selected, marker_color in ((has_value, None), (~has_value, "lightgrey")):
        rows = buses[selected]
        marker: dict[str, t.Any] = {
            "size": 16,
            "symbol": [SYMBOLS[bus_type] for bus_type in rows["type"]],
            "line": {"color": "black", "width": 1},
        }
        if marker_color is None:
            marker |= {"color": values[selected], "coloraxis": coloraxis}
        else:
            marker |= {"color": marker_color}
        traces.append(
            go.Scatter(
                x=[positions[bus][0] for bus in rows["bus"]],
                y=[positions[bus][1] for bus in rows["bus"]],
                mode="markers+text",
                marker=marker,
                text=[str(bus) for bus in rows["bus"]],
                textposition="top center",
                customdata=list(zip(rows["type"], values[selected], strict=True)),
                hovertemplate=(
                    "bus %{text} (%{customdata[0]})<br>"
                    f"%{{customdata[1]:.4g}} {unit}<extra></extra>"
                ),
            )
        )
    return traces


if __name__ == "__main__":
    app.run()
