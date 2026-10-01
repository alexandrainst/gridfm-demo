# MATPOWER Data File Format

---

## Overview

There are two versions of the **MATPOWER case file format**:

- **Version 1**: Used by MATPOWER 3.0.0 and earlier.
- **Version 2**: Used by subsequent versions of MATPOWER. Version 1 files are still
  supported and automatically converted by `loadcase` and `savecase` functions.

In **Version 2**, the input data for MATPOWER are specified in a set of data matrices
packaged as fields of a MATLAB struct, referred to as a **"MATPOWER case" struct** and
conventionally denoted by the variable `mpc`. This struct is typically defined in a case
file, either:

- A function M-file whose return value is the `mpc` struct, or
- A MAT-file that defines a variable named `mpc` when loaded.

The fields of this struct are:

- `baseMVA` (scalar)
- `bus` (matrix)
- `branch` (matrix)
- `gen` (matrix)
- `gencost` (matrix, optional)

Each row in the data matrices corresponds to a single bus, branch, or generator, and the
columns are similar to the columns in the standard IEEE and PTI formats. The `mpc`
struct also includes a `version` field, whose value is a string set to the current
MATPOWER case version (default: `'2'`).

The **Version 1** case format defines the data matrices as individual variables rather
than fields of a struct, and some do not include all of the columns defined in
Version 2.

---

## Case File Examples

Numerous examples can be found in the case files listed in **Table D-18** in Appendix D.
The case files created by `savecase` use a **tab-delimited format** for the data
matrices to facilitate seamless data transfer between a text editor and a spreadsheet
via copy and paste.

For more details, type `help caseformat` at the MATLAB prompt.

---

## BaseMVA Field

The `baseMVA` field is a **scalar value** specifying the system MVA base used for
converting power into per unit quantities.

For convenience and code portability, the following constants are defined:

- `idx_bus`: Named indices for the columns of the `bus` matrix.
- `idx_brch`: Named indices for the columns of the `branch` matrix.
- `idx_gen`: Named indices for the columns of the `gen` matrix.
- `idx_cost`: Named indices for the columns of the `gencost` matrix.

The script `define_constants` provides a simple way to define all the usual constants at
once. These names appear in the first column of the tables below.

---

## Additional Fields

The MATPOWER case format allows for **additional fields** to be included in the
structure. The OPF (Optimal Power Flow) is designed to recognize the following fields as
parameters to directly extend the OPF formulation:

- `A`, `l`, `u`, `H`, `Cw`, `N`, `fparm`, `z0`, `zl`, `zu`

Additional **standard optional fields** include:

- `bus_name`
- `gentype`
- `genfuel`
- User-defined fields (e.g., `reserves`)

The `loadcase` function automatically loads any extra fields from a case file. If the
appropriate `'savecase'` callback function is added via `add_userfcn`, `savecase` will
also save them back to a case file.

---

## Bus Data (`mpc.bus`)

| Name     | Column | Description                                             |
| -------- | ------ | ------------------------------------------------------- |
| BUS_I    | 1      | Bus number (positive integer)                           |
| BUS_TYPE | 2      | Bus type (1 = PQ, 2 = PV, 3 = ref, 4 = isolated)        |
| PD       | 3      | Real power demand (MW)                                  |
| QD       | 4      | Reactive power demand (MVAr)                            |
| GS       | 5      | Shunt conductance (MW demanded at V = 1.0 p.u.)         |
| BS       | 6      | Shunt susceptance (MVAr injected at V = 1.0 p.u.)       |
| BUS_AREA | 7      | Area number (positive integer)                          |
| VM       | 8      | Voltage magnitude (p.u.)                                |
| VA       | 9      | Voltage angle (degrees)                                 |
| BASE_KV  | 10     | Base voltage (kV)                                       |
| ZONE     | 11     | Loss zone (positive integer)                            |
| VMAX     | 12     | Maximum voltage magnitude (p.u.)                        |
| VMIN     | 13     | Minimum voltage magnitude (p.u.)                        |
| LAM_P†   | 14     | Lagrange multiplier on real power mismatch (1/MW)       |
| LAM_Q†   | 15     | Lagrange multiplier on reactive power mismatch (1/MVAr) |
| MU_VMAX† | 16     | Kuhn-Tucker multiplier on upper voltage limit (1/p.u.)  |
| MU_VMIN† | 17     | Kuhn-Tucker multiplier on lower voltage limit (1/p.u.)  |

† Included in OPF output, typically not included (or ignored) in input matrix.

---

## Generator Data (`mpc.gen`)

