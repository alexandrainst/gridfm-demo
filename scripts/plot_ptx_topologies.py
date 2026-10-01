#!/usr/bin/env python3
"""
Plot the PtX network topologies in data/networks/ptx/.

One subplot per .m case (max 3 per row).  Each subplot shows:
  * bus positions at their geographic (x, y) coordinates [km]
  * branches (lines) with their length annotated
  * bus type by colour/marker (slack / PV gen / PQ load / PtX injection)
  * input parameters per bus (loads, generation, setpoints)
  * the power-flow outcome (parsed from the file header)

Reads the coordinates from the '%% Coords[km]:' header comment that
build_ptx_cases.py writes, and the electrical data from the mpc matrices.
"""

import glob
import os
import re
import math

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.offsetbox import DrawingArea, AnnotationBbox

REACTOR_COL = "#8B4513"

# bus-type styling: (marker, facecolor, legend label)
STYLE = {
    "slack": ("s", "#C44E52", "Slack (ext. grid)"),
    "pv": ("^", "#55A868", "PV generator"),
    "pq": ("o", "#4C72B0", "PQ load"),
    "ptx": ("D", "#9467BD", "PtX (net injection)"),
}


def parse_case(path):
    txt = open(path).read()

    coords, order = {}, []
    cline = re.search(r"Coords\[km\]:\s*(.+)", txt).group(1)
    for nm, x, y in re.findall(r"(\w+)=\(([-\d.]+),\s*([-\d.]+)\)", cline):
        coords[nm] = (float(x), float(y))
        order.append(nm)

    status = re.search(r"Power flow:\s*(.+)", txt)
    status = status.group(1).strip() if status else ""
    base = float(re.search(r"mpc\.baseMVA\s*=\s*([\d.]+)", txt).group(1))

    def matrix(name):
        block = re.search(r"mpc\.%s\s*=\s*\[(.*?)\];" % name, txt, re.S).group(1)
        rows = []
        for ln in block.strip().splitlines():
            ln = ln.split("%")[0].strip().rstrip(";").strip()
            if ln:
                rows.append([float(v) for v in ln.split()])
        return np.array(rows)

    return dict(
        name=os.path.basename(path).replace("case_ptx_", "").replace(".m", ""),
        coords=coords,
        order=order,
        status=status,
        base=base,
        bus=matrix("bus"),
        gen=matrix("gen"),
        branch=matrix("branch"),
        kv=matrix("bus")[0, 9],
    )


def bus_style_and_label(case, bus_i, name):
    row = case["bus"][case["bus"][:, 0] == bus_i][0]
    btype, pd, qd = int(row[1]), row[2], row[3]
    grow = case["gen"][case["gen"][:, 0] == bus_i]

    if btype == 3:  # slack
        vg = grow[0, 5] if len(grow) else 1.0
        return "slack", "%s — Slack\nVg=%.2f" % (name, vg)
    if btype == 2:  # PV
        pg, vg = grow[0, 1], grow[0, 5]
        return "pv", "%s — PV gen\nPg=%.0f MW\nVg=%.2f" % (name, pg, vg)
    if pd < 0:  # PtX injection (neg load)
        return "ptx", "%s — PtX\n%+.0f MW (Q=%.0f)" % (name, -pd, -qd)
    return "pq", "%s — PQ load\nPd=%.0f MW\nQd=%.0f MVAr" % (name, pd, qd)


