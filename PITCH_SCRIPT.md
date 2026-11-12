# Q-SHIELD: 3-minute video script

This is the same text as the speaker notes in `Q-SHIELD_Pitch.pptx`: 269 words, about **2:17** at 130 words per minute.

**How to record:** open the deck in PowerPoint, then go to Slide Show → Record → *Record from Beginning*. Read the notes (they appear in the teleprompter view) and press → to advance. Afterwards use File → Export → Create a Video (1080p), and check that it runs under 3:00. Upload it to Google Drive and set sharing to *Anyone with the link → Viewer*.

| # | Slide | Time | Say |
|---|---|---|---|
| 1 | Title | 0:00–0:09 | Q-SHIELD. One question, every outbreak season: which fields do you spray when you cannot spray them all? |
| 2 | The problem | 0:09–0:29 | Fall Armyworm costs African agriculture up to 9.4 billion dollars a year. Sprays only work on young larvae. A village team can treat a few fields, in a few days. And the moths fly up to 40 kilometres a night. |
| 3 | The insight | 0:29–0:48 | Today's rule: spray the worst fields first. Our plan makes one swap. Skip F9. Treat F4, the bridge between the hotspot and the healthy fields. Same four sprays. 16 percent less loss. Proven optimal against all 495 plans. |
| 4 | Formulation | 0:48–1:03 | One qubit per field. The objective: direct loss, re-infestation between untreated neighbours, and chemical load. Re-infestation multiplies two decisions, so every spread link becomes a ZZ coupling. A natural QUBO. |
| 5 | Quantum circuit | 1:03–1:25 | The spray budget is built into the circuit. A Dicke state holds every plan with exactly K sprays. The XY mixer moves sprays; it never adds one. Every shot is a valid plan. We train on CVaR: the best twenty percent of outcomes. |
| 6 | Results | 1:25–1:41 | Textbook penalty QAOA wastes 28 percent of its shots and does no better than chance. Ours: 100 percent valid. The optimal plan in 505 of 4096 shots. 60 times better than random. |
| 7 | Robustness | 1:41–1:55 | Across 12 villages, spraying the worst first loses up to 19 percent. Our best sample is optimal in 11 of 12, and at every spray budget we tested. |
| 8 | Honest limits | 1:55–2:10 | The limits. No speed-up at 12 fields; classical search is instant. Hardware noise erodes the guarantee beyond 0.3 percent error. And the spread model still awaits field data. |
| 9 | Close | 2:10–2:17 | Q-SHIELD. A real farming decision. A constraint-native quantum formulation. Fully reproducible. Thank you. |

**Delivery tips:** pause for a beat on slide 3 so the two maps can sink in. Point your cursor at F9, then at F4. On slide 6 let the tall violet bar do the talking. Say slide 8 calmly and with confidence: judges reward honesty.

**Likely judge questions:**
- *Why not just use a classical solver?* At this size you should, and we do: it's our referee. The contribution is a correct, constraint-native quantum formulation of a real decision. It scales with the hardware, and we measure where it breaks.
- *Why the XY mixer instead of a penalty?* A penalty wastes 28% of shots and needs a tuned weight. The XY mixer conserves the spray budget exactly, so every shot is a valid plan.
- *Why CVaR?* A spray officer acts on one plan, the best sample, not on the average. CVaR rewards putting probability on the very best plans: 12% vs 5% optimal per shot here.
- *Where does the spread model come from?* A distance-decay dispersal kernel biased downwind, calibrated from moth flight-mill studies. The next step is fitting it to FAO FAMEWS trap data.
