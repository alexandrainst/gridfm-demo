# Spec Delta

## Purpose

A training run that produces a shared model leaves its weights in the run's output
folder on the host. Weights alone cannot be loaded: the model must first be rebuilt with
the architecture and task it was trained with, and that configuration lives in the
experiment's Python code, which changes over time. Without an export that describes the
model, a run's model could only be used while the code still matched it, and predicting
with an older run would silently build the wrong model or fail. This capability makes
each run folder self-describing, so tools on the host can rebuild the model from the
folder alone.

## ADDED Requirements

### Requirement: Runs export the configuration their model was built from

A model cannot be rebuilt from its weights alone, and the experiment's configuration
code may change after the run. When an experiment run saves a trained model, it SHALL
also save, in the same output folder, the complete graphkit configuration the model was
built from, except for the client-specific dataset settings.

#### Scenario: A FedAvg run finishes

- **GIVEN** the federation `case14_2clients` is up
- **WHEN** a developer runs `gridfm run fedavg` and the run finishes
- **THEN** the run's folder under `outputs/case14_2clients/fedavg/` holds
  `final_model.pt` and `graphkit_config.json`
- **AND** `graphkit_config.json` holds the task, data, model, optimizer and training
  settings of the run

#### Scenario: The experiment's configuration changes after a run

- **GIVEN** a FedAvg run that finished with `hidden_size` 32
- **WHEN** a developer changes `hidden_size` to 64 in the FedAvg experiment's graphkit
  configuration
- **THEN** that run's `graphkit_config.json` still says `hidden_size` 32

### Requirement: Exported configuration is plain JSON

Host tools read the export without importing the experiment's code. The exported
configuration SHALL be a JSON file that holds only JSON values.

#### Scenario: Reading the export without the experiment

- **GIVEN** a finished FedAvg run
- **WHEN** a developer loads its `graphkit_config.json` with a JSON parser
- **THEN** the parser returns the configuration without error

### Requirement: Experiments without a shared model export nothing new

Only experiments that produce one model can be used for prediction, and an export
without a model would mislead tools that look for one. An experiment run that saves no
model SHALL NOT write a graphkit configuration export.

#### Scenario: An isolated run finishes

- **WHEN** a developer runs `gridfm run isolated` and the run finishes
- **THEN** the run's folder holds no `final_model.pt` and no `graphkit_config.json`
