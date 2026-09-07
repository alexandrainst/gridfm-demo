#!/usr/bin/env python3
"""
Fun demo: a 200-bus power network whose buses trace a T-Rex silhouette.

  * 1   slack bus (external grid)
  * 20  PV generators distributed around the contour
  * 3   PtX plants (one of them in the T-Rex's EYE)
  * the rest (~176) PQ consumer buses

Buses are placed by arc length around a hand-drawn outline; the eye PtX bus
sits at the eye coordinate.  Topology = contour ring + nearest-neighbour
chords (so the folds -- legs, jaw -- cross-connect into a mesh).  Solved with
pandapower, exported to a standard MATPOWER .m, and plotted.
"""

import math
import os
import warnings

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

warnings.filterwarnings("ignore")
import pandapower as pp
from pandapower.converter.matpower import to_mpc

from trex_contour import extract  # traces the real image silhouette + eye

# ---------------------------------------------------------------- config -----
N_TOTAL = 200
N_GEN = 20
N_PTX = 3
V_KV = 150.0
BASE_MVA = 100.0
R_PER_KM, X_PER_KM, C_PER_KM_NF = 0.12, 0.40, 9.0
MAX_I_KA = 0.7
UNIT_KM = 1.0  # 1 outline unit = 1 km
CHORD_MAX_KM = 14.0  # add a chord to nearest bus within this range
RNG = np.random.default_rng(0)


def build():
    # --- bus coordinates: real image contour + detected eye ----------------
    contour, eye_xy, _ = extract(n_points=N_TOTAL - 1)
    coords = np.vstack([contour, eye_xy])  # eye is the last bus
    eye_idx = N_TOTAL - 1
    n = len(coords)

    # --- assign bus roles (anchors derived from the geometry) --------------
    xs, ys = coords[:, 0], coords[:, 1]
    tail_tip = int(np.argmax(xs))  # rightmost  = tail tip
    foot = int(np.argmin(ys))  # lowest     = a foot
    slack = next(
        i
        for i in np.argsort(-ys)  # highest back, not a PtX
        if i not in {eye_idx, tail_tip, foot}
    )

    ptx = {eye_idx, tail_tip, foot}
    role = ["load"] * n
    role[slack] = "slack"
    for i in ptx:
        role[i] = "ptx"
    # 20 generators spread evenly around the contour, skipping taken buses
    taken = ptx | {slack}
    gens, i = [], 0
    for idx in np.linspace(0, N_TOTAL - 2, N_GEN, dtype=int):
        j = idx
        while j in taken or role[j] != "load":
            j = (j + 1) % (N_TOTAL - 1)
        role[j] = "gen"
        taken.add(j)
        gens.append(j)

    # --- edges: contour ring + nearest-neighbour chords --------------------
    edges = set()
    ring = N_TOTAL - 1
    for i in range(ring):
        edges.add(frozenset((i, (i + 1) % ring)))
    # eye connects to its two nearest contour buses
    d_eye = np.hypot(*(coords[:ring] - coords[eye_idx]).T)
    for j in np.argsort(d_eye)[:2]:
        edges.add(frozenset((eye_idx, int(j))))
    # one extra chord per bus to its nearest non-adjacent neighbour
    D = np.hypot(
        coords[:, 0, None] - coords[None, :, 0], coords[:, 1, None] - coords[None, :, 1]
    )
    np.fill_diagonal(D, np.inf)
    for i in range(n):
        order = np.argsort(D[i])
        for j in order[:4]:
            if frozenset((i, int(j))) in edges:
                continue
            if D[i, j] * UNIT_KM <= CHORD_MAX_KM:
                edges.add(frozenset((i, int(j))))
            break

    # --- pandapower net ----------------------------------------------------
    net = pp.create_empty_network(sn_mva=BASE_MVA, f_hz=50.0)
    bus = [
        pp.create_bus(net, vn_kv=V_KV, max_vm_pu=1.1, min_vm_pu=0.9, name=str(i))
        for i in range(n)
    ]

    loads = [i for i in range(n) if role[i] == "load"]
    p_load = RNG.uniform(3.0, 12.0, len(loads))
    for i, p in zip(loads, p_load):
        pp.create_load(net, bus[i], p_mw=float(p), q_mvar=float(p) * 0.33)
    total_load = float(p_load.sum())

    pp.create_ext_grid(
        net,
        bus[slack],
        vm_pu=1.02,
        va_degree=0.0,
        max_p_mw=9999,
        min_p_mw=-9999,
        max_q_mvar=9999,
        min_q_mvar=-9999,
    )
    pg = 0.75 * total_load / N_GEN
    for i in gens:
        pp.create_gen(
            net,
            bus[i],
            p_mw=pg,
            vm_pu=1.01,
            max_q_mvar=0.6 * pg,
            min_q_mvar=-0.6 * pg,
            max_p_mw=1.5 * pg,
            min_p_mw=0.0,
        )
    for i in ptx:  # net injection (neg load)
        pp.create_load(net, bus[i], p_mw=-30.0, q_mvar=0.0)

    for e in edges:
        a, b = tuple(e)
        L = max(D[a, b] * UNIT_KM, 0.3)
        pp.create_line_from_parameters(
            net,
            bus[a],
            bus[b],
            length_km=float(L),
            r_ohm_per_km=R_PER_KM,
            x_ohm_per_km=X_PER_KM,
            c_nf_per_km=C_PER_KM_NF,
            max_i_ka=MAX_I_KA,
        )

    # --- solve -------------------------------------------------------------
    try:
        pp.runpp(net, init="flat", max_iteration=50)
        conv = net.converged
    except Exception as ex:
        conv = False
        print("solve error:", str(ex).splitlines()[0])

    info = dict(
        coords=coords,
        role=role,
        edges=edges,
        eye=eye_idx,
        slack=slack,
        gens=gens,
        ptx=ptx,
        n=n,
        total_load=total_load,
        conv=conv,
        net=net,
    )
    if conv:
        info["vmin"] = net.res_bus.vm_pu.min()
        info["vmax"] = net.res_bus.vm_pu.max()
        info["maxload"] = net.res_line.loading_percent.max()
        info["slack_p"] = net.res_ext_grid.p_mw.iloc[0]
        info["loss"] = net.res_line.pl_mw.sum()
    return net, info


