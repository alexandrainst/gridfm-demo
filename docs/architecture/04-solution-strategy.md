# 4. Solution Strategy

The demo wraps two libraries from the GridFM project, gridfm-datakit for data and
gridfm-graphkit for the model, in Flower's federated learning loop, and runs the
federation as Docker containers on one machine. The fundamental decisions are:

- Technology: [Flower](https://flower.ai/) 1.23 for federated learning, because it ships
  the project's code to the server and the clients with each run, so the containers hold
  only dependencies.
- Technology: [gridfm-graphkit](https://github.com/gridfm/gridfm-graphkit) for the power
  flow model and [gridfm-datakit](https://github.com/gridfm/gridfm-datakit) for the
  synthetic data, because they are the GridFM project's own libraries and the data
  generator writes the format the model library reads. Each client trains with a
  [Lightning](https://lightning.ai/docs/pytorch/stable/) trainer, because
  gridfm-graphkit's tasks are Lightning modules.
- Technology: [Docker Compose](https://docs.docker.com/compose/) as the federation
  runtime, because it is Flower's documented deployment and one Compose file per
  federation defines its containers and data mounts.
- Technology: a [Typer](https://typer.tiangolo.com/) command-line interface with one
  command per step of the demo, and [marimo](https://marimo.io/) notebooks for the
  results, because a notebook runs as an app without an editor.
- Technology: [uv](https://docs.astral.sh/uv/) for the host environment, because it
  builds `torch-scatter` from source, so host tools can import gridfm-graphkit.
- Decomposition: the host is separated from the federation. The gridfm CLI runs on the
  host and controls the federation through the `docker compose` and `flwr` commands,
  while `flower_app/` is the code Flower ships into the containers.
- Decomposition: what is trained is separated from where it is trained. An experiment in
  `flower_app/experiments/<name>/` holds the model and the training procedure, and a
  federation in `federations/<name>/` holds the clients, their data and the Compose
  file. Because the two are independent, a run can train any experiment on any
  federation.
- Organization: changes are specified before they are built, with OpenSpec proposals in
  `openspec/` and architecture decision records, so that the reasons behind the code are
  written down for a small, changing team.

| Quality Goal                               | Solution Approach                                                                                                                               |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Flexible: any experiment on any federation | An experiment learns its data from the `ClientDataset` the driver builds from the SuperNode's node config.                                      |
| Reliable: runs are reproducible            | The server seeds from the run config and sends the seed with every train message. Each client seeds from the seed, the round and its client ID. |
| Secure: data stays on the clients          | Each ClientApp container mounts only its own client's data. Clients reply with weights and metrics only.                                        |
| Operable: one command per step             | `gridfm` wraps data generation, Compose and `flwr run`, and checks the preconditions of each step before running it.                            |
