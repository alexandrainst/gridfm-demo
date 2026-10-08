---
status: accepted
date: 2026-10-08
---

# Run Inference on the Host, with torch-scatter as a Project Dependency

## Context and Problem Statement

A trained model is saved to `outputs/` on the host, and the demo needs to run it on
client data to show its predictions. gridfm-graphkit, which builds and runs the model,
imports `torch_scatter`, which until now was installed only in the Docker images. Where
should inference run?

## Considered Options

- Run inference on the host, and make `torch-scatter` a dependency of the project, built
  from source by `uv sync`.
- Run inference in a one-off container from the ClientApp image.
- Replace `torch_scatter` with `torch_geometric.utils.scatter` in the project's fork of
  gridfm-graphkit.

## Decision Outcome

Chosen option: "Run inference on the host", because it keeps the containers to a single
purpose, training. Flower ships the project's code to the containers as a bundle at run
time, so the images hold no project code: inference in a container would need the code
mounted or baked into an image built for training. Patching the fork would remove the
dependency everywhere, but it adds a patch to maintain in another repository.

### Consequences

- Good, because the containers only train, and everything that uses a finished run
  happens on the host.
- Good, because host code and tests can import gridfm-graphkit and the experiments.
- Bad, because `uv sync` compiles `torch-scatter`, which takes about two minutes the
  first time and needs a C++ compiler on every contributor's machine.
- Bad, because a torch upgrade can break the build until `torch-scatter` supports the
  new version.
