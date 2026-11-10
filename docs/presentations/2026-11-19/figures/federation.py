"""Diagram of federated learning: clients keep their data and share only models."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

output = Path(sys.argv[1])
DARK, BLUE, ACCENT = "#002A3F", "#0E495F", "#BE5D2B"
# Text and arrow greys reach a contrast of at least 4.5:1 against white.
TEXT, ARROW_GRAY = "#4A565E", "#6F747A"
# At the width of the figure on the slide, 22 pt is about 30 px and 26 pt about 35 px.
BODY_SIZE, TITLE_SIZE = 22, 26
LINE_SPACING = 0.6

figure, axis = plt.subplots(figsize=(11, 7.07))
axis.set_xlim(0, 14)
axis.set_ylim(0.2, 9.2)
axis.set_axis_off()


def box(x: float, y: float, width: float, height: float, color: str):
    """Draw a rounded box."""
    axis.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.05,rounding_size=0.2",
            facecolor="white",
            edgecolor=color,
            linewidth=3,
        )
    )


def arrow(start: tuple[float, float], end: tuple[float, float], color: str):
    """Draw an arrow between two points."""
    axis.add_patch(
        FancyArrowPatch(
            start, end, arrowstyle="-|>", mutation_scale=28, linewidth=3, color=color
        )
    )


def centred_text(x: float, y: float, lines: list[str], size: int, color: str):
    """Draw lines of text, evenly spaced and centred on the point (x, y)."""
    for index, line in enumerate(lines):
        offset = (len(lines) - 1) / 2 - index
        axis.text(
            x, y + offset * LINE_SPACING, line, ha="center", va="center",
            fontsize=size, color=color,
        )


CLIENT_X, CLIENT_WIDTH, CLIENT_HEIGHT = 0.3, 3.8, 2.0
SERVER_X, SERVER_Y, SERVER_WIDTH, SERVER_HEIGHT = 8.1, 0.6, 5.8, 8.0
# The arrows leave and arrive 0.15 from the boxes, which have a padding of 0.05.
LEFT, RIGHT = CLIENT_X + CLIENT_WIDTH + 0.2, SERVER_X - 0.2
# Mathtext sets the variable N in italics.
CLIENT_BOTTOMS = {"Client 1": 6.6, "Client 2": 4.3, "Client $N$": 0.6}
for index, (name, bottom) in enumerate(CLIENT_BOTTOMS.items()):
    box(CLIENT_X, bottom, CLIENT_WIDTH, CLIENT_HEIGHT, BLUE)
    middle = bottom + CLIENT_HEIGHT / 2
    centre_x = CLIENT_X + CLIENT_WIDTH / 2
    axis.text(
        centre_x, middle + 0.35, name, ha="center", va="center",
        fontsize=TITLE_SIZE, color=DARK,
    )
    axis.text(
        centre_x, middle - 0.35, "data stays here", ha="center", va="center",
        fontsize=BODY_SIZE, color=TEXT,
    )
    # Two lanes per client: the model and the validation loss go up, the global
    # model comes back.
    arrow((LEFT, middle + 0.55), (RIGHT, middle + 0.55), BLUE)
    arrow((RIGHT, middle - 0.55), (LEFT, middle - 0.55), ARROW_GRAY)
    if index == 0:
        # Only the first client is labelled, the others repeat the same pattern.
        centre = (LEFT + RIGHT) / 2
        centred_text(
            centre, middle + 1.2, ["model update", "+ validation loss"],
            size=BODY_SIZE, color=DARK,
        )
        centred_text(
            centre, middle - 0.1, ["global model"], size=BODY_SIZE, color=TEXT
        )

# The dots sit midway between Client 2 and Client N.
dots_middle = (CLIENT_BOTTOMS["Client 2"] + CLIENT_BOTTOMS["Client $N$"] + CLIENT_HEIGHT) / 2
for offset in (0.35, 0.0, -0.35):
    axis.add_patch(
        Circle((CLIENT_X + CLIENT_WIDTH / 2, dots_middle + offset), 0.06, color=DARK)
    )

box(SERVER_X, SERVER_Y, SERVER_WIDTH, SERVER_HEIGHT, DARK)
server_middle = SERVER_X + SERVER_WIDTH / 2
# The stop rule sits in its own box, since it ends the whole training.
STOP_Y, STOP_HEIGHT = 1.0, 2.4
box(SERVER_X + 0.25, STOP_Y, SERVER_WIDTH - 0.5, STOP_HEIGHT, ACCENT)
centred_text(
    server_middle,
    STOP_Y + STOP_HEIGHT / 2,
    ["stops after $M$ rounds", "without improvement", "keeps the best model"],
    size=BODY_SIZE,
    color=TEXT,
)
# The rest of the server text is centred in the space above the stop rule. Both
# server functions use the body size, and the stop rule uses the same size.
top_middle = (STOP_Y + STOP_HEIGHT + SERVER_Y + SERVER_HEIGHT) / 2
axis.text(
    server_middle, top_middle + 1.95, "Server", ha="center", va="center",
    fontsize=TITLE_SIZE, color=DARK,
)
centred_text(
    server_middle,
    top_middle + 0.45,
    ["averages the models,", "weighted by the number", "of training examples"],
    size=BODY_SIZE,
    color=TEXT,
)
centred_text(
    server_middle,
    top_middle - 1.45,
    ["tracks validation loss"],
    size=BODY_SIZE,
    color=TEXT,
)
figure.tight_layout()
figure.savefig(output, dpi=130, transparent=True)
print(output, output.stat().st_size)
