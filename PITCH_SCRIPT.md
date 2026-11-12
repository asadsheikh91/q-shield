# Q-SHIELD: 3-minute video script

This is the same text as the speaker notes in `Q-SHIELD_Pitch.pptx`: 380 words, about **2:45** at 150 words per minute.

**How to record:** open the deck in PowerPoint, then go to Slide Show → Record → *Record from Beginning*. Read the notes (they appear in the teleprompter view) and press → to advance. Afterwards use File → Export → Create a Video (1080p), and check that it runs under 3:00. Upload it to Google Drive and set sharing to *Anyone with the link → Viewer*.

| # | Slide | Time | Say |
|---|---|---|---|
| 1 | Title | 0:00–0:11 | This is Q-SHIELD. It answers a question farmer cooperatives face every outbreak season: which fields do you spray when you can't spray them all? |
| 2 | The problem | 0:11–0:32 | The pest is Fall Armyworm, costing African agriculture up to 9.4 billion dollars a year. Sprays only work on young larvae, so a village team gets a few days and a handful of fields. And the moths fly 20 to 40 kilometres a night, so fields keep re-infesting each other. |
| 3 | The insight | 0:32–0:55 | Today's rule is: spray the worst fields first. The grey lines are re-infestation risk. Our plan makes one swap: skip F9, on the edge of the outbreak, and treat F4, the bridge between the hotspot and the healthy fields. Same four sprays, 16 percent less expected loss, certified against all 495 possible plans. |
| 4 | Formulation | 0:55–1:13 | One qubit per field. We minimise direct loss, plus spread between untreated neighbours, plus chemical load. The spread term multiplies two decisions, so each spread link becomes a ZZ coupling: a natural QUBO. The budget, exactly K sprays, is a hard constraint. |
| 5 | Quantum circuit | 1:13–1:39 | So we build the constraint into the circuit. We start in a Dicke state: every plan with exactly K sprays, in superposition. Each layer applies the cost, then an XY mixer that only moves a spray between fields, so every shot is valid. We train on CVaR, the best twenty percent of outcomes, because a farmer needs one excellent plan. |
| 6 | Results | 1:39–1:58 | On Qiskit Aer, textbook penalty QAOA wastes 28 percent of its shots on impossible plans and finds the optimum no better than chance. Ours is 100 percent feasible, and the optimal plan comes out in 505 of 4096 shots: 60 times more often than random. |
| 7 | Robustness | 1:58–2:15 | Across 12 random villages, spraying the worst first loses 7.6 percent more on average, up to 19, and our best sample is exactly optimal in 11 of 12. And across spray budgets, QAOA matched the exact optimum every time. |
| 8 | Honest limits | 2:15–2:35 | Honestly: at 12 fields classical search is instant, so we claim no speed-up. Hardware noise breaks the feasibility guarantee. With post-selection the signal survives up to 0.3 percent error, and it's gone by 1 percent. The spread model is literature-calibrated, not yet fitted to field data. |
| 9 | Close | 2:35–2:45 | Q-SHIELD: a real farming decision, a constraint-native quantum formulation, fully reproducible in Qiskit. Code and report are on GitHub. Thank you. |

**Delivery tips:** pause for a beat on slide 3 so the two maps can sink in. Point your cursor at F9, then at F4. On slide 6 let the tall violet bar do the talking. Say slide 8 calmly and with confidence: judges reward honesty.

**Likely judge questions:**
- *Why not just use a classical solver?* At this size you should, and we do: it's our referee. The contribution is a correct, constraint-native quantum formulation of a real decision. It scales with the hardware, and we measure where it breaks.
- *Why the XY mixer instead of a penalty?* A penalty wastes 28% of shots and needs a tuned weight. The XY mixer conserves the spray budget exactly, so every shot is a valid plan.
- *Why CVaR?* A spray officer acts on one plan, the best sample, not on the average. CVaR rewards putting probability on the very best plans: 12% vs 5% optimal per shot here.
- *Where does the spread model come from?* A distance-decay dispersal kernel biased downwind, calibrated from moth flight-mill studies. The next step is fitting it to FAO FAMEWS trap data.
