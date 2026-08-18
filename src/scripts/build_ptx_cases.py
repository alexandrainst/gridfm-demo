#!/usr/bin/env python3
"""
Generate standard MATPOWER (.m) case files for the Danish PtX siting demo,
using pandapower as the single source of truth.

Workflow per scenario:
    1. build a pandapower `net` from physical inputs (km, Ohm/km, MW, kV)
    2. solve it with pp.runpp  ->  GROUND TRUTH (res_bus, res_line saved to CSV)
    3. convert with pandapower.converter.to_mpc  ->  per-unit mpc dict
    4. serialise that dict to a standard MATPOWER .m text file

pandapower owns all the electrical/per-unit maths; this script only formats
text.  Every tunable assumption lives in the CONFIG block.

Five-bus fictional network:
    A = DSO consumer (PQ load)        B = DSO consumer (PQ load)
    C = external grid tie (slack)     G = gas power plant (PV gen)
    P = Power-to-X site (solar - electrolysis), a net PQ injection (neg. load)

Topology: fixed 400 kV ring A-G-B-C-A + P spurred to all four corners.
Line length = Euclidean distance between bus (x, y) coordinates [km].
"""

import math
import os
import warnings

import numpy as np

warnings.filterwarnings("ignore")
import pandapower as pp
from pandapower.converter.matpower import to_mpc

# ----------------------------------------------------------------------------
# CONFIG  (every assumed value lives here -- override freely)
# ----------------------------------------------------------------------------
BASE_MVA = 100.0
V_BASE_KV = 400.0                       # transmission level (loads are GW-scale)

# 400 kV single-circuit overhead line, per km
R_PER_KM = 0.025                        # ohm/km
X_PER_KM = 0.30                         # ohm/km
C_PER_KM_NF = 12.0                      # nF/km

RATE_A, RATE_B, RATE_C = 1400.0, 1600.0, 1800.0          # MVA thermal ratings
MAX_I_KA = RATE_A / (math.sqrt(3) * V_BASE_KV)           # current rating [kA]

HOURS_PER_YEAR = 8760.0
LOAD_PF = 0.95                          # lagging power factor for DSO loads
Q_OVER_P = math.tan(math.acos(LOAD_PF))

A_GWH, B_GWH = 10000.0, 2000.0          # annual delivered energy
A_PD = A_GWH * 1000.0 / HOURS_PER_YEAR  # MW (annual-average power)
B_PD = B_GWH * 1000.0 / HOURS_PER_YEAR

P_SOLAR_MW, P_ELYS_MW = 304.0, 54.0     # PtX site components
P_NET_INJ = P_SOLAR_MW - P_ELYS_MW      # +250 MW injected (modelled as neg load)

G_PG, G_VG = 800.0, 1.02                # gas plant (PV)
G_QMAX, G_QMIN = 400.0, -300.0
G_PMAX, G_PMIN = 900.0, 200.0

C_VG = 1.00                             # slack / external grid voltage
WIDE = 9999.0                           # "unlimited" for slack P/Q

VMAX, VMIN = 1.10, 0.90                 # voltage band

FIXED_COORDS = {
    "A": (-100.0, 0.0),
    "B": (100.0, 0.0),
    "C": (0.0, -100.0),
    "G": (0.0, 100.0),
}
SCENARIOS = {
    "s1": (0.0, 0.0),
    "s2": (100.0, 100.0),
    "s3": (250.0, 0.0),
    "s4": (5.0, 0.0),
    "s5": (0.0, -500.0),
    "s6": (0.0, -900.0),     # longest spur P-G = 1000 km (Hydro-Quebec scale)
}
LINES = [
    ("A", "G"), ("G", "B"), ("B", "C"), ("C", "A"),     # backbone ring
    ("P", "A"), ("P", "B"), ("P", "C"), ("P", "G"),     # P spurs
]


# Shunt reactor compensation at bus P (cancels long-line charging).
# Scenarios listed here get a reactor sized to absorb COMP_FRACTION of the
# capacitive charging the P-spurs dump at bus P (Hydro-Quebec-style).
COMP_FRACTION = 1.0
COMP_SCENARIOS = {"s6"}

_B_PER_KM = 2 * math.pi * 50.0 * C_PER_KM_NF * 1e-9   # S/km


def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def p_charging_mvar(coords):
    """Capacitive MVAr the P-end half of every P-spur injects at 1 p.u."""
    total = 0.0
    for f, t in LINES:
        if "P" in (f, t):
            L = dist(coords[f], coords[t])
            total += (V_BASE_KV * 1e3) ** 2 * (_B_PER_KM * L / 2.0) / 1e6
    return total