STYLE = {
    "slack": ("s", "#C44E52", "Slack (ext. grid)"),
    "gen": ("^", "#55A868", "PV generator (20)"),
    "load": ("o", "#4C72B0", "PQ consumer"),
    "ptx": ("D", "#9467BD", "PtX plant (3)"),
}


def plot(info, outpng):
    coords, role, edges = info["coords"], info["role"], info["edges"]
    fig, ax = plt.subplots(figsize=(13, 11))

    for e in edges:
        a, b = tuple(e)
        ax.plot(
            coords[[a, b], 0], coords[[a, b], 1], "-", color="0.7", lw=0.8, zorder=1
        )

    for kind, (m, c, _) in STYLE.items():
        idx = [i for i in range(info["n"]) if role[i] == kind]
        if idx:
            ax.scatter(
                coords[idx, 0],
                coords[idx, 1],
                marker=m,
                c=c,
                s=70,
                edgecolors="black",
                linewidths=0.6,
                zorder=3,
            )

    # highlight the eye PtX
    ex, ey = coords[info["eye"]]
    ax.scatter(
        [ex],
        [ey],
        marker="D",
        s=260,
        facecolors="none",
        edgecolors="#9467BD",
        linewidths=2.0,
        zorder=4,
    )
    ax.annotate(
        "PtX in the eye",
        (ex, ey),
        xytext=(ex - 24, ey + 9),
        fontsize=10,
        color="#6a3da5",
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#6a3da5"),
    )

    if info["conv"]:
        sub = (
            "converged | Vm[%.3f, %.3f] | max line %.0f%% | slack %+.0f MW | "
            "loss %.0f MW | load %.0f MW"
            % (
                info["vmin"],
                info["vmax"],
                info["maxload"],
                info["slack_p"],
                info["loss"],
                info["total_load"],
            )
        )
    else:
        sub = "DID NOT CONVERGE"
    ax.set_title(
        "Jurassic Grid — 200-bus T-Rex network\n" + sub, fontsize=13, fontweight="bold"
    )
    ax.set_aspect("equal")
    ax.axis("off")
    handles = [
        Line2D(
            [0],
            [0],
            marker=m,
            color="w",
            markerfacecolor=c,
            markeredgecolor="black",
            markersize=11,
            label=lab,
        )
        for (m, c, lab) in STYLE.values()
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=10, frameon=True)
    fig.tight_layout()
    fig.savefig(outpng, dpi=120, bbox_inches="tight")
    print("wrote", outpng)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = here
    while root != os.path.dirname(root) and not os.path.exists(
        os.path.join(root, "pyproject.toml")
    ):
        root = os.path.dirname(root)
    outdir = os.path.join(root, "data", "networks", "trex")
    os.makedirs(outdir, exist_ok=True)

    net, info = build()
    print(
        "buses=%d edges=%d gens=%d ptx=%d slack=1  conv=%s"
        % (
            info["n"],
            len(info["edges"]),
            len(info["gens"]),
            len(info["ptx"]),
            info["conv"],
        )
    )
    if info["conv"]:
        print(
            "Vm[%.3f, %.3f]  maxLoad %.0f%%  slack %+.0f MW  loss %.0f MW  load %.0f MW"
            % (
                info["vmin"],
                info["vmax"],
                info["maxload"],
                info["slack_p"],
                info["loss"],
                info["total_load"],
            )
        )

    # export standard MATPOWER .m (reuse the to_mpc dict, write minimal text)
    mpc = to_mpc(net)["mpc"]
    np.set_printoptions(suppress=True)
    plot(info, os.path.join(outdir, "trex_grid.png"))
    # also dump the mpc as .mat-free .m via savetxt-style for completeness
    from pandapower.converter import to_mpc as _t

    _t(net, filename=os.path.join(outdir, "case_trex.mat"))
    print("wrote", os.path.join(outdir, "case_trex.mat"))


if __name__ == "__main__":
    main()
