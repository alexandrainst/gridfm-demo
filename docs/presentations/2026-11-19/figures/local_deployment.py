"""Diagram of the demo as it runs today: Docker containers on one machine."""

import sys
from pathlib import Path

from drawing import (
    ACCENT,
    BLUE,
    CLIENT_TINT,
    DARK,
    DOCKER_BLUE,
    GRAY,
    SERVER_TINT,
    TITLE_SIZE,
    arrow,
    box,
    labelled_box,
    logo,
    new_figure,
    tab_title,
    text,
)

output = Path(sys.argv[1])
figure, axis = new_figure()

WIDTH = 3.6
LEFT_X, LINK_X, RIGHT_X = 0.7, 5.0, 9.7
LEFT, LINK, RIGHT = (x + WIDTH / 2 for x in (LEFT_X, LINK_X, RIGHT_X))
TOP_Y, SERVER_ROW, NODE_ROW, APP_ROW, DATA_Y = 10.55, 7.3, 4.75, 2.3, 0.3
NODE_HEIGHT, APP_HEIGHT, SERVER_HEIGHT = 1.2, 1.4, 1.2

# The machine and the Docker network that the containers share.
box(axis, 0.1, 0.1, 13.8, 11.7, GRAY, dashed=True, zorder=0)
tab_title(axis, 0.5, 11.8, "Local Machine", GRAY)
box(axis, 0.25, 1.85, 13.5, 8.05, DOCKER_BLUE, dashed=True, zorder=0)
logo(axis, "docker", 0.6, 9.15, 0.5)
text(axis, 1.8, 9.4, "Docker", size=TITLE_SIZE, color=DOCKER_BLUE, align="left")

# The server and the clients each get a tinted group.
box(axis, 4.75, 6.9, 8.8, 2.25, DARK, fill=SERVER_TINT, zorder=0)
tab_title(axis, 7.7, 9.15, "Server", DARK)
for x, client in ((0.45, 1), (9.45, 2)):
    box(axis, x, 2.05, 4.1, 4.35, BLUE, fill=CLIENT_TINT, zorder=0)
    if client == 1:
        tab_title(axis, x + 0.3, 6.4, "Client 1", BLUE)
    else:
        tab_title(axis, x + 3.8, 6.4, "Client 2", BLUE, align="right")

# The results, on the machine and outside the containers.
labelled_box(axis, RIGHT_X, TOP_Y, WIDTH, 0.9, color=ACCENT, title="Model output")
for x, client in ((LEFT_X, 1), (RIGHT_X, 2)):
    labelled_box(axis, x, DATA_Y, WIDTH, 0.9, color=ACCENT, title=f"Client {client} data")

# The containers.
labelled_box(
    axis, LINK_X, SERVER_ROW, WIDTH, SERVER_HEIGHT, color=DARK, title="SuperLink",
    lines=("relays messages",), logos={0: ("flower-mark",)},
)
labelled_box(
    axis, RIGHT_X, SERVER_ROW, WIDTH, SERVER_HEIGHT, color=DARK, title="ServerApp",
    lines=("averages models",),
)
for x, client in ((LEFT_X, 1), (RIGHT_X, 2)):
    labelled_box(
        axis, x, NODE_ROW, WIDTH, NODE_HEIGHT, color=BLUE, title=f"SuperNode {client}",
        lines=(f"for client {client}",), logos={1: ("flower-mark",)},
    )
    labelled_box(
        axis, x, APP_ROW, WIDTH, APP_HEIGHT, color=BLUE, title=f"ClientApp {client}",
        lines=("training",), logos={1: ("nvidia", "pytorch")},
    )

# What passes between them.
middle = SERVER_ROW + SERVER_HEIGHT / 2
arrow(axis, (LINK_X + WIDTH + 0.15, middle), (RIGHT_X - 0.15, middle), DARK, both=True)
arrow(axis, (RIGHT, SERVER_ROW + SERVER_HEIGHT + 0.1), (RIGHT, TOP_Y - 0.1), ACCENT)
text(axis, RIGHT - 0.3, 10.2, "metrics, model", align="right")
for node in (LEFT, RIGHT):
    # The SuperLink to each SuperNode, and each SuperNode to its ClientApp.
    sign = -1 if node == LEFT else 1
    arrow(axis, (LINK + sign * 0.9, SERVER_ROW - 0.1),
          (node + sign * -1.0, NODE_ROW + NODE_HEIGHT + 0.1), DARK,
          both=True)
    arrow(axis, (node, NODE_ROW - 0.1), (node, APP_ROW + APP_HEIGHT + 0.1), BLUE,
          both=True)
    arrow(axis, (node, DATA_Y + 0.9 + 0.1), (node, APP_ROW - 0.1), ACCENT)
text(axis, LINK, 5.6, "model weights", color=DARK)
text(axis, LINK, 5.1, "validation loss", color=DARK)
text(axis, LEFT + 0.3, 1.55, "own data only", align="left")
text(axis, RIGHT - 0.3, 1.55, "own data only", align="right")

figure.tight_layout()
figure.savefig(output, dpi=130, transparent=True)
print(output, output.stat().st_size)
