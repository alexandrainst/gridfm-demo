"""The ServerApp: server side of the experiment named in the run config."""

from flwr.app import Context
from flwr.serverapp import Grid, ServerApp

from .experiments import get_experiment
from .interface import ServerPaths
from .paths import server_output_dir

app = ServerApp()


@app.main()
def main(grid: Grid, context: Context) -> None:
    """Run the experiment's server side.

    Args:
        grid:
          Grid connecting the ServerApp to the SuperNodes.
        context:
          Context of the ServerApp. Its run config holds `"experiment"`.
    """
    experiment = get_experiment(name=str(context.run_config["experiment"]))
    paths = ServerPaths(output_dir=server_output_dir(context=context))
    experiment.server_main(grid=grid, context=context, paths=paths)
