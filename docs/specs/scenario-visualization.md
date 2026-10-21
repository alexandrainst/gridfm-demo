# scenario-visualization Specification

## Purpose

Metrics such as a mean squared error say how good a model is on average, but not where
on the grid it is wrong or what it was given to work with. This capability is a notebook
that draws one scenario of one client as a network in 2D, four times: the values the
model receives as input, the true power flow solution, the model's prediction and the
error. It lets a developer or an audience see a federated model's behavior on a concrete
grid. Without it, the demo can show only loss curves.

## Requirements

### Requirement: Choose a run, a client, a scenario and a feature

The notebook must show any predicted scenario without code edits. It SHALL offer a
choice of run among the runs that have predictions, a choice of client, a number input
for the scenario limited to that client's scenarios, and a choice of bus feature among
Vm, Va, Pg and Qg.

#### Scenario: Picking a scenario

- **GIVEN** predictions exist for one FedAvg run of `case14_2clients`
- **WHEN** a developer opens the notebook, picks that run, client 1, scenario 12 and
  feature Va
- **THEN** the notebook shows Va for scenario 12 of client 1

#### Scenario: A scenario number out of range

- **GIVEN** client 0 has scenarios 0 to 39
- **WHEN** a developer tries to enter scenario 40
- **THEN** the number input does not accept it

### Requirement: Draw input, truth, prediction and error on the network

Seeing the values on the grid shows where the model is wrong. For the chosen scenario
and feature, the notebook SHALL draw the network four times with the same node
positions: the model's input, the true value, the predicted value and the absolute
error. Truth and prediction SHALL share one color scale and SHALL be drawn next to each
other, and every plot SHALL keep the network's proportions.

#### Scenario: Comparing truth and prediction

- **WHEN** a developer views Vm for a scenario
- **THEN** four network plots appear with the buses at the same positions
- **AND** the truth and prediction plots are next to each other
- **AND** the network has the same shape in all four plots
- **AND** a bus with the same true and predicted Vm has the same color in the truth and
  prediction plots

### Requirement: The input plot marks the values the model must predict

For the power flow task the model is given only some values per bus type, and the
predictions record which. The input plot SHALL show the true value for buses where the
predictions say the feature was given to the model, and SHALL mark the other buses as
hidden.

#### Scenario: Voltage magnitude at a PQ bus

- **GIVEN** bus 13 of `case14_ieee` is a PQ bus
- **WHEN** a developer views Vm
- **THEN** the input plot marks bus 13 as hidden

#### Scenario: Voltage magnitude at a PV bus

- **GIVEN** bus 1 of `case14_ieee` is a PV bus
- **WHEN** a developer views Vm
- **THEN** the input plot colors bus 1 by its true Vm

### Requirement: The layout comes from the network topology

Future networks will not come with coordinates. Node positions SHALL be computed from
the buses and branches in the data alone, and SHALL be the same for every scenario of a
network.

#### Scenario: Switching scenarios

- **WHEN** a developer changes the scenario from 3 to 4 for the same client
- **THEN** every bus keeps its position

### Requirement: Bus type and branch status are visible

A topology perturbation can take a branch out of service, and the bus type decides which
values are hidden. The plots SHALL distinguish PQ, PV and reference buses, and SHALL
distinguish branches that are out of service in the chosen scenario.

#### Scenario: A branch out of service

- **GIVEN** a scenario in which the branch between buses 3 and 4 has `br_status` 0
- **WHEN** a developer views that scenario
- **THEN** that branch is drawn differently from the branches in service

### Requirement: A table lists every bus

Exact values are hard to read from colors. Below the plots, the notebook SHALL show a
table with one row per bus: the bus, its type, the input, the true value, the predicted
value and the error of the chosen feature.

#### Scenario: Reading exact values

- **WHEN** a developer views Pg for a scenario of `case14_ieee`
- **THEN** a table with 14 rows lists the true and predicted Pg of each bus

### Requirement: Each scenario shows its split

Most scenarios were used for training, so an error can only be judged when it is known
whether the model saw the scenario. The notebook SHALL show the split (train, validation
or test) of the chosen scenario next to the scenario input, and SHALL list which
scenario numbers of the chosen client belong to each split.

#### Scenario: Looking at an unseen scenario

- **GIVEN** the test scenarios of client 0 are 24, 25, 30 and 31
- **WHEN** a developer picks client 0
- **THEN** the notebook lists 24, 25, 30 and 31 as test scenarios
- **AND** after entering scenario 24, the label next to the input says test

#### Scenario: Changing the scenario

- **GIVEN** a developer views scenario 24 of client 0
- **WHEN** they change the scenario to 2
- **THEN** the label next to the input changes to train

### Requirement: The notebook explains what it shows

The notebook is shown to people who did not build it. It SHALL open with text that lists
the steps before it can show a model (generate the data, start the federation, run an
experiment that saves a model, run `gridfm predict`), says that it shows a trained model
on the clients' training, validation and test scenarios, and explains the bus symbols
and the four plots.

#### Scenario: A newcomer opens the notebook

- **WHEN** a developer who has never run the demo opens the notebook
- **THEN** the text at the top names `gridfm data`, `gridfm up`, `gridfm run` and
  `gridfm predict` in that order
- **AND** it says that circles are PQ buses, squares PV buses and diamonds the reference
  bus
- **AND** it says what the input, truth, prediction and absolute error plots show

### Requirement: The notebook only reads files

The notebook stays light and quick to open. It SHALL read only the client data and the
prediction files, and SHALL NOT load or run a model.

#### Scenario: Opening the notebook on a fresh checkout

- **GIVEN** a developer has the client data but has not run `gridfm predict`
- **WHEN** they open the notebook
- **THEN** the notebook says that no run has predictions and that `gridfm predict` makes
  them
