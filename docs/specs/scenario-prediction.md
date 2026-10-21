# scenario-prediction Specification

## Purpose

A finished run leaves a trained model, but the demo has no way to see what that model
predicts for a given scenario. This capability runs a run's exported model on the host
over the federation's client data and stores, for every bus of every scenario, the true
power flow solution next to the prediction. The stored predictions let the notebook plot
results without running a model itself. Without this capability, judging a model would
require running inference by hand inside a container built only for training.

## Requirements

### Requirement: Predict every scenario of every client with a run's model

The notebook needs a prediction for any scenario a developer picks. `gridfm predict`
SHALL rebuild the model of a chosen run from that run's exported files and predict every
scenario of every client dataset of the run's federation.

#### Scenario: Predicting a FedAvg run

- **GIVEN** the federation `case14_2clients` with two clients of 40 scenarios each
- **AND** a finished FedAvg run that exported `final_model.pt` and
  `graphkit_config.json`
- **WHEN** a developer runs `gridfm predict case14_2clients <run>`
- **THEN** the command writes predictions for scenarios 0 to 39 of client 0 and of
  client 1

### Requirement: Predictions hold truth and prediction per bus

The notebook compares the model with the solver and shows which values the model was
given. The predictions of each client SHALL hold one row per scenario and bus, with the
bus type (PQ, PV or REF), the load (Pd, Qd), the true and predicted Vm, Va, Pg and Qg,
whether the model was given each of these four values, and whether the scenario was in
the client's train, validation or test split.

#### Scenario: Looking up one bus

- **GIVEN** predictions written for client 0 of `case14_2clients`
- **WHEN** a developer reads the rows for scenario 17
- **THEN** there are 14 rows, one per bus of `case14_ieee`
- **AND** each row has the bus type, Pd, Qd, the true and predicted Vm, Va, Pg and Qg,
  whether each of the four was given, and the split

#### Scenario: Which values a PQ bus was given

- **GIVEN** bus 13 of `case14_ieee` is a PQ bus
- **WHEN** a developer reads its row for any scenario
- **THEN** the row says that Vm and Va were not given to the model

### Requirement: Values are in physical units

Normalized values cannot be compared with the solver's output. Predicted and true values
SHALL be in the units of the datakit data: Vm in per unit, Va in degrees, and powers in
MW and MVAr.

#### Scenario: True values match the generated data

- **GIVEN** predictions written for client 0
- **WHEN** a developer compares the true Vm of scenario 3 with `Vm` in that client's
  `bus_data.parquet` for scenario 3
- **THEN** the values are equal up to floating point precision

### Requirement: Normalization matches the client's training

Each client fitted its own normalizer on its own data during training, so the model
expects inputs scaled the same way. Before predicting a client's data, the command SHALL
fit the normalizer on that client's data with the same settings the client used during
training.

#### Scenario: Two clients with different load levels

- **GIVEN** client 0 and client 1 were generated with different seeds and so have
  different load levels
- **WHEN** a developer runs `gridfm predict` on a FedAvg run
- **THEN** each client's predictions are made with the normalizer fitted on that
  client's own data

### Requirement: Predictions are written to a tree that mirrors outputs

The notebook finds predictions by run, and the run folders in `outputs/` are owned by
`root`, so the host cannot write there. The command SHALL write one Parquet file per
client to `predictions/<federation>/<experiment>/<run>/client_<i>.parquet` and SHALL NOT
write to `outputs/`.

#### Scenario: Where the predictions land

- **WHEN** a developer runs
  `gridfm predict case14_2clients fedavg/2026-10-07_08-49-43-266Z`
- **THEN** the files
  `predictions/case14_2clients/fedavg/2026-10-07_08-49-43-266Z/client_0.parquet` and
  `client_1.parquet` exist
- **AND** nothing under `outputs/` has changed

#### Scenario: Predicting the same run again

- **GIVEN** predictions already exist for a run
- **WHEN** a developer runs `gridfm predict` on that run again
- **THEN** the command replaces the existing files

### Requirement: Runs that cannot be predicted are refused

A developer may pick a run of an experiment that saves no model, or a run made before
runs exported their configuration. The command SHALL refuse a run that lacks
`final_model.pt` or `graphkit_config.json`, name the missing file, and write nothing.

#### Scenario: Picking an isolated run

- **WHEN** a developer runs `gridfm predict` on a run of the `isolated` experiment
- **THEN** the command fails with a message that the run has no `final_model.pt`
- **AND** no predictions folder is created for the run

#### Scenario: Picking a run from before this change

- **GIVEN** a FedAvg run folder with `final_model.pt` but no `graphkit_config.json`
- **WHEN** a developer runs `gridfm predict` on it
- **THEN** the command fails with a message that the run has no `graphkit_config.json`
  and must be run again

### Requirement: Prediction runs on the host without the federation

Prediction is separate from training, so it must not depend on the containers.
`gridfm predict` SHALL run on the host and SHALL work while the federation is down.

#### Scenario: Federation stopped

- **GIVEN** a developer ran `gridfm down case14_2clients` after a FedAvg run
- **WHEN** they run `gridfm predict` on that run
- **THEN** the command writes the predictions

### Requirement: Missing arguments are prompted for

The other `gridfm` commands ask for a federation when none is given. When the federation
or the run is not given, the command SHALL ask the developer to choose one, offering
only runs that have both exported files.

#### Scenario: No arguments

- **GIVEN** `case14_2clients` has two isolated runs and three FedAvg runs, of which one
  has `graphkit_config.json`
- **WHEN** a developer runs `gridfm predict` without arguments
- **THEN** the command asks for a federation and then offers only that one FedAvg run
