"""Diagram of the containers on HPC: a server and any number of clients."""

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
figure, axis = new_figure(height=12.9)

# The server, with its three parts side by side.
SERVER_Y, SERVER_TOP = 10.8, 12.65
box(axis, 0.1, SERVER_Y, 13.8, SERVER_TOP - SERVER_Y, DARK, fill=SERVER_TINT, zorder=0)
tab_title(axis, 0.5, SERVER_TOP, "Server", DARK)
INNER_Y, INNER_WIDTH, INNER_HEIGHT = 11.1, 3.5, 1.2
LINK_X, APP_X = 3.2, 7.9
labelled_box(
    axis, LINK_X, INNER_Y, INNER_WIDTH, INNER_HEIGHT, color=DARK, title="SuperLink",
    lines=("relays messages",), logos={0: ("flower-mark",)},
)
labelled_box(
    axis, APP_X, INNER_Y, INNER_WIDTH + 0.3, INNER_HEIGHT, color=DARK,
    title="ServerApp", lines=("averages models",),
)
middle = INNER_Y + INNER_HEIGHT / 2
arrow(axis, (LINK_X + INNER_WIDTH + 0.12, middle), (APP_X - 0.12, middle), DARK,
      both=True)

# Clients 1 and 2, dots, and client M. Each client is one HPC site.
CLIENT_Y, CLIENT_TOP, CLIENT_WIDTH = 0.25, 8.9, 3.8
NODE_Y, APP_Y, STORAGE_Y, CPU_Y = 7.2, 4.9, 2.8, 0.6
NODE_HEIGHT, APP_HEIGHT, SMALL_HEIGHT = 1.2, 1.4, 1.2
CLIENTS = ((0.2, "1"), (4.4, "2"), (10.0, "$M$"))
for x, name in CLIENTS:
    inner_x, inner_width = x + 0.2, CLIENT_WIDTH - 0.4
    box(axis, x, CLIENT_Y, CLIENT_WIDTH, CLIENT_TOP - CLIENT_Y, BLUE,
        fill=CLIENT_TINT, zorder=0)
    tab_title(axis, x + 0.3, CLIENT_TOP, f"Client {name} (HPC)", BLUE)
    labelled_box(
        axis, inner_x, NODE_Y, inner_width, NODE_HEIGHT, color=BLUE,
        title=f"SuperNode {name}", lines=("connects",), logos={1: ("flower-mark",)},
    )
    labelled_box(
        axis, inner_x, APP_Y, inner_width, APP_HEIGHT, color=BLUE,
        title=f"ClientApp {name}", lines=("trains",),
        logos={1: ("nvidia", "pytorch")},
    )
    labelled_box(
        axis, inner_x, STORAGE_Y, inner_width, SMALL_HEIGHT, color=ACCENT,
        title="Data", lines=("stays here",),
    )
    labelled_box(
        axis, inner_x, CPU_Y, inner_width, SMALL_HEIGHT, color=BLUE,
        title="CPU nodes", lines=("make the data",),
    )
    centre = inner_x + inner_width / 2
    arrow(axis, (centre, NODE_Y - 0.1), (centre, APP_Y + APP_HEIGHT + 0.1), BLUE,
          both=True)
    arrow(axis, (centre, STORAGE_Y + SMALL_HEIGHT + 0.1), (centre, APP_Y - 0.1), ACCENT)
    arrow(axis, (centre, CPU_Y + SMALL_HEIGHT + 0.1), (centre, STORAGE_Y - 0.1), ACCENT)
    # Each client connects out to the server, which sits above it.
    link_x = x + CLIENT_WIDTH - 0.5
    arrow(axis, (link_x, CLIENT_TOP + 0.1), (link_x, SERVER_Y - 0.1), BLUE, both=True)
    if name == "1":
        text(axis, link_x + 0.3, 10.4, "encrypted,", align="left", color=DARK)
        text(axis, link_x + 0.3, 10.0, "model updates only", align="left", color=DARK)

# The dots between client 2 and client M.
for offset in (0.4, 0.0, -0.4):
    axis.scatter([9.0], [4.6 + offset], s=60, color=DARK, zorder=4)

figure.tight_layout()
figure.savefig(output, dpi=130, transparent=True)
print(output, output.stat().st_size)
