"""Draw scenario 0 of the three grids as node-link diagrams."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

root = Path(sys.argv[1])
output = Path(sys.argv[2])
GRIDS = [
    ("Client 1", "federations/case500_2clients/data/client_0/case500_goc", "#0E495F"),
    ("Client 2", "federations/case500_2clients/data/client_1/case588_sdet", "#BE5D2B"),
    ("Test grid", "federations/case300_1client/data/client_0/case300_ieee", "#002A3F"),
]
figure, axes = plt.subplots(1, 3, figsize=(18, 6.2))
for axis, (name, path, color) in zip(axes, GRIDS, strict=True):
    branches = pd.read_parquet(root / path / "raw" / "branch_data.parquet")
    first = branches[(branches["scenario"] == 0) & (branches["br_status"] == 1)]
    graph = nx.Graph(zip(first["from_bus"], first["to_bus"], strict=True))
    position = nx.spring_layout(graph, seed=1, k=0.15, iterations=200)
    nx.draw_networkx_edges(graph, position, ax=axis, edge_color="#95989C", width=0.8)
    nx.draw_networkx_nodes(graph, position, ax=axis, node_size=14, node_color=color)
    axis.set_title(f"{name}: {graph.number_of_nodes()} nodes", fontsize=24, color="#002A3F")
    axis.set_axis_off()
figure.tight_layout()
figure.savefig(output, dpi=130, transparent=True)
print(output, output.stat().st_size)
