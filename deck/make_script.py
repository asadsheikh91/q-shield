"""Regenerates PITCH_SCRIPT.md from the speaker notes in Q-SHIELD_Pitch.pptx (run from repo root)."""
from pptx import Presentation

p = Presentation("Q-SHIELD_Pitch.pptx")
titles = ["Title", "The problem", "The insight", "Formulation", "Quantum circuit", "Results", "Robustness",
          "Honest limits", "Close"]
WPM = 150
rows, total, t = [], 0, 0.0
for i, (sl, name) in enumerate(zip(p.slides, titles), 1):
    note = sl.notes_slide.notes_text_frame.text.strip()
    w = len(note.split())
    secs = w / WPM * 60 + 1.5          # +1.5 s per slide change
    rows.append((i, name, t, t + secs, note))
    t += secs
    total += w


def mmss(x):
    return f"{int(x // 60)}:{int(x % 60):02d}"


out = ["# Q-SHIELD: 3-minute video script", "",
       f"This is the same text as the speaker notes in `Q-SHIELD_Pitch.pptx`: {total} words, about **{mmss(t)}** at "
       f"{WPM} words per minute.", "",
       "**How to record:** open the deck in PowerPoint, then go to Slide Show → Record → *Record from Beginning*. "
       "Read the notes (they appear in the teleprompter view) and press → to advance. Afterwards use File → Export → "
       "Create a Video (1080p), and check that it runs under 3:00. Upload it to Google Drive and set sharing to "
       "*Anyone with the link → Viewer*.", "",
       "| # | Slide | Time | Say |", "|---|---|---|---|"]
out += [f"| {i} | {name} | {mmss(a)}–{mmss(b)} | {note} |" for i, name, a, b, note in rows]
out += ["", "**Delivery tips:** pause for a beat on slide 3 so the two maps can sink in. Point your cursor at F9, "
        "then at F4. On slide 6 let the tall violet bar do the talking. Say slide 8 calmly and with confidence: "
        "judges reward honesty.",
        "", "**Likely judge questions:**",
        "- *Why not just use a classical solver?* At this size you should, and we do: it's our referee. The "
        "contribution is a correct, constraint-native quantum formulation of a real decision. It scales with the "
        "hardware, and we measure where it breaks.",
        "- *Why the XY mixer instead of a penalty?* A penalty wastes 28% of shots and needs a tuned weight. The XY "
        "mixer conserves the spray budget exactly, so every shot is a valid plan.",
        "- *Why CVaR?* A spray officer acts on one plan, the best sample, not on the average. CVaR rewards putting "
        "probability on the very best plans: 12% vs 5% optimal per shot here.",
        "- *Where does the spread model come from?* A distance-decay dispersal kernel biased downwind, calibrated "
        "from moth flight-mill studies. The next step is fitting it to FAO FAMEWS trap data."]
open("PITCH_SCRIPT.md", "w", encoding="utf8").write("\n".join(out) + "\n")
print(total, "words,", mmss(t))
