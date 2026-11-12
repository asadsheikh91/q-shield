"""Builds Q-SHIELD_Report.docx from results/summary.json + figures (run after run_demo.py)."""
import json
import os
import sys
from math import comb

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches

ROOT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ROOT, "results")
S = json.load(open(os.path.join(RES, "summary.json"), encoding="utf-8"))
REPO = sys.argv[1] if len(sys.argv) > 1 else "<GitHub repository link>"
VIDEO = sys.argv[2] if len(sys.argv) > 2 else "<3-minute video link>"
PURPLE = RGBColor(0x69, 0x29, 0xC4)

doc = Document()
st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(10.5)
for s_name, size in [("Heading 1", 15), ("Heading 2", 12.5), ("Heading 3", 11)]:
    doc.styles[s_name].font.color.rgb = PURPLE
    doc.styles[s_name].font.size = Pt(size)
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Inches(0.9)
sec.top_margin = sec.bottom_margin = Inches(0.8)


def para(text, bold=False, italic=False, size=None, align=None, space_after=6):
    p = doc.add_paragraph()
    _runs(p, text, bold, italic, size)
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p


def _runs(p, text, bold=False, italic=False, size=None):
    """**bold** inline markup."""
    parts = text.split("**")
    for k, part in enumerate(parts):
        r = p.add_run(part)
        r.bold = bold or (k % 2 == 1)
        r.italic = italic
        if size:
            r.font.size = Pt(size)


