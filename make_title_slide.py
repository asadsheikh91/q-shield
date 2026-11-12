"""Title card for the video pitch -> results/title_slide.png"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
fig = plt.figure(figsize=(16, 9), facecolor="#161616")
fig.text(0.07, 0.80, "QISKIT FALL FEST 2026  ·  AGRICULTURE", color="#A6C8FF", fontsize=18, weight="bold")
fig.text(0.07, 0.60, "Q-SHIELD", color="white", fontsize=84, weight="bold")
fig.text(0.07, 0.50, "Which fields do you spray when you can't spray them all?", color="#F4F4F4", fontsize=28)
fig.text(0.07, 0.40, "Network-aware Fall Armyworm containment with a constraint-preserving QAOA\n"
         "(Dicke state + XY mixer, CVaR training) in Qiskit", color="#C6C6C6", fontsize=19, linespacing=1.5)
fig.text(0.07, 0.12, "12 fields = 12 qubits   ·   100% feasible shots   ·   certified against exact search",
         color="#BE95FF", fontsize=17)
fig.savefig(os.path.join(OUT, "title_slide.png"), facecolor=fig.get_facecolor(), dpi=120)
print("saved")
