"""Chart of the speed-ups that the GridFM papers report over classical solvers."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

output = Path(sys.argv[1])
# (label, speed-up shown, text, measured?)
BARS = [
    ("GENCO power flow\nvs Newton-Raphson", 30, "up to 30x", True),
    ("GENCO optimal power flow\nvs IPOPT", 81, "up to 81x", True),
    ("DynGridFM dynamics, GPU\nvs one CPU core", 1232, "924x to 1,232x", True),
    ("GridFM-v0 power flow\n(projection)", 10000, "1,000x to 10,000x", False),
]
figure, axis = plt.subplots(figsize=(14, 6.2))
labels = [bar[0] for bar in BARS][::-1]
for index, (_, value, text, measured) in enumerate(BARS[::-1]):
    axis.barh(
        index,
        value,
        color="#0E495F" if measured else "white",
        edgecolor="#0E495F",
        hatch=None if measured else "//",
        height=0.6,
    )
    axis.text(value * 1.15, index, text, va="center", fontsize=20, color="#002A3F")
axis.set_xscale("log")
axis.set_xlim(1, 500000)
axis.set_yticks(range(len(BARS)), labels, fontsize=18, color="#002A3F")
axis.set_xticks([1, 10, 100, 1000, 10000], ["1x", "10x", "100x", "1,000x", "10,000x"])
axis.tick_params(axis="x", labelsize=18, colors="#002A3F")
axis.set_xlabel("Speed-up over the classical method, log scale", fontsize=18, color="#002A3F")
for side in ("top", "right"):
    axis.spines[side].set_visible(False)
figure.tight_layout()
figure.savefig(output, dpi=130, transparent=True)
print(output, output.stat().st_size)
