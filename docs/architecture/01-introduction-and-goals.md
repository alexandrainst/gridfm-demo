# 1. Introduction and Goals

## 1.1 Requirements Overview

GridFM Demo shows how federated learning can train a foundation model for the power
grid. Several clients each hold their own synthetic power grid data, and a power flow
model from the Python library
[gridfm-graphkit](https://github.com/gridfm/gridfm-graphkit) is trained across them with
the federated learning framework [Flower](https://flower.ai/), without the data leaving
the clients. The essential features are:

- Generate a synthetic dataset per client with the Python library
  [gridfm-datakit](https://github.com/gridfm/gridfm-datakit), from fictional grid
  topologies.
- Start and stop a federation of Docker containers, one server and one or more clients,
  with a single command each.
- Train a gridfm-graphkit power flow model across the clients with a federated learning
  strategy, and train it on each client alone as a baseline.
- Write the metrics, the trained model and the configuration it was built from to a run
  folder on the host.
- Predict every client's scenarios with the model of a finished run, on the host.
- Plot a scenario's input, power flow solution, prediction and error as a network in a
  marimo notebook.

## 1.2 Quality Goals

The goals are ordered by priority. They are stated as goals only, without measurable
scenarios, because the system is a demo.

| Priority | Quality Goal                               | Meaning in This Project                                                                            |
| -------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| 1        | Flexible: any experiment on any federation | Adding an experiment needs no change to a federation, and the other way around.                    |
| 2        | Reliable: runs are reproducible            | Two runs with the same seed, experiment and federation give the same metrics.                      |
| 3        | Secure: data stays on the clients          | A client's data never leaves its container. The server sees weights and metrics.                   |
| 4        | Operable: one command per step             | A newcomer runs the demo end to end with `gridfm` commands, without manual Docker or Flower steps. |

## 1.3 Stakeholders

| Role                | Contact                                                                       | Expectations                                                          |
| ------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Maintainers         | Étienne Bourbeau and Michael Iversen, listed under Maintainers in `README.md` | The structure, the decisions and the contracts between the parts.     |
| Future contributors |                                                                               | Where to add an experiment or a federation and which invariants hold. |