def build_net(p_coord, comp_fraction=0.0):
    """Build the 5-bus pandapower net for a given P coordinate."""
    coords = dict(FIXED_COORDS, P=p_coord)
    net = pp.create_empty_network(sn_mva=BASE_MVA, f_hz=50.0)

    bus = {}
    for nm in ["A", "B", "C", "G", "P"]:
        bus[nm] = pp.create_bus(net, vn_kv=V_BASE_KV, name=nm,
                                 max_vm_pu=VMAX, min_vm_pu=VMIN)

    # Slack: external grid tie C
    pp.create_ext_grid(net, bus["C"], vm_pu=C_VG, va_degree=0.0, name="C",
                       max_p_mw=WIDE, min_p_mw=-WIDE,
                       max_q_mvar=WIDE, min_q_mvar=-WIDE)
    # PV generator: gas plant G
    pp.create_gen(net, bus["G"], p_mw=G_PG, vm_pu=G_VG, name="G",
                  max_q_mvar=G_QMAX, min_q_mvar=G_QMIN,
                  max_p_mw=G_PMAX, min_p_mw=G_PMIN, slack=False)
    # PQ loads: DSO consumers A, B
    pp.create_load(net, bus["A"], p_mw=A_PD, q_mvar=A_PD * Q_OVER_P, name="A")
    pp.create_load(net, bus["B"], p_mw=B_PD, q_mvar=B_PD * Q_OVER_P, name="B")
    # PtX site P: net injection as a negative load (PQ bus, no V regulation)
    pp.create_load(net, bus["P"], p_mw=-P_NET_INJ, q_mvar=0.0, name="P")

    lengths = {}
    for f, t in LINES:
        L = dist(coords[f], coords[t])
        lengths[(f, t)] = L
        pp.create_line_from_parameters(
            net, bus[f], bus[t], length_km=L,
            r_ohm_per_km=R_PER_KM, x_ohm_per_km=X_PER_KM,
            c_nf_per_km=C_PER_KM_NF, g_us_per_km=0.0,
            max_i_ka=MAX_I_KA, name="%s-%s" % (f, t))

    # Shunt reactor at P: q_mvar > 0 absorbs reactive power (inductive).
    comp_mvar = comp_fraction * p_charging_mvar(coords)
    if comp_mvar > 0:
        pp.create_shunt(net, bus["P"], q_mvar=comp_mvar, p_mw=0.0,
                        name="P-reactor")
    return net, coords, lengths, comp_mvar


def fmt_row(vals, fmts):
    return "\t" + "\t".join(f % v for f, v in zip(fmts, vals)) + ";"


