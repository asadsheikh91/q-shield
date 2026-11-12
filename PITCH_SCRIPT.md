# Q-SHIELD: 3-minute video script (about 420 spoken words, hard stop at 2:55)

Record your screen with OBS, Loom or the Windows Game Bar (Win+Alt+R) and talk over it. Have these open in tabs:
`results/fig_map.png`, `results/architecture.png`, a terminal in the repo, `results/fig_qaoa_layers.png`, `results/fig_pareto.png`, `results/fig_noise.png`.

| Time | On screen | Say |
|---|---|---|
| 0:00–0:25 | Title slide, or the README header | "Fall Armyworm is an invasive moth that now attacks maize across Africa and Asia. CABI estimates African losses of up to 9.4 billion dollars a year. When it breaks out in a village, one spray team can treat only a few fields in the 72 hours before the larvae become uncontrollable. So: **which fields do you spray?**" |
| 0:25–0:55 | `fig_map.png`, left panel then right | "Today the rule is 'spray the worst fields'. But moths from untreated fields re-infest their neighbours; the grey edges are that risk. On the right is our plan. It skips F9 and treats F4, the bridge between the hotspot and the healthy cluster. Same spray effort, **19% lower expected cost**, and that difference is certified by exact search." |
| 0:55–1:30 | `architecture.png` | "We model it as a QUBO. Each field is a qubit, and each re-infestation link is a ZZ coupling, so the quadratic terms are the epidemiology itself. The budget 'exactly K sprays' is a hard constraint. Instead of a penalty, we start in a **Dicke state**, which is every plan with exactly K sprays in superposition, and mix with an **XY mixer** that only swaps which field is treated. Every shot is a valid plan by construction." |
| 1:30–2:00 | Terminal: `python run_demo.py --quick` (pre-run it, then show output scrolling) | "Here is the Qiskit pipeline running: exact baseline, greedy, simulated annealing, then QAOA trained on a statevector and sampled on Aer. The best QAOA sample is the certified optimum, and 100% of shots are feasible." |
| 2:00–2:25 | `fig_qaoa_layers.png` | "Against textbook penalty QAOA, ours is always feasible, while the penalty version wastes 28 to 57% of its shots on impossible plans. Our approximation ratio climbs with depth, while the penalty version stays near random. With CVaR training at four layers, the optimal plan comes out in 12% of shots, 60 times more often than uniform sampling." |
| 2:25–2:45 | `fig_pareto.png`, then `fig_noise.png` | "Sweeping the spray budget gives cooperatives a trade-off curve between crop loss and chemical load. And we're honest: at 12 fields, classical search is instant; we don't claim speed-up. Our noise study shows that hardware noise breaks the feasibility guarantee. With post-selection we still get about 16 times uniform at 0.3% error, but the signal is gone by 1%." |
| 2:45–2:55 | README / repo link | "Q-SHIELD: a real farming decision with a correct, constraint-native quantum formulation, fully reproducible in Qiskit. Thank you." |

Tips: speak a bit faster than feels natural, cut dead air when you edit, and check that the final file is **under 3:00**. Upload it to Google Drive and set it to *Anyone with the link → Viewer*.