def add_shunt_glyph(ax, x, y, bs_mvar):
    """Draw a scale-independent shunt glyph at bus (x, y).

    bs_mvar < 0 -> reactor (coil to ground);  bs_mvar > 0 -> capacitor.
    Sized in points via DrawingArea so it is unaffected by the data scale.
    """
    col = REACTOR_COL
    da = DrawingArea(26, 36, 0, 0)
    da.add_artist(Line2D([13, 13], [36, 30], color=col, lw=1.3))  # lead into box
    if bs_mvar < 0:  # reactor coil
        t = np.linspace(0, 3 * np.pi, 60)
        da.add_artist(
            Line2D(13 + 3 * np.sin(t), 14 + t / (3 * np.pi) * 16, color=col, lw=1.3)
        )
        da.add_artist(Line2D([13, 13], [14, 10], color=col, lw=1.3))
        label = "%.0f MVAr\nreactor" % abs(bs_mvar)
    else:  # capacitor plates
        da.add_artist(Line2D([13, 13], [30, 20], color=col, lw=1.3))
        da.add_artist(Line2D([7, 19], [20, 20], color=col, lw=1.6))
        da.add_artist(Line2D([7, 19], [16, 16], color=col, lw=1.6))
        da.add_artist(Line2D([13, 13], [16, 10], color=col, lw=1.3))
        label = "%.0f MVAr\ncapacitor" % abs(bs_mvar)
    for yy, w in [(10, 7), (7.5, 4.5), (5.2, 2.2)]:  # ground symbol
        da.add_artist(Line2D([13 - w, 13 + w], [yy, yy], color=col, lw=1.3))

    ab = AnnotationBbox(
        da,
        (x, y),
        xybox=(30, -16),
        xycoords="data",
        boxcoords="offset points",
        frameon=False,
        pad=0,
        box_alignment=(0.5, 1.0),
        arrowprops=dict(arrowstyle="-", color=col, lw=1.2),
    )
    ax.add_artist(ab)
    ax.annotate(
        label,
        (x, y),
        xytext=(46, -22),
        textcoords="offset points",
        fontsize=6,
        color=col,
        va="top",
        zorder=5,
    )


def plot_case(ax, case):
    name_by_idx = {i + 1: nm for i, nm in enumerate(case["order"])}
    pos = case["coords"]

    # branches
    for r in case["branch"]:
        f, t = int(r[0]), int(r[1])
        nf, nt = name_by_idx[f], name_by_idx[t]
        (x0, y0), (x1, y1) = pos[nf], pos[nt]
        ax.plot([x0, x1], [y0, y1], "-", color="0.55", lw=1.4, zorder=1)
        L = math.hypot(x1 - x0, y1 - y0)
        ax.annotate(
            "%.0f km" % L,
            ((x0 + x1) / 2, (y0 + y1) / 2),
            fontsize=6.5,
            color="0.35",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7),
        )

    # buses
    for bus_i, nm in name_by_idx.items():
        kind, label = bus_style_and_label(case, bus_i, nm)
        marker, color, _ = STYLE[kind]
        x, y = pos[nm]
        ax.scatter(
            [x],
            [y],
            marker=marker,
            s=190,
            c=color,
            edgecolors="black",
            linewidths=1.0,
            zorder=3,
        )
        ax.annotate(
            label,
            (x, y),
            textcoords="offset points",
            xytext=(10, 10),
            fontsize=7,
            zorder=4,
            bbox=dict(
                boxstyle="round,pad=0.3", fc="white", ec=color, lw=1.2, alpha=0.95
            ),
        )
        # shunt (Bs = bus matrix column 5): draw reactor/capacitor glyph
        bs = case["bus"][case["bus"][:, 0] == bus_i][0][5]
        if abs(bs) > 1e-6:
            add_shunt_glyph(ax, x, y, bs)

    # 'auto' (not 'equal') keeps the cluster readable when P is far away;
    # true distances are preserved in the per-line km labels.
    ax.set_aspect("auto")
    ax.margins(0.28)
    ax.grid(True, ls=":", alpha=0.4)
    ax.tick_params(labelsize=7)
    ax.set_xlabel("x [km]", fontsize=7)
    ax.set_ylabel("y [km]", fontsize=7)

    ok = case["status"].startswith("OK")
    ax.set_title(
        "%s   (%.0f kV, %.0f MVA base)\n%s"
        % (case["name"].upper(), case["kv"], case["base"], case["status"]),
        fontsize=8.5,
        color="#2a6e2a" if ok else "#a01010",
    )


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ddir = os.path.normpath(os.path.join(here, "..", "data", "networks", "ptx"))
    files = sorted(glob.glob(os.path.join(ddir, "case_ptx_*.m")))
    cases = [parse_case(f) for f in files]

    n = len(cases)
    ncols = min(3, n)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(5.2 * ncols, 4.8 * nrows), squeeze=False
    )
    for ax in axes.flat[n:]:
        ax.axis("off")
    for ax, case in zip(axes.flat, cases):
        plot_case(ax, case)

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
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=4,
        fontsize=9,
        frameon=True,
        bbox_to_anchor=(0.5, -0.005),
    )
    fig.suptitle(
        "Danish PtX siting demo — network topologies (move plant P)",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))

    out = os.path.join(ddir, "ptx_topologies.png")
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print("wrote", os.path.relpath(out, here))


if __name__ == "__main__":
    main()