| Name       | Column | Description                                                  |
| ---------- | ------ | ------------------------------------------------------------ |
| GEN_BUS    | 1      | Bus number                                                   |
| PG         | 2      | Real power output (MW)                                       |
| QG         | 3      | Reactive power output (MVAr)                                 |
| QMAX       | 4      | Maximum reactive power output (MVAr)                         |
| QMIN       | 5      | Minimum reactive power output (MVAr)                         |
| VG‡        | 6      | Voltage magnitude setpoint (p.u.)                            |
| MBASE      | 7      | Total MVA base of machine, defaults to `baseMVA`             |
| GEN_STATUS | 8      | Machine status (1 = in-service, 0 = out-of-service)          |
| PMAX       | 9      | Maximum real power output (MW)                               |
| PMIN       | 10     | Minimum real power output (MW)                               |
| PC1\*      | 11     | Lower real power output of PQ capability curve (MW)          |
| PC2\*      | 12     | Upper real power output of PQ capability curve (MW)          |
| QC1MIN\*   | 13     | Minimum reactive power output at PC1 (MVAr)                  |
| QC1MAX\*   | 14     | Maximum reactive power output at PC1 (MVAr)                  |
| QC2MIN\*   | 15     | Minimum reactive power output at PC2 (MVAr)                  |
| QC2MAX\*   | 16     | Maximum reactive power output at PC2 (MVAr)                  |
| RAMP_AGC\* | 17     | Ramp rate for load following/AGC (MW/min)                    |
| RAMP_10\*  | 18     | Ramp rate for 10-minute reserves (MW)                        |
| RAMP_30\*  | 19     | Ramp rate for 30-minute reserves (MW)                        |
| RAMP_Q\*   | 20     | Ramp rate for reactive power (2-second timescale) (MVAr/min) |
| APF\*      | 21     | Area participation factor                                    |
| MU_PMAX†   | 22     | Kuhn-Tucker multiplier on upper limit (1/MW)                 |
| MU_PMIN†   | 23     | Kuhn-Tucker multiplier on lower limit (1/MW)                 |
| MU_QMAX†   | 24     | Kuhn-Tucker multiplier on upper limit (1/MVAr)               |
| MU_QMIN†   | 25     | Kuhn-Tucker multiplier on lower limit (1/MVAr)               |

\*Not included in Version 1 case format. † Included in OPF output, typically not
included (or ignored) in input matrix. ‡ Used to determine voltage setpoint for OPF only
if `opf.use_vg` option is non-zero (default: 0)

---

## Branch Data (`mpc.branch`)

| Name       | Column | Description                                                                                                      |
| ---------- | ------ | ---------------------------------------------------------------------------------------------------------------- |
| F_BUS      | 1      | "From" bus number                                                                                                |
| T_BUS      | 2      | "To" bus number                                                                                                  |
| BR_R       | 3      | Resistance (p.u.)                                                                                                |
| BR_X       | 4      | Reactance (p.u.)                                                                                                 |
| BR_B       | 5      | Total line charging susceptance (p.u.)                                                                           |
| RATE_A\*   | 6      | MVA rating A (long-term rating), set to 0 for unlimited                                                          |
| RATE_B\*   | 7      | MVA rating B (short-term rating), set to 0 for unlimited                                                         |
| RATE_C\*   | 8      | MVA rating C (emergency rating), set to 0 for unlimited                                                          |
| TAP        | 9      | Transformer off-nominal turns ratio (taps at "from" bus, impedance at "to" bus; set to 0 for transmission lines) |
| SHIFT      | 10     | Transformer phase shift angle (degrees), positive delay                                                          |
| BR_STATUS  | 11     | Initial branch status (1 = in-service, 0 = out-of-service)                                                       |
| ANGMIN†    | 12     | Minimum angle difference (degrees)                                                                               |
| ANGMAX†    | 13     | Maximum angle difference (degrees)                                                                               |
| PF‡        | 14     | Real power injected at "from" bus end (MW)                                                                       |
| QF‡        | 15     | Reactive power injected at "from" bus end (MVAr)                                                                 |
| PT‡        | 16     | Real power injected at "to" bus end (MW)                                                                         |
| QT‡        | 17     | Reactive power injected at "to" bus end (MVAr)                                                                   |
| MU_SF§     | 18     | Kuhn-Tucker multiplier on MVA limit at "from" bus (1/MVA)                                                        |
| MU_ST§     | 19     | Kuhn-Tucker multiplier on MVA limit at "to" bus (1/MVA)                                                          |
| MU_ANGMIN§ | 20     | Kuhn-Tucker multiplier on lower angle difference limit (1/degree)                                                |
| MU_ANGMAX§ | 21     | Kuhn-Tucker multiplier on upper angle difference limit (1/degree)                                                |

