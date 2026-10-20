# 9. Architecture Decisions

Three decisions are recorded, each as an architecture decision record (ADR). A decision
gets a record when it is hard to reverse, affects several building blocks or has a
trade-off that a reader would otherwise question. A new record starts as proposed and
becomes accepted once the maintainers agree. An accepted record is frozen. To change a
decision, write a new record and set the status of the old one to superseded by the new
one. OpenSpec reads these records before it writes a change, as configured in
`openspec/config.yaml`.

## 9.1 ADR 1: Run Inference on the Host, with torch-scatter as a Project Dependency

Accepted on 2026-10-08.

### Context

A trained model is saved to `outputs/` on the host, and the demo needs to run it on
client data to show its predictions. gridfm-graphkit, which builds and runs the model,
imports `torch_scatter`, which until then was installed only in the Docker images. Where
should inference run?

### Decision

Inference runs on the host, and `torch-scatter` is a dependency of the project, built
from source by `uv sync`. This keeps the containers to a single purpose, training.
Flower ships the project's code to the containers as a bundle at run time, so the images
hold no project code: inference in a container would need the code mounted or baked into
an image built for training.

### Consequences

- Good, because the containers only train, and everything that uses a finished run
  happens on the host.
- Good, because host code and tests can import gridfm-graphkit and the experiments.
- Bad, because `uv sync` compiles `torch-scatter`, which takes about two minutes the
  first time and needs a C++ compiler on every contributor's machine.
- Bad, because a torch upgrade can break the build until `torch-scatter` supports the
  new version.

### Alternatives

| Alternative                                                                                 | Why Rejected                                                                                          |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Run inference in a one-off container from the ClientApp image                               | The image holds no project code, so the code would have to be mounted or baked into a training image. |
| Replace `torch_scatter` with `torch_geometric.utils.scatter` in the fork of gridfm-graphkit | Removes the dependency everywhere, but adds a patch to maintain in another repository.                |

## 9.2 ADR 2: Runs That Save a Model Also Save the Configuration to Rebuild It

Accepted on 2026-10-08.

### Context

A run of an experiment that trains one shared model saves its weights as a state dict in
`final_model.pt`. Weights alone cannot be loaded: the model must first be rebuilt from
the gridfm-graphkit configuration it was trained with, which lives in the experiment's
Python code and changes over time. How do tools on the host rebuild the model of a past
run?

### Decision

Every experiment that saves a model must also save, in the same folder, the complete
gridfm-graphkit configuration the model was built from, as plain JSON in
`graphkit_config.json`. The client-specific `data.networks` and `data.scenarios` are
left out. This makes each run folder self-describing.

### Consequences

- Good, because host tools rebuild a run's model from its folder alone, without
  importing `flower_app`.
- Good, because changing an experiment's configuration does not break its old runs.
- Bad, because runs made before this record cannot be rebuilt and must be run again.
- Bad, because the configuration must stay JSON-serializable.

### Alternatives

| Alternative                                                                  | Why Rejected                                                                                        |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Rebuild the model from the current version of the experiment's configuration | Breaks old runs as soon as the configuration changes, and makes the gridfm CLI import `flower_app`. |
| Pickle the whole Lightning module                                            | Depends on the import paths of gridfm-graphkit's classes and breaks when gridfm-graphkit changes.   |

## 9.3 ADR 3: Only the Federation Writes `outputs/`; Results Made on the Host Go Elsewhere

Accepted on 2026-10-08.

### Context

The ServerApp container writes each run's outputs to
`outputs/<federation>/<experiment>/<timestamp>/`, which is mounted from the host. The
container runs as root, so the run folders belong to root and the host user cannot write
into them. Where do results that the host computes from a run, such as predictions, go?

### Decision

Only the federation writes to `outputs/`. Every result the host makes from a run goes to
its own top-level folder with the same `<federation>/<experiment>/<timestamp>/` layout,
such as `predictions/<federation>/<experiment>/<timestamp>/`. This needs no change to
the federation and works for every existing run.

### Consequences

- Good, because a run's outputs are never changed after the run, so they always show
  what the federation produced.
- Good, because host results can be deleted and recomputed without touching the runs.
- Bad, because a run's results are spread over two folders that tools must join by path.

### Alternatives

| Alternative                                                          | Why Rejected                                                                    |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Run the ServerApp as the host user, so that run folders are writable | Needs the user's IDs in every Compose file and leaves existing runs unwritable. |
