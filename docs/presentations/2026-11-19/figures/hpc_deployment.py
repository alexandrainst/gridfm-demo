"""Diagram of the demo on HPC: one site per client and a server that coordinates."""

import sys
from pathlib import Path

from drawing import (
    ACCENT,
    BLUE,
    CLIENT_TINT,
    DARK,
    SERVER_TINT,
    arrow,
    box,
    labelled_box,
    new_figure,
    tab_title,
    text,
)

output = Path(sys.argv[1])
figure, axis = new_figure()

# The server, with its three parts side by side.
SERVER_Y, SERVER_TOP = 9.0, 11.2
box(axis, 0.1, SERVER_Y, 13.8, SERVER_TOP - SERVER_Y, DARK, fill=SERVER_TINT, zorder=0)
tab_title(axis, 0.5, SERVER_TOP, "Server", DARK)
INNER_Y, INNER_WIDTH, INNER_HEIGHT = 9.4, 3.5, 1.4
CLI_X, LINK_X, APP_X = 0.7, 5.15, 9.6
labelled_box(
    axis, CLI_X, INNER_Y, INNER_WIDTH, INNER_HEIGHT, color=DARK, title="gridfm CLI",
    lines=("starts a run",),
)
labelled_box(
    axis, LINK_X, INNER_Y, INNER_WIDTH, INNER_HEIGHT, color=DARK, title="SuperLink",
    lines=("relays messages",), logos={0: ("flower-mark",)},
)
labelled_box(
    axis, APP_X, INNER_Y, INNER_WIDTH + 0.3, INNER_HEIGHT, color=DARK,
    title="ServerApp", lines=("averages models",),
)
middle = INNER_Y + INNER_HEIGHT / 2
arrow(axis, (CLI_X + INNER_WIDTH + 0.12, middle), (LINK_X - 0.12, middle), DARK)
arrow(axis, (LINK_X + INNER_WIDTH + 0.12, middle), (APP_X - 0.12, middle), DARK,
      both=True)

# One client per HPC site, with three parts from the top to the bottom.
SITE_Y, SITE_TOP, SITE_WIDTH, SITE_GAP = 0.15, 7.5, 4.2, 0.4
GPU_Y, GPU_HEIGHT = 4.4, 2.5
STORAGE_Y, CPU_Y, SMALL_HEIGHT = 2.35, 0.35, 1.35
for index, name in enumerate(("1", "2", "$N$")):
    x = 0.25 + index * (SITE_WIDTH + SITE_GAP)
    inner_x, inner_width = x + 0.2, SITE_WIDTH - 0.4
    box(axis, x, SITE_Y, SITE_WIDTH, SITE_TOP - SITE_Y, BLUE, fill=CLIENT_TINT,
        zorder=0)
    tab_title(axis, x + 0.3, SITE_TOP, f"Client {name} (HPC)", BLUE)
    labelled_box(
        axis, inner_x, GPU_Y, inner_width, GPU_HEIGHT, color=BLUE, title="GPU nodes",
        lines=("SuperNode", "ClientApp", "Slurm, Apptainer"),
        logos={0: ("nvidia",), 1: ("flower-mark",), 2: ("pytorch",)},
    )
    labelled_box(
        axis, inner_x, STORAGE_Y, inner_width, SMALL_HEIGHT, color=ACCENT,
        title="Storage", lines=("data stays here",),
    )
    labelled_box(
        axis, inner_x, CPU_Y, inner_width, SMALL_HEIGHT, color=BLUE, title="CPU nodes",
        lines=("make the data",),
    )
    centre = inner_x + inner_width / 2
    arrow(axis, (centre, CPU_Y + SMALL_HEIGHT + 0.1), (centre, STORAGE_Y - 0.1), ACCENT)
    arrow(axis, (centre, STORAGE_Y + SMALL_HEIGHT + 0.1), (centre, GPU_Y - 0.1), ACCENT)
    # The client connects to the server, which sits above it.
    link_x = x + SITE_WIDTH - 0.5
    arrow(axis, (link_x, SITE_TOP + 0.1), (link_x, SERVER_Y - 0.1), BLUE, both=True)
    if index == 0:
        text(axis, link_x + 0.3, 8.6, "encrypted,", align="left", color=DARK)
        text(axis, link_x + 0.3, 8.1, "model updates only", align="left", color=DARK)

figure.tight_layout()
figure.savefig(output, dpi=130, transparent=True)
print(output, output.stat().st_size)
