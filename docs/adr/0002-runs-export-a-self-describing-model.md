---
status: accepted
date: 2026-10-08
---

# Runs That Save a Model Also Save the Configuration to Rebuild It

## Context and Problem Statement

A run of `fedavg` saves its trained weights as a state dict in `final_model.pt`. Weights
alone cannot be loaded: the model must first be rebuilt from the graphkit configuration
it was trained with, which lives in the experiment's Python code and changes over time.
How do tools on the host rebuild the model of a past run?

## Considered Options

- Save the graphkit configuration as `graphkit_config.json` next to `final_model.pt`.
- Rebuild the model from the current version of the experiment's configuration.
- Pickle the whole Lightning module.

## Decision Outcome

Chosen option: "Save the graphkit configuration as JSON", because it makes each run
folder self-describing. Rebuilding from the current code breaks old runs as soon as the
configuration changes, and it would make `gridfm_cli` import `flower_app`. A pickle
depends on the import paths of graphkit's classes and breaks when graphkit changes.

Every experiment that saves a model must also save, in the same folder, the complete
graphkit configuration the model was built from, as plain JSON. The client-specific
`data.networks` and `data.scenarios` are left out.

### Consequences

- Good, because host tools rebuild a run's model from its folder alone, without
  importing `flower_app`.
- Good, because changing an experiment's configuration does not break its old runs.
- Bad, because runs made before this record cannot be rebuilt and must be run again.
- Bad, because the configuration must stay JSON-serializable.