def bullets(items, style="List Bullet"):
    for it in items:
        p = doc.add_paragraph(style=style)
        _runs(p, it)
        p.paragraph_format.space_after = Pt(2)


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def table(header, rows, widths=None, fs=9):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(fs)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(c, "6929C4")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(fs)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def fig(name, caption, width=6.6):
    path = os.path.join(RES, name)
    if not os.path.exists(path):
        return
    doc.add_picture(path, width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = para(caption, italic=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    return p


inst = S["instance"]
n, K = inst["n"], inst["K"]
ex = S["classical"]["exact"]
g1 = S["classical"]["greedy_most_infested"]
xy = S["qaoa_xy"]
pen = S["qaoa_penalty"]
cv = S.get("qaoa_xy_cvar", [])
qs = S["qaoa_sampled"]
bstats = S.get("benchmark_stats", {})
best_xy = max(xy + cv, key=lambda h: h["p_optimal"])
gap = 100 * (g1["cost"] / ex["cost"] - 1)
loss_saved = g1["expected_loss_usd"] - ex["expected_loss_usd"]

# ----------------------------------------------------------------------------- title
para("Qiskit Fall Fest 2026 Hackathon  ·  Domain 4: Agriculture", size=10, italic=True,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
t = para("Q-SHIELD", bold=True, size=28, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
t.runs[0].font.color.rgb = PURPLE
para("Quantum-assisted, network-aware containment of Fall Armyworm outbreaks "
     "with a constraint-preserving QAOA", size=13, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
para(f"Code: {REPO}\nVideo: {VIDEO}", size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

doc.add_heading("Executive summary", level=1)
para("When Fall Armyworm (FAW) breaks out in a cluster of smallholder maize fields, a village spray team can "
     "only treat a few fields inside the short window in which young larvae are still controllable. "
     "Today the default rule is “spray the worst fields first”. That rule ignores the fact that moths from "
     "untreated fields re-infest their neighbours, so the fields that matter most are often the ones that sit "
     "between hotspots and healthy crops.")
para(f"We formulate the choice of which **K** of **n** fields to treat as a constrained quadratic binary "
     f"optimisation problem (QUBO) whose quadratic terms come directly from field-to-field re-infestation risk. "
     f"We solve it with a **Quantum Alternating Operator Ansatz** in Qiskit that starts in a **Dicke state** "
     f"(every plan that treats exactly K fields) and uses an **XY mixer** that never leaves the feasible set. "
     f"On a {n}-field / {n}-qubit test village with K = {K}:")
bullets([
    f"The exact optimum (certified by enumerating all {comb(n, K)} feasible plans) cuts expected cost by "
    f"**{gap:.1f}%** versus spray-most-infested, i.e. **≈ USD {loss_saved:,.0f}** of maize saved in one control "
    f"window for the same spray effort.",
    f"Our XY-QAOA returns the certified optimum as its best sample; 100% of shots are feasible plans, and the "
    f"optimal plan is sampled **{best_xy['amplification']:.1f}×** more often than by uniform sampling of feasible plans "
    f"(p = {best_xy['p']}, {qs.get('objective', 'mean-energy')} objective).",
    f"The textbook penalty-QAOA on the same problem reaches only {max(h['p_feasible'] for h in pen) * 100:.0f}% feasible shots "
    f"and an approximation ratio of ≈ {pen[-1]['approx_ratio']:.2f} (≈ random), which is why the constraint-preserving design matters.",
    "We are explicit about limits: at 12 qubits classical exact search is instant, and noisy-hardware simulation "
    "shows the amplification survives ~0.1–0.3% two-qubit error only with post-selection and vanishes by 1%. The contribution is a correct, "
    "honest, reproducible quantum formulation of a real agronomic decision, not a speed-up claim.",
])

# ----------------------------------------------------------------------------- 1 problem
doc.add_heading("1. The problem and who it serves", level=1)
para("Fall Armyworm (Spodoptera frugiperda) is an invasive moth from the Americas that reached Africa in 2016 and "
     "spread to more than a dozen Asian countries, including India and China, by 2019. CABI estimates maize losses "
     "of USD 1–4.6 billion per year across 12 African countries (2018), rising to USD 9.4 billion per year for "
     "African agriculture overall (2021 study). Farmers in Ghana and Zambia reported average maize losses of 26.6% "
     "and 35%. FAO's Global Action for Fall Armyworm Control (65 target countries) explicitly calls for "
     "coordinated, area-wide management, because adult moths fly 20–40 km per night and fields re-infest each other.")
para("**The decision.** In a village or cooperative cluster, scouts report infestation levels (pheromone-trap "
     "counts, % of plants with fresh damage). An extension officer or cooperative has **one spray team / drone** "
     f"that can treat only **K** fields before larvae reach late instars, when control efficacy collapses. "
     "Which K fields should be treated now?")
para("**Who it serves.** Extension officers, farmer cooperatives and national FAW task forces making area-wide "
     "decisions for smallholders, who farm most of the maize in affected regions on less than two hectares.")
para("**Competing objectives.** (i) minimise expected crop loss, both direct loss and re-infestation of neighbours; "
     "(ii) minimise chemical load (cost, farmer health, pollinators and insecticide-resistance pressure). "
     "We expose the trade-off as a Pareto front over spray capacity K and a weight λ.")

# ----------------------------------------------------------------------------- 2 formulation
doc.add_heading("2. Formulation", level=1)
doc.add_heading("2.1 Variables, objective, constraint", level=2)
bullets([
    "**Decision variables:** x_i ∈ {0,1}; x_i = 1 if field i is treated in this control window (one qubit per field).",
    "**Direct loss:** D_i = V_i · p_i · δ, with crop value V_i, scouted infestation probability p_i and yield-loss "
    "fraction δ = 0.30 (consistent with the 26–35% farmer-reported losses).",
    "**Re-infestation risk:** S_ij = p_i · β_ij · (1 − p_j) · V_j · δ is the expected loss caused in field j by moths "
    "from field i, and W_ij = S_ij + S_ji. It counts only when both fields are untreated, which gives the term "
    "(1 − x_i)(1 − x_j). Spread probability: β_ij = β0 · exp(−d_ij / L) · (1 + 0.6 cos(θ_ij − θ_wind)), "
    "a distance-decay dispersal kernel biased downwind.",
    "**Objective:** minimise f(x) = Σ_i D_i (1 − x_i) + Σ_{i<j} W_ij (1 − x_i)(1 − x_j) + λ Σ_i E_i x_i.",
    "**Constraint:** Σ_i x_i = K (spray-team capacity in the 72-hour early-instar window).",
])
para("Expanding (1 − x_i)(1 − x_j) gives a QUBO with linear terms h_i = −D_i − Σ_j W_ij + λE_i and couplings "
     "J_ij = W_ij. The quadratic structure is not added for convenience: it is the epidemiology. Treating one "
     "field protects its neighbours, so the value of treating a field depends on which other fields are treated.")
doc.add_heading("2.2 Test instance", level=2)
para(f"A synthetic, literature-calibrated village of n = {n} maize fields on a 2.5 × 2.5 km area (seed {inst['seed']}): "
     "areas 0.4–2.0 ha, yield 3 t/ha at USD 260/t, infestation clustered around an outbreak hotspot, wind from "
     f"{inst['meta']['wind_deg']}°, dispersal length L = {inst['meta']['L_km']} km, β0 = {inst['meta']['beta0']}, "
     f"K = {K}. Search space: {2 ** n} bitstrings, {comb(n, K)} feasible plans.")
rows = [[f["name"], f"{f['x_km']:.2f}, {f['y_km']:.2f}", f["area_ha"], f["infestation"], f"{f['value_usd']:.0f}",
         f["chem_load"]] for f in inst["fields"]]
table(["Field", "Position (km)", "Area (ha)", "Infestation p_i", "Value (USD)", "Chem. load E_i"], rows,
      widths=[0.7, 1.3, 0.9, 1.2, 1.0, 1.1])

# ----------------------------------------------------------------------------- 3 algorithm
doc.add_heading("3. Quantum algorithm and why we chose it", level=1)
para("**Mapping.** Substituting x_i = (1 − Z_i)/2 turns f(x) into an Ising Hamiltonian "
     "H_C = Σ a_i Z_i + Σ b_ij Z_i Z_j, whose ground state within the K-excitation subspace is the optimal spray "
     "plan. Each qubit is one field; each ZZ coupling is one re-infestation link.")
para("**Why QAOA, and why this variant.** QAOA is the natural variational algorithm for QUBO and Ising problems on "
     "gate-based hardware. However, the standard version (|+⟩ start, X mixer, constraint as penalty "
     "A(Σx − K)²) spends most of its amplitude on infeasible plans and must balance A against the objective. "
     "We instead use the **Quantum Alternating Operator Ansatz** (Hadfield et al. 2019):")
bullets([
    "**Initial state: Dicke state |D(n,K)⟩**, an equal superposition of all C(n,K) feasible plans, prepared "
    "deterministically with the Bärtschi–Eidenbenz split-and-cyclic-shift circuit (O(nK) gates, implemented "
    "from scratch and unit-tested).",
    "**Cost unitary exp(−iγH_C):** RZ gates (linear terms) and RZZ gates (re-infestation couplings).",
    "**XY ring mixer exp(−iβ Σ (X_iX_{i+1} + Y_iY_{i+1})/2):** it swaps “treated” between neighbouring fields and "
    "commutes with Σ Z_i, so the Hamming weight, i.e. the spray budget, is conserved exactly. Every shot is "
    "feasible by construction, and no penalty weight needs tuning.",
    "**Classical outer loop:** COBYLA minimises ⟨H_C⟩. The p = 1 angles are seeded by a grid search over (γ, β), "
    "and deeper circuits are warm-started with the INTERP heuristic (Zhou et al. 2020).",
    "**Extension: CVaR objective.** A spray officer needs one good plan, not a good average. We therefore also "
    "optimise CVaR_0.2, the mean cost of the best 20% of the output distribution (Barkoutsos et al. 2020). "
    "This rewards circuits that put a large probability on the very best plans.",
])
para("**What the quantum part does.** The quantum circuit is the solver. The classical optimiser only tunes 2p "
     "angles; the spray plan returned to the user is a measured bitstring from the circuit. Classical exact "
     "search is used purely as a referee.")

doc.add_heading("4. Architecture", level=1)
fig("architecture.png", "Figure 1. Q-SHIELD architecture: field data → risk network → constrained QUBO → "
    "Dicke-initialised XY-QAOA in Qiskit (COBYLA loop) → sampled spray plan, validated against exact search.",
    width=6.7)

# ----------------------------------------------------------------------------- 5 implementation
doc.add_heading("5. Implementation", level=1)
bullets([
    "qshield/instance.py: instance generator, objective, QUBO and Ising conversion, cost of all 2^n bitstrings.",
    "qshield/quantum.py: Dicke-state circuit, cost layer, XY ring mixer, penalty-QAOA baseline, "
    "statevector optimiser (Qiskit quantum_info.Statevector), and shot-based execution on Qiskit Aer "
    "(ideal and depolarising-noise models).",
    "qshield/classical.py: exact enumeration, spray-most-infested rule, marginal greedy, simulated annealing.",
    "run_demo.py: end-to-end reproducible pipeline that writes results/summary.json and every figure in this report. "
    "tests/test_core.py checks Dicke uniformity, QUBO correctness, feasibility preservation and exactness.",
    f"Environment: Python 3.12, Qiskit 2.x, Qiskit Aer 0.18. Full run ≈ {S['runtime_s'] / 60:.0f} min on a laptop CPU.",
])

# ----------------------------------------------------------------------------- 6 results
doc.add_heading("6. Results", level=1)
doc.add_heading("6.1 Quantum vs classical/exact on the test village", level=2)
cl = S["classical"]
rows = [
    ["Exact enumeration (reference)", cl["exact"]["plan"], f"{cl['exact']['cost']:.1f}", "0.0%", "certified optimum"],
    ["Spray most infested (current practice)", cl["greedy_most_infested"]["plan"],
     f"{cl['greedy_most_infested']['cost']:.1f}", f"+{gap:.1f}%", "ignores spread"],
    ["Marginal greedy", cl["greedy_marginal"]["plan"], f"{cl['greedy_marginal']['cost']:.1f}",
     f"+{100 * (cl['greedy_marginal']['cost'] / ex['cost'] - 1):.1f}%", "classical heuristic"],
    ["Simulated annealing", cl["simulated_annealing"]["plan"], f"{cl['simulated_annealing']['cost']:.1f}",
     f"+{100 * (cl['simulated_annealing']['cost'] / ex['cost'] - 1):.1f}%", "classical heuristic"],
    [f"Q-SHIELD XY-QAOA ({qs.get('objective', '')}, p={qs['p']}, 4096 shots, Aer)", qs["best_plan"], f"{qs['best_cost']:.1f}",
     f"+{100 * (qs['best_cost'] / ex['cost'] - 1):.1f}%",
     f"optimum sampled {qs['optimal_shots']}×; {qs['feasible_shots']}/4096 feasible"],
]
table(["Method", "Fields treated", "Cost f(x)", "Gap", "Note"], rows, widths=[1.9, 1.4, 0.8, 0.6, 1.9])
para(f"Expected loss: optimum USD {ex['expected_loss_usd']:,.0f} (direct {ex['direct_loss_usd']:,.0f} + spread "
     f"{ex['spread_loss_usd']:,.0f}) vs spray-most-infested USD {g1['expected_loss_usd']:,.0f} (direct "
     f"{g1['direct_loss_usd']:,.0f} + spread {g1['spread_loss_usd']:,.0f}). The optimal plan accepts slightly more "
     f"direct loss in exchange for a much larger cut in re-infestation. This is the network effect that a "
     f"field-by-field rule cannot see.")
fig("fig_map.png", "Figure 2. Test village. Node colour = infestation, size = area, edge width = re-infestation "
    "risk; blue rings = treated fields. Left: current practice. Right: QAOA plan (= exact optimum).")

doc.add_heading("6.2 Constraint-preserving vs penalty QAOA", level=2)
rows = []
for a, b in zip(xy, pen):
    rows.append([a["p"], f"{a['approx_ratio']:.3f}", f"{a['p_feasible']:.3f}", f"{a['p_optimal']:.4f}",
                 f"{a['amplification']:.1f}×", a["cx_count"],
                 f"{b['approx_ratio']:.3f}", f"{b['p_feasible']:.3f}", f"{b['p_optimal']:.4f}", b["cx_count"]])
table(["p", "XY approx.", "XY feasible", "XY P(opt)", "XY vs uniform", "XY CX",
       "Pen. approx.", "Pen. feasible", "Pen. P(opt)", "Pen. CX"], rows, fs=8)
para("Approximation ratio = (worst feasible − ⟨cost⟩_feasible)/(worst − optimum): 1 means optimal and 0.5 is "
     "roughly what a random feasible plan scores. P(opt) is the probability that a single shot returns the "
     f"certified optimum; for uniform sampling of feasible plans it is {xy[0]['p_optimal_uniform_feasible']:.4f}. "
     "CX = two-qubit gate count after transpiling to {rz, sx, x, cx}, including Dicke preparation.")
if cv:
    table(["p", "CVaR approx.", "CVaR feasible", "CVaR P(opt)", "CVaR vs uniform"],
          [[h["p"], f"{h['approx_ratio']:.3f}", f"{h['p_feasible']:.3f}", f"{h['p_optimal']:.4f}",
            f"{h['amplification']:.1f}×"] for h in cv], fs=8.5)
    para("CVaR training usually scores a lower average (approximation ratio) but puts more probability on the optimum. "
         "That is the right trade-off for a decision tool that returns the best sampled plan. Because the optimiser "
         "targets the expectation or the CVaR rather than P(opt) directly, P(opt) does not rise monotonically with p.")
fig("fig_qaoa_layers.png", "Figure 3. XY-QAOA with mean-energy (purple) and CVaR (blue) objectives vs penalty QAOA "
    "(red) as circuit depth p grows.")
fig("fig_distribution.png", "Figure 4. Output distribution over all feasible plans, ranked by true cost. QAOA "
    "moves probability from the uniform Dicke start towards the best plans.", width=6.2)
fig("fig_landscape.png", "Figure 5. p = 1 energy landscape used to seed the optimiser.", width=3.8)

doc.add_heading("6.3 Trade-off: crop loss vs chemical load", level=2)
para("Sweeping the spray capacity K gives the Pareto front a cooperative actually needs: how much crop each extra "
     "treated field saves, and at what chemical cost. QAOA with CVaR training (circles) was run for K = 2…6, with "
     "Hilbert-space sizes of 66 to 924 feasible plans, and its best sample matched the exact optimum for every K.")
fig("fig_pareto.png", "Figure 6. Expected loss vs chemical load for K = 1…11: exact optimum, spray-most-infested "
    "rule, and QAOA best samples.", width=5.6)
pq = [f for f in S["pareto"] if "q_matches_exact" in f]
if pq:
    table(["K", "Exact loss (USD)", "Greedy gap", "QAOA matches exact", "QAOA P(opt)", "vs uniform"],
          [[f["K"], f"{f['loss']:,.0f}", f"+{f['greedy_gap_pct']:.1f}%", "yes" if f["q_matches_exact"] else "no",
            f"{f['q_p_opt']:.3f}", f"{f['q_amplification']:.1f}×"] for f in pq])

if "benchmark" in S:
    doc.add_heading("6.4 Robustness over 12 random villages", level=2)
    b = bstats
    para(f"To avoid reporting a single lucky instance, we repeated the pipeline on 12 random villages (n = {n}, "
         f"K = {K}). Spray-most-infested was on average **{b['greedy_gap_pct']['mean']:.1f}%** worse than the optimum "
         f"(range {b['greedy_gap_pct']['min']:.1f}–{b['greedy_gap_pct']['max']:.1f}%). XY-QAOA at p = 3 reached a mean "
         f"approximation ratio of **{b['qaoa_p3_approx']['mean']:.3f}** (range {b['qaoa_p3_approx']['min']:.3f}–"
         f"{b['qaoa_p3_approx']['max']:.3f}) and amplified the optimal plan by **{b['qaoa_p3_amplification']['mean']:.1f}×** "
         f"on average; with the CVaR objective the mean amplification was **{b['cvar_p3_amplification']['mean']:.1f}×**. "
         f"The best of 1024 shots was on average {b['qaoa_best_of_1024_gap_pct']['mean']:.2f}% from the "
         f"optimum (11 of 12 villages exact). The showcase village (seed {inst['seed']}) was chosen as the most "
         f"network-sensitive of these 12; we report that choice transparently. Two honest observations: (1) on two "
         f"villages spray-most-infested is already optimal, because when hotspots are isolated the network effect "
         f"vanishes; (2) with the mean-energy objective, amplification is uneven: in village 4 the circuit concentrates "
         f"on a near-optimal plan and the optimum falls below uniform (0.05×). The CVaR objective fixes this in most "
         f"villages but not all (minimum 1.5×). This is the main reason we recommend CVaR training.")
    table(["Village", "Greedy gap", "XY p=3 approx.", "XY amp.", "CVaR amp.", "Best-of-1024 gap"],
          [[x["seed"], f"+{x['greedy_gap_pct']:.1f}%", f"{x['qaoa_p3_approx']:.3f}", f"{x['qaoa_p3_amplification']:.1f}×",
            f"{x['cvar_p3_amplification']:.1f}×", f"{x['qaoa_best_of_1024_gap_pct']:.2f}%"] for x in S["benchmark"]], fs=8.5)
    fig("fig_benchmark.png", "Figure 7. Per-village greedy gap (left) and XY-QAOA approximation ratio (right).")

doc.add_heading("6.5 Sensitivity to hardware noise", level=2)
nz = S["noise"]
table(["Circuit", "2-qubit error", "P(optimal) per shot", "P(feasible)", "P(optimal | feasible)"],
      [[r["circuit"], f"{r['noise']:.3f}", f"{r['p_opt']:.4f}", f"{r['p_feasible']:.3f}",
        f"{r['p_opt_postselected']:.4f}"] for r in nz])
best_noise = [r for r in nz if r["circuit"].startswith("best")]
nz_txt = "; ".join(f"{r['noise'] * 100:.1f}% → P(opt|feasible) = {r['p_opt_postselected']:.3f} "
                   f"({r['p_opt_postselected'] / r['uniform']:.0f}× uniform), feasible {r['p_feasible'] * 100:.0f}%"
                   for r in best_noise)
para("We ran the best circuit through Aer with depolarising noise (1-qubit error = 2-qubit error / 10, plus "
     "readout error of half the 2-qubit rate). Feasibility is no longer guaranteed: the XY mixer conserves "
     "Hamming weight only in the noiseless limit, and the CX-heavy Dicke preparation and the dense cost layer "
     "(66 couplings) accumulate errors. Discarding shots with Σx ≠ K (post-selection) is cheap and recovers part "
     f"of the signal: {nz_txt}. In short, the amplification survives at today's best two-qubit error rates "
     "(~0.1–0.3%) only with post-selection, and it is gone by 1%. Probabilities near 10⁻³ are shot-noise limited "
     "(2048 shots, about 2 counts), so the small rise for the p = 1 circuit at 1% error is not significant.")
fig("fig_noise.png", "Figure 8. Left: probability of the optimal plan (solid) and after post-selecting feasible shots "
    "(dotted). Right: fraction of feasible shots vs two-qubit depolarising error.", width=6.6)

# ----------------------------------------------------------------------------- 7 limitations
doc.add_heading("7. Limitations: what did not work, and what we assume", level=1)
bullets([
    "**No quantum advantage, and none claimed.** At 12 fields, exact enumeration of 495 plans takes milliseconds, "
    "and marginal greedy and simulated annealing also find the optimum on this instance. Our quantum results show "
    "that the formulation is correct and that the ansatz concentrates probability on good plans; they do not "
    "show speed-up.",
    "**Modest, uneven amplification.** The probability of the optimum per shot rises well above uniform (best: 12%, "
    "60×), but it varies a lot between villages and depths (Section 6.4). With 4096 shots even uniform sampling of feasible plans would probably hit the optimum "
    "once. The meaningful metrics are therefore approximation ratio and amplification, not “found the optimum”.",
    "**Scaling.** Statevector optimisation is exponential in n (we stop at 12–14 qubits). Real districts with "
    "hundreds of fields would need decomposition by village, warm-started or recursive QAOA, or hardware runs "
    "with CVaR objectives. Barren-plateau and parameter-transfer behaviour at scale remain untested.",
    "**Circuit cost.** Dicke preparation needs multi-controlled RY gates (hundreds of CX after transpilation), and "
    "the dense spread graph gives all-to-all RZZ, which costs SWAPs on heavy-hex hardware. Sparsifying weak links "
    "(W_ij below a threshold) and using a cheaper W-state-like initial mix are natural next steps.",
    "**Noise breaks the feasibility guarantee** (Section 6.5): the elegant constraint handling holds only "
    "for noiseless or error-mitigated execution.",
    "**Model assumptions.** One-step spread over a single control window; independent infestation probabilities; "
    "treatment assumed fully effective; synthetic but literature-calibrated parameters (β0, L, δ) that are not "
    "fitted to field data. Multi-week dynamics, partial efficacy, resistance and farmer adoption are not "
    "modelled. A real deployment would calibrate β with trap-network data.",
    "**Ring XY mixer** mixes slowly between distant fields; a complete-graph XY mixer mixes faster but doubles the "
    "two-qubit cost. We did not explore that trade-off fully in the time available.",
])

doc.add_heading("8. Future work", level=1)
bullets([
    "Calibrate the dispersal kernel with FAO FAMEWS trap and scouting data, then run on IBM Heron hardware with "
    "error mitigation and post-selection.",
    "Multi-period version (which fields this week, which next week) with time-indexed qubits.",
    "Add equity constraints so that no farmer is repeatedly left untreated, using a third objective term.",
])

doc.add_heading("References", level=1)
bullets([
    "CABI (2017, 2018), Fall Armyworm: Impacts and Implications for Africa (evidence notes); CABI (2021) estimate of "
    "USD 9.4 bn per year losses to African agriculture.",
    "FAO (2020), Global Action for Fall Armyworm Control: Action framework 2020–2022 (65 target countries).",
    "Flight-mill studies of S. frugiperda: median 21–38 km per night, maximum ~70 km (reviewed in Insects 13(5):422, 2022).",
    "Hadfield, S. et al. (2019), From the Quantum Approximate Optimization Algorithm to a Quantum Alternating "
    "Operator Ansatz, Algorithms 12(2):34.",
    "Bärtschi, A. & Eidenbenz, S. (2019), Deterministic Preparation of Dicke States, FCT 2019, LNCS 11651.",
    "Farhi, E., Goldstone, J. & Gutmann, S. (2014), A Quantum Approximate Optimization Algorithm, arXiv:1411.4028.",
    "Zhou, L. et al. (2020), Quantum Approximate Optimization Algorithm: Performance, Mechanism, and Implementation "
    "on Near-Term Devices, PRX 10, 021067 (INTERP initialisation).",
    "Barkoutsos, P. et al. (2020), Improving Variational Quantum Optimization using CVaR, Quantum 4, 256.",
    "Lucas, A. (2014), Ising formulations of many NP problems, Frontiers in Physics 2:5.",
    "Qiskit SDK 2.x and Qiskit Aer (IBM Quantum).",
], style="List Number")
para("All code in the repository was written for this hackathon, with AI coding assistance (Claude). The algorithms "
     "above are cited and implemented from the papers; no tutorial or other teams' code was copied.", italic=True, size=9)

out = os.path.join(ROOT, "Q-SHIELD_Report.docx")
doc.save(out)
print("saved", out)
