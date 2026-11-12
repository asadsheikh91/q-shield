"""Draws results/architecture.png (the system architecture diagram used in the report)."""
import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)

fig, ax = plt.subplots(figsize=(15, 8.4))
ax.set_xlim(0, 150); ax.set_ylim(0, 84); ax.axis("off")

PAL = {"data": ("#E5F6FF", "#0072C3"), "model": ("#FFF8E1", "#B28600"), "q": ("#F6F2FF", "#6929C4"),
       "cl": ("#F2F4F8", "#4D5358"), "val": ("#DEFBE6", "#198038"), "out": ("#FFF0F7", "#9F1853")}


def box(x, y, w, h, title, body, kind, fs=8.6):
    fc, ec = PAL[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.6",
                                fc=fc, ec=ec, lw=1.8))
    ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="top", fontsize=fs + 1.4, weight="bold", color=ec)
    ax.text(x + w / 2, y + h - 7.0, body, ha="center", va="top", fontsize=fs, color="#161616", linespacing=1.35)


def arrow(p, q, label=None, color="#393939", rad=0.0, lx=0, ly=0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, lw=1.6, color=color,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((p[0] + q[0]) / 2 + lx, (p[1] + q[1]) / 2 + ly, label, fontsize=7.8, color=color,
                ha="center", style="italic")


def group(x, y, w, h, label, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=2.5",
                                fc="none", ec=color, lw=1.2, ls="--"))
    ax.text(x + 1.5, y + h - 1.2, label, fontsize=9, color=color, weight="bold", va="top")


ax.text(75, 82.5, "Q-SHIELD — quantum-assisted, network-aware pest containment: system architecture",
        ha="center", fontsize=14, weight="bold")

# 1 data
group(1, 4, 30, 72, "1  FIELD DATA", PAL["data"][1])
box(3, 56, 26, 15, "Scouting", "pheromone-trap counts,\n% plants with FAW damage\n→ infestation p_i", "data")
box(3, 38, 26, 15, "Field registry / GIS", "centroids, area (ha),\ncrop stage, value V_i", "data")
box(3, 20, 26, 15, "Weather + biology", "wind direction, moth\ndispersal kernel → β_ij", "data")
box(3, 6, 26, 11, "Resources", "spray-team capacity K,\nchemical load E_i", "data", fs=8.2)

# 2 model
group(34, 40, 34, 36, "2  OPTIMISATION MODEL", PAL["model"][1])
box(36, 58, 30, 14, "Risk network", "nodes = fields (direct loss D_i)\nedges = re-infestation W_ij", "model")
box(36, 42, 30, 13.5, "Constrained QUBO", "min Σ D_i(1−x_i) + Σ W_ij(1−x_i)(1−x_j)\n+ λ Σ E_i x_i    s.t.  Σ x_i = K", "model", fs=8.0)

# 3 quantum
group(71, 22, 50, 54, "3  QUANTUM CORE  (Qiskit)", PAL["q"][1])
box(73, 59, 22, 13, "Dicke state", "|D(n,K)⟩: all plans that\ntreat exactly K fields\n(Bärtschi–Eidenbenz)", "q", fs=8.0)
box(97, 59, 22, 13, "Cost layer", "e^{−iγ H_C}\nRZ + RZZ gates\n(Ising form of QUBO)", "q", fs=8.0)
box(97, 42, 22, 13.5, "XY ring mixer", "e^{−iβ(XX+YY)/2}\nconserves Σx = K\n→ 100 % feasible", "q", fs=8.0)
box(73, 42, 22, 13.5, "Measure", "Aer sampler\n(ideal + noisy)\nbitstrings = plans", "q", fs=8.0)
box(73, 24, 46, 14, "Classical outer loop", "COBYLA on ⟨H_C⟩ (statevector), p=1 grid seed,\nINTERP warm-start for p → p+1 layers", "cl")
ax.text(109.5, 57.2, "× p layers", fontsize=8, color=PAL["q"][1], weight="bold")

# 4 validation
group(124, 40, 25, 36, "4  VALIDATION", PAL["val"][1])
box(126, 58, 21, 14, "Exact", "enumerate all C(n,K)\nplans → certified\noptimum", "val", fs=8.0)
box(126, 42, 21, 13.5, "Heuristics", "spray-most-infested,\nmarginal greedy,\nsimulated annealing", "val", fs=8.0)

# 5 output
group(34, 4, 115, 15, "5  DECISION SUPPORT", PAL["out"][1])
box(36, 6, 34, 10, "Spray plan + map", "which K fields to treat now", "out", fs=8.2)
box(74, 6, 34, 10, "Pareto front", "crop loss vs chemical load per K", "out", fs=8.2)
box(112, 6, 35, 10, "Users", "extension officers, co-ops, FAW task forces", "out", fs=8.2)

# arrows
for y in (63, 45):
    arrow((31.5, y), (35.5, y + 2 if y == 63 else y + 4))
arrow((31.5, 27), (35.5, 60), rad=-0.15)
arrow((31.5, 11), (35.5, 46), rad=-0.2)
arrow((51, 57.5), (51, 56))
arrow((66.5, 48), (72.5, 64), "H_C, K", rad=-0.2, lx=-2, ly=2)
arrow((95.4, 65.5), (96.6, 65.5))
arrow((108, 58.6), (108, 56))
arrow((96.6, 48.5), (95.4, 48.5))
arrow((84, 41.6), (84, 38.4), "⟨H_C⟩", lx=4)
arrow((112, 38.4), (112, 41.6), "γ, β", lx=4)
arrow((119.5, 46), (125.5, 46), "plan", rad=0.0, lx=0, ly=1.2, color=PAL["val"][1])
arrow((84, 23.6), (60, 16.6), "decoded plan", color=PAL["out"][1], rad=0.1)
arrow((136, 41.6), (128, 16.6), "certify / compare", color=PAL["val"][1], rad=0.0, lx=7)

fig.savefig(os.path.join(OUT, "architecture.png"), bbox_inches="tight", dpi=170)
print("saved", os.path.join(OUT, "architecture.png"))