\*Used to specify branch flow limits. By default, these are limits on apparent power
(MVA). The `opf.flow_lim` option can specify limits on active power or current (MW or
kA, respectively). †Not included in Version 1 case format. The voltage angle difference
is unbounded below if `ANGMIN` is missing and unbounded above if `ANGMAX` is missing. If
both are zero, the voltage angle difference is unconstrained. ‡Included in power flow
and OPF output, ignored on input. §Included in OPF output, typically not included (or
ignored) in input matrix

---

## Generator Cost Data (`mpc.gencost`)

| Name     | Column | Description                                                                                                                                |
| -------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| MODEL    | 1      | Cost model (1 = piecewise linear, 2 = polynomial)                                                                                          |
| STARTUP  | 2      | Startup cost (US dollars)\*                                                                                                                |
| SHUTDOWN | 3      | Shutdown cost (US dollars)\*                                                                                                               |
| NCOST    | 4      | Number of data points defining an n-segment piecewise linear cost function, or coefficients defining an nth-order polynomial cost function |
| COST     | 5+     | Parameters defining total cost function (units: $/hr for cost, MW or MVAr for power)                                                       |

\*For **MODEL = 1** (piecewise linear):

- The cost is defined by the coordinates `(x1, y1), (x2, y2), ...` of the
  end/break-points of the piecewise linear cost function.

\*For **MODEL = 2** (polynomial):

- Coefficients of the nth-order polynomial cost function, starting with the highest
  order.

†If `gen` has `n` rows, the first `n` rows of `gencost` contain the costs for active
power produced by the corresponding generators. If `gencost` has `2n` rows, rows `n+1`
to `2n` contain the reactive power costs in the same format. \*Not currently used by any
MATPOWER functions

---

## DC Line Data (`mpc.dcline`)

| Name      | Column | Description                                                      |
| --------- | ------ | ---------------------------------------------------------------- |
| F_BUS     | 1      | "From" bus number                                                |
| T_BUS     | 2      | "To" bus number                                                  |
| BR_STATUS | 3      | Initial branch status (1 = in-service, 0 = out-of-service)       |
| PF†       | 4      | Real power flow at "from" bus end (MW), positive = "from" → "to" |
| PT†       | 5      | Real power flow at "to" bus end (MW), positive = "from" → "to"   |
| QF†       | 6      | Reactive power injected into "from" bus (MVAr)                   |
| QT†       | 7      | Reactive power injected into "to" bus (MVAr)                     |
| VF        | 8      | Voltage magnitude setpoint at "from" bus (p.u.)                  |
| VT        | 9      | Voltage magnitude setpoint at "to" bus (p.u.)                    |
| PMIN      | 10     | Lower limit on PF (if positive) or PT (if negative) (MW)         |
| PMAX      | 11     | Upper limit on PF (if positive) or PT (if negative) (MW)         |
| QMINF     | 12     | Lower limit on reactive power injection into "from" bus (MVAr)   |
| QMAXF     | 13     | Upper limit on reactive power injection into "from" bus (MVAr)   |
| QMINT     | 14     | Lower limit on reactive power injection into "to" bus (MVAr)     |
| QMAXT     | 15     | Upper limit on reactive power injection into "to" bus (MVAr)     |
| LOSS0     | 16     | Coefficient of constant term of linear loss function (MW)        |
| LOSS1     | 17     | Coefficient of linear term of linear loss function (MW/MW)       |
| MU_PMIN‡  | 18     | Kuhn-Tucker multiplier on lower flow limit at "from" bus (1/MW)  |
| MU_PMAX‡  | 19     | Kuhn-Tucker multiplier on upper flow limit at "from" bus (1/MW)  |
| MU_QMINF‡ | 20     | Kuhn-Tucker multiplier on lower VAr limit at "from" bus (1/MVAr) |
| MU_QMAXF‡ | 21     | Kuhn-Tucker multiplier on upper VAr limit at "from" bus (1/MVAr) |
| MU_QMINT‡ | 22     | Kuhn-Tucker multiplier on lower VAr limit at "to" bus (1/MVAr)   |
| MU_QMAXT‡ | 23     |                                                                  |

\*Requires explicit use of `toggle_dcline`. †Output column, value updated by power flow
or OPF (except PF in case of simple power flow). ‡Included in OPF output, typically not
included (or ignored) in input matrix.
