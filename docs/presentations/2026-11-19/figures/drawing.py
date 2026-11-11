"""Shared drawing helpers for the deployment diagrams."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

LOGOS = Path(__file__).parent.parent / "public" / "logos"
DARK, BLUE, ACCENT = "#002A3F", "#0E495F", "#BE5D2B"
DOCKER_BLUE = "#2496ED"
# Light tints that set the server and the clients apart.
SERVER_TINT, CLIENT_TINT = "#E6ECEF", "#E3F0F5"
# Text and line greys reach a contrast of at least 4.5:1 against white.
TEXT, GRAY = "#4A565E", "#6F747A"
# At the width of the figure on the slide, 20 pt is about 27 px, 24 pt about 33 px.
BODY_SIZE, TITLE_SIZE = 20, 24
WIDTH, HEIGHT = 14.0, 12.0


def new_figure(height: float = HEIGHT) -> tuple[plt.Figure, Axes]:
    """Return a figure and axis of 14 units wide and `height` units high."""
    figure, axis = plt.subplots(figsize=(11, 11 * height / WIDTH))
    axis.set_xlim(0, WIDTH)
    axis.set_ylim(0, height)
    axis.set_axis_off()
    return figure, axis


def box(
    axis: Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    color: str,
    *,
    dashed: bool = False,
    fill: str = "white",
    zorder: float = 1,
) -> None:
    """Draw a rounded box."""
    axis.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.05,rounding_size=0.2",
            facecolor=fill,
            edgecolor=color,
            linewidth=3,
            linestyle=(0, (5, 3)) if dashed else "-",
            zorder=zorder,
        )
    )


def arrow(
    axis: Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
    *,
    both: bool = False,
) -> None:
    """Draw an arrow between two points, with a head at each end if `both`."""
    axis.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="<|-|>" if both else "-|>",
            mutation_scale=28,
            linewidth=3,
            color=color,
            zorder=3,
        )
    )


def text(
    axis: Axes,
    x: float,
    y: float,
    content: str,
    *,
    size: int = BODY_SIZE,
    color: str = TEXT,
    align: str = "center",
) -> None:
    """Draw one line of text, centred vertically on y."""
    axis.text(
        x,
        y,
        content,
        ha=align,
        va="center",
        fontsize=size,
        color=color,
        zorder=4,
    )


def logo(
    axis: Axes, name: str, x: float, y: float, height: float, *, align: str = "left"
) -> float:
    """Draw a logo from `public/logos` with its lower left corner at (x, y).

    The transparent margin of the image is cut off first, so the logo fills the
    given height. With `align="right"`, x is the right edge instead.

    Returns:
        The width of the logo in axis units.
    """
    image = Image.open(LOGOS / f"{name}.png").convert("RGBA")
    image = image.crop(image.getchannel("A").getbbox())
    width = height * image.width / image.height
    left = x - width if align == "right" else x
    x_limits, y_limits = axis.get_xlim(), axis.get_ylim()
    axis.imshow(
        image,
        extent=(left, left + width, y, y + height),
        aspect="auto",
        zorder=4,
    )
    axis.set_xlim(x_limits)
    axis.set_ylim(y_limits)
    return width


def labelled_box(
    axis: Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    color: str,
    title: str,
    lines: tuple[str, ...] = (),
    logos: dict[int, tuple[str, ...]] | None = None,
) -> None:
    """Draw a box with a title and lines of text on the left, and some logos.

    The text is left aligned and centred vertically. `logos` maps a text row, where
    row 0 is the title, to the logos at the right end of that row.
    """
    box(axis, x, y, width, height, color)
    line_height = 0.5
    top = y + height / 2 + (line_height * (1 + len(lines)) + 0.1) / 2
    title_y = top - 0.3
    text(axis, x + 0.3, title_y, title, size=TITLE_SIZE, color=DARK, align="left")
    for index, line in enumerate(lines, start=1):
        text(axis, x + 0.3, title_y - index * line_height - 0.1, line, align="left")
    for row, names in (logos or {}).items():
        row_y = title_y - (row * line_height + (0.1 if row else 0))
        right = x + width - 0.25
        for name in names:
            right -= logo(axis, name, right, row_y - 0.225, 0.45, align="right") + 0.15


def tab_title(
    axis: Axes,
    x: float,
    y: float,
    content: str,
    color: str,
    *,
    fill: str = "white",
    align: str = "left",
) -> None:
    """Write a title on the top border of a box, the way a tab would."""
    axis.text(
        x, y, content, ha=align, va="center", fontsize=TITLE_SIZE, color=color,
        zorder=5, bbox={"facecolor": fill, "edgecolor": "none", "pad": 6},
    )