def write_m(mpc, path, name, coords, lengths, header):
    """Serialise an mpc dict (from to_mpc) to a standard MATPOWER .m file."""
    bus = np.atleast_2d(np.array(mpc["bus"], dtype=float))[:, :13]
    gen = np.atleast_2d(np.array(mpc["gen"], dtype=float))[:, :10]
    br = np.atleast_2d(np.array(mpc["branch"], dtype=float))[:, :13]

    # override line ratings (to_mpc mishandles max_i_ka mapping)
    br[:, 5], br[:, 6], br[:, 7] = RATE_A, RATE_B, RATE_C
    # repair metadata to_mpc leaves wrong: bus voltage band + generator mBase
    bus[:, 11], bus[:, 12] = VMAX, VMIN
    gen[:, 6] = BASE_MVA

    L = []
    L += header
    L.append("function mpc = case_ptx_%s" % name)
    L.append("mpc.version = '2';")
    L.append("mpc.baseMVA = %.1f;" % float(mpc["baseMVA"]))
    L.append("")
    L.append("%% bus data")
    L.append("%\tbus_i\ttype\tPd\tQd\tGs\tBs\tarea\tVm\tVa\tbaseKV\tzone\tVmax\tVmin")
    L.append("mpc.bus = [")
    bf = ["%d", "%d", "%.4f", "%.4f", "%.1f", "%.1f", "%d",
          "%.5f", "%.5f", "%.1f", "%d", "%.3f", "%.3f"]
    for r in bus:
        L.append(fmt_row(r, bf))
    L.append("];")
    L.append("")
    L.append("%% generator data")
    L.append("%\tbus\tPg\tQg\tQmax\tQmin\tVg\tmBase\tstatus\tPmax\tPmin")
    L.append("mpc.gen = [")
    gf = ["%d", "%.4f", "%.4f", "%.2f", "%.2f", "%.4f", "%.1f", "%d", "%.2f", "%.2f"]
    for r in gen:
        L.append(fmt_row(r, gf))
    L.append("];")
    L.append("")
    L.append("%% branch data")
    L.append("%\tfbus\ttbus\tr\tx\tb\trateA\trateB\trateC\tratio\tangle\tstatus\tangmin\tangmax")
    L.append("mpc.branch = [")
    cf = ["%d", "%d", "%.6f", "%.6f", "%.6f", "%.1f", "%.1f", "%.1f",
          "%.4f", "%.4f", "%d", "%.1f", "%.1f"]
    for (f, t), r in zip(LINES, br):
        L.append(fmt_row(r, cf) + "\t%% %s-%s  %.1f km" % (f, t, lengths[(f, t)]))
    L.append("];")
    L.append("")
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = here
    while root != os.path.dirname(root) and not os.path.exists(
            os.path.join(root, "pyproject.toml")):
        root = os.path.dirname(root)
    outdir = os.path.join(root, "data", "networks", "ptx")
    resdir = os.path.join(outdir, "results")
    os.makedirs(resdir, exist_ok=True)

    Zb = V_BASE_KV ** 2 / BASE_MVA
    print("Base: %.0f kV, %.0f MVA  (Z_base=%.0f ohm)  line rating %.0f MVA = %.3f kA"
          % (V_BASE_KV, BASE_MVA, Zb, RATE_A, MAX_I_KA))
    print("Loads: A=%.1f MW (Q %.1f)  B=%.1f MW (Q %.1f)   P net=%+.0f MW\n"
          % (A_PD, A_PD * Q_OVER_P, B_PD, B_PD * Q_OVER_P, P_NET_INJ))

    for name, pc in SCENARIOS.items():
        cf = COMP_FRACTION if name in COMP_SCENARIOS else 0.0
        net, coords, lengths, comp_mvar = build_net(pc, comp_fraction=cf)
        # 1. solve -> ground truth
        try:
            pp.runpp(net, init="flat", max_iteration=50)
            conv = net.converged
        except Exception as e:
            conv = False
            err = str(e).splitlines()[0][:60]

        if conv:
            vmin, vmax = net.res_bus.vm_pu.min(), net.res_bus.vm_pu.max()
            load_pct = net.res_line.loading_percent.max()
            slack_p = net.res_ext_grid.p_mw.iloc[0]
            loss = net.res_line.pl_mw.sum()
            net.res_bus.to_csv(os.path.join(resdir, "res_bus_%s.csv" % name))
            net.res_line.to_csv(os.path.join(resdir, "res_line_%s.csv" % name))
            status = ("OK   Vm[%.3f,%.3f]  maxLoad %5.0f%%  slack %+6.0f MW  loss %5.0f MW"
                      % (vmin, vmax, load_pct, slack_p, loss))
        else:
            status = "DID NOT CONVERGE  (%s)" % (err if "err" in dir() else "n/a")

        # 2-4. convert + serialise (export even if PF diverged, for inspection)
        mpc = to_mpc(net)["mpc"]
        header = [
            "%% MATPOWER case -- Danish PtX siting demo, scenario %s" % name.upper(),
            "%% Generated by scripts/build_ptx_cases.py via pandapower to_mpc.",
            "%% Buses: 1=A(load) 2=B(load) 3=C(slack/ext-grid) 4=G(gas,PV) 5=P(PtX)",
            "%% Coords[km]: " + ", ".join("%s=(%g,%g)" % (k, *coords[k])
                                          for k in ["A", "B", "C", "G", "P"]),
            "%% P net = %g MW solar - %g MW electrolysis = %+g MW (neg. load)"
            % (P_SOLAR_MW, P_ELYS_MW, P_NET_INJ),
            "%% Power flow: " + status,
        ]
        if comp_mvar > 0:
            header.insert(-1, "%% Shunt reactor at P: %.0f MVAr (charging compensation)"
                          % comp_mvar)
        path = os.path.join(outdir, "case_ptx_%s.m" % name)
        write_m(mpc, path, name, coords, lengths, header)
        tag = "  [P-reactor %.0f MVAr]" % comp_mvar if comp_mvar > 0 else ""
        print("%s  P=(%g,%g)  %s%s" % (name, pc[0], pc[1], status, tag))


if __name__ == "__main__":
    main()
