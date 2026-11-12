"""Presentation-grade field maps for the pitch deck (run from repo root or deck/)."""
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from qshield.instance import make_instance  # noqa: E402
from qshield.classical import exact, greedy_infestation  # noqa: E402

GOLD, VIOLET, INK = "#D9A21B", "#6929C4", "#1B1F1D"
inst = make_instance(n=12, K=4, seed=6)
plans = {"map_greedy.png": (greedy_infestation(inst)["x"], GOLD),
         "map_qshield.png": (exact(inst)["x"], VIOLET)}
W = inst.spread_matrix()
P = inst.xy.copy()                       # display positions (schematic): separate the F5/F11 pair slightly
P[inst.names.index("F11")] += [-0.08, 0.0]
P[inst.names.index("F5")] += [0.08, 0.0]
wmax = W.max()
cmap = matplotlib.colormaps["YlOrRd"]

for fname, (x, ring) in plans.items():
    fig, ax = plt.subplots(figsize=(5.6, 5.0))
    for i in range(inst.n):
        for j in range(i + 1, inst.n):
            if W[i, j] > 0.05 * wmax:
                ax.plot(*P[[i, j]].T, color="#9AA19D", lw=0.6 + 5.0 * W[i, j] / wmax,
                        alpha=0.55, zorder=1, solid_capstyle="round")
    for i in range(inst.n):
        r = 0.075 + 0.04 * inst.area[i] / inst.area.max()
        if x[i]:
            ax.add_patch(plt.Circle(P[i], r + 0.045, color=ring, zorder=2))
            ax.add_patch(plt.Circle(P[i], r + 0.018, color="white", zorder=2.5))
        ax.add_patch(plt.Circle(P[i], r, color=cmap(0.15 + 1.2 * inst.infest[i]), zorder=3,
                                ec="#5C625F", lw=0.6))
        ax.text(*P[i], inst.names[i], ha="center", va="center", fontsize=9,
                weight="bold", color=INK if inst.infest[i] < 0.42 else "white", zorder=4)
    ax.set_xlim(-0.25, 2.75); ax.set_ylim(0.05, 2.75)
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(os.path.join(HERE, fname), dpi=220, bbox_inches="tight", transparent=True, pad_inches=0.02)
    plt.close(fig)

# horizontal infestation legend strip
fig, ax = plt.subplots(figsize=(3.2, 0.32))
grad = np.linspace(0.05, 0.65, 256)[None, :]
ax.imshow(cmap(0.15 + 1.2 * grad), aspect="auto", extent=[0.05, 0.65, 0, 1])
ax.set_yticks([]); ax.set_xticks([])
for s in ax.spines.values():
    s.set_visible(False)
fig.savefig(os.path.join(HERE, "legend_infestation.png"), dpi=220, bbox_inches="tight", transparent=True)
print("ok", [inst.names[i] for i in np.flatnonzero(greedy_infestation(inst)["x"])],
      [inst.names[i] for i in np.flatnonzero(exact(inst)["x"])])
