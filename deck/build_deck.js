// Q-SHIELD pitch deck.  Run from repo root:  node deck/build_deck.js
// Numbers are read from results/summary.json so the deck always matches the code.
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const S = JSON.parse(fs.readFileSync(path.join(ROOT, "results", "summary.json"), "utf8"));
const SKILL_THEME = process.env.APPLY_THEME_JS;            // path to the pptx skill's apply_theme.js (optional)
const OUT = process.env.DECK_OUT || path.join(ROOT, "Q-SHIELD_Pitch.pptx");
const IMG = (f) => path.join(__dirname, f);

// ------------------------------------------------------------------ numbers
const ex = S.classical.exact, g1 = S.classical.greedy_most_infested;
const pen = S.qaoa_penalty, xy = S.qaoa_xy, cv = S.qaoa_xy_cvar, qs = S.qaoa_sampled;
const last = (a) => a[a.length - 1];
const uniformPct = 100 * xy[0].p_optimal_uniform_feasible;
const cutPct = 100 * (1 - ex.cost / g1.cost);               // optimum vs worst-first (≈16 %)
const worsePct = 100 * (g1.cost / ex.cost - 1);             // worst-first vs optimum (≈19 %)
const saved = g1.expected_loss_usd - ex.expected_loss_usd;
const bs = S.benchmark_stats;
const exactVillages = S.benchmark.filter((b) => b.qaoa_best_of_1024_gap_pct < 1e-6).length;
const noiseBest = S.noise.filter((r) => r.circuit.startsWith("best"));
const fmt = (v, d = 1) => v.toFixed(d);

// ------------------------------------------------------------------ theme
const THEME = {
  name: "Q-SHIELD",
  headFontFace: "Arial",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F1D", lt1: "FFFFFF", dk2: "0F231A", lt2: "F1F3F1",
    accent1: "6929C4",   // quantum violet  (our method)
    accent2: "D9A21B",   // maize gold      (current practice)
    accent3: "B8361E",   // pest red        (penalty / loss)
    accent4: "8A918D",   // field grey      (baselines)
    accent5: "EFE8FB",   // violet tint     (cards)
    accent6: "BE95FF",   // light violet
    hlink: "6929C4", folHlink: "4A1D8C",
  },
};
const H = THEME.colors;   // hex values for hex-only options

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.333 x 7.5 in
pres.title = "Q-SHIELD";
pres.author = "Q-SHIELD team";
pres.subject = "Qiskit Fall Fest 2026 - Agriculture";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

const M = 0.6, W = 13.333, Hh = 7.5;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "DARK",
  background: { color: H.dk2 },
  objects: [],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: H.lt1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.42, w: W - 2 * M, h: 0.85,
        fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 },
      text: "" } },
    { text: { text: "Q-SHIELD  ·  Qiskit Fall Fest 2026  ·  Agriculture",
        options: { x: M, y: Hh - 0.48, w: 6, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 } } },
  ],
  slideNumber: { x: W - M - 0.6, y: Hh - 0.48, w: 0.6, h: 0.3, fontSize: 10, color: H.accent4, align: "right" },
});

// ------------------------------------------------------------------ helpers
function text(slide, t, o) { slide.addText(t, Object.assign({ isTextBox: true, margin: 0 }, o)); }

function stat(slide, x, y, w, big, label, opt = {}) {
  text(slide, big, { x, y, w, h: opt.bigH || 0.95, fontFace: THEME.headFontFace, fontSize: opt.size || 54,
    bold: true, color: opt.color || C.accent1, valign: "bottom", objectName: "stat " + big });
  text(slide, label, { x, y: y + (opt.bigH || 0.95) + 0.08, w, h: opt.labelH || 0.75, fontSize: opt.labelSize || 15,
    color: opt.labelColor || C.text1, valign: "top" });
}

function chip(slide, x, y, d, label, fill, color) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  text(slide, label, { x, y, w: d, h: d, align: "center", valign: "middle", fontSize: d > 0.5 ? 16 : 12,
    bold: true, color });
}

function card(slide, x, y, w, h, fill, name) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill },
    line: { color: fill }, objectName: name });
}

function arrow(slide, x1, y1, x2, y2, color = H.accent4, w = 2) {
  slide.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1),
    h: Math.abs(y2 - y1), flipV: y2 < y1, line: { color, width: w, endArrowType: "triangle" } });
}

const chartBase = () => ({
  catAxisLabelColor: H.dk1, valAxisLabelColor: H.accent4, catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  legendFontFace: "+mn-lt", titleFontFace: "+mn-lt", valAxisTitleFontFace: "+mn-lt", catAxisTitleFontFace: "+mn-lt",
  valGridLine: { color: "E3E6E4", size: 0.75 }, catGridLine: { style: "none" },
  catAxisLineShow: true, valAxisLineShow: false, titleColor: H.dk1, titleFontSize: 14,
  valAxisTitleColor: H.accent4, catAxisTitleColor: H.accent4, valAxisTitleFontSize: 11, catAxisTitleFontSize: 11,
});

// ================================================================== 1. TITLE
pres.addSection({ title: "Opening" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Opening" });
s.addImage({ path: IMG("map_qshield.png"), x: 7.35, y: 0.75, w: 5.6, h: 5.0, transparency: 8,
  altText: "Network of 12 maize fields; four treated fields ringed in violet", objectName: "hero map" });
text(s, "QISKIT FALL FEST 2026  ·  AGRICULTURE", { x: M, y: 0.9, w: 7, h: 0.4, fontSize: 14, bold: true,
  color: C.accent6, charSpacing: 2 });
text(s, "Q-SHIELD", { x: M, y: 1.65, w: 7, h: 1.4, fontFace: THEME.headFontFace, fontSize: 80, bold: true,
  color: C.background1 });
text(s, "Which fields do you spray when you can't spray them all?", { x: M, y: 3.15, w: 6.6, h: 1.2,
  fontSize: 28, color: C.background1 });
text(s, "Network-aware Fall Armyworm containment with a constraint-preserving QAOA in Qiskit",
  { x: M, y: 4.55, w: 6.4, h: 0.8, fontSize: 16, color: "C9D1CC" });
text(s, "github.com/asadsheikh91/q-shield", { x: M, y: 6.55, w: 6, h: 0.35, fontSize: 13, color: "C9D1CC" });
s.addNotes(
  "Q-SHIELD. One question, every outbreak season: which fields do you spray when you cannot spray them all?");

// ================================================================== 2. PROBLEM
pres.addSection({ title: "Problem" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Problem" });
s.addText("A pest that outflies the spray team", { placeholder: "title" });
const stats2 = [
  ["$9.4B", "a year in losses to African agriculture", "CABI, 2021"],
  ["26–35%", "of maize lost on affected farms", "farmer surveys, Ghana & Zambia (CABI)"],
  ["20–40 km", "a moth can fly in one night, so fields re-infest each other", "flight-mill studies, Insects 2022"],
  ["65", "countries in FAO's Global Action, which calls for area-wide control", "FAO, 2020"],
];
const colW = (W - 2 * M - 3 * 0.4) / 4;
stats2.forEach(([big, label, src], i) => {
  const x = M + i * (colW + 0.4);
  stat(s, x, 1.55, colW, big, label, { color: i < 2 ? C.accent3 : C.text1, size: 40, labelH: 0.95 });
  text(s, src, { x, y: 3.6, w: colW, h: 0.3, fontSize: 10, italic: true, color: C.accent4 });
});
card(s, M, 4.45, W - 2 * M, 1.85, H.accent5, "decision card");
text(s, "THE DECISION", { x: M + 0.45, y: 4.75, w: 4, h: 0.35, fontSize: 13, bold: true, color: C.accent1,
  charSpacing: 2 });
text(s, [
  { text: "One village spray team can treat only ", options: {} },
  { text: "K", options: { bold: true, color: C.accent1 } },
  { text: " of ", options: {} },
  { text: "n", options: { bold: true, color: C.accent1 } },
  { text: " infested fields while the larvae are still young enough to kill. Which fields go first?", options: {} },
], { x: M + 0.45, y: 5.15, w: W - 2 * M - 0.9, h: 1.1, fontSize: 22, color: C.text1, valign: "top" });
s.addNotes(
  "Fall Armyworm costs African agriculture up to 9.4 billion dollars a year. Sprays only work on young larvae. " +
  "A village team can treat a few fields, in a few days. And the moths fly up to 40 kilometres a night.");

// ================================================================== 3. INSIGHT (MAPS)
pres.addSection({ title: "Insight" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Insight" });
s.addText("Spraying the worst fields first misses the bridge", { placeholder: "title" });
const mapW = 4.15, mapH = mapW * 5.0 / 5.6, mapY = 1.85;
[[M, "map_greedy.png", "SPRAY WORST FIRST", C.accent2, "F1 · F2 · F9 · F12", g1.expected_loss_usd],
 [M + mapW + 0.3, "map_qshield.png", "Q-SHIELD", C.accent1, "F1 · F2 · F4 · F12", ex.expected_loss_usd]]
  .forEach(([x, f, label, col, plan, loss]) => {
    text(s, label, { x, y: 1.4, w: mapW, h: 0.35, fontSize: 14, bold: true, color: col, charSpacing: 2 });
    s.addImage({ path: IMG(f), x, y: mapY, w: mapW, h: mapH, altText: label + " plan: " + plan });
    text(s, [
      { text: "Expected loss  ", options: { color: C.accent4 } },
      { text: "$" + Math.round(loss), options: { bold: true, color: col } },
    ], { x, y: mapY + mapH + 0.08, w: mapW, h: 0.4, fontSize: 16 });
  });
const rx = M + 2 * mapW + 0.85, rw = W - M - rx;
stat(s, rx, 1.5, rw, "−" + fmt(cutPct, 0) + "%", "expected loss, with the same four sprays", { size: 60, bigH: 1.05 });
text(s, [
  { text: "One swap: ", options: { bold: true } },
  { text: "skip F9 on the outbreak's edge, and treat F4, the bridge between the hotspot and the healthy fields to the east.", options: {} },
], { x: rx, y: 3.55, w: rw, h: 1.5, fontSize: 15, color: C.text1, valign: "top" });
text(s, "≈ $" + Math.round(saved) + " of maize saved in one 12-field village, per outbreak window. " +
  "Certified optimal by checking all 495 possible plans.",
  { x: rx, y: 5.15, w: rw, h: 1.0, fontSize: 13, color: C.accent4, valign: "top" });
s.addImage({ path: IMG("legend_infestation.png"), x: M, y: 6.55, w: 2.0, h: 0.2 });
text(s, "low → high scouted infestation  ·  line width = re-infestation risk", { x: M + 2.15, y: 6.5, w: 6.0, h: 0.3,
  fontSize: 10, color: C.accent4 });
s.addNotes(
  "Today's rule: spray the worst fields first. Our plan makes one swap. Skip F9. Treat F4, the bridge between the " +
  "hotspot and the healthy fields. Same four sprays. " + fmt(cutPct, 0) + " percent less loss. Proven optimal against all 495 plans.");

// ================================================================== 4. FORMULATION
pres.addSection({ title: "Method" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
s.addText("The spread itself makes the problem quadratic", { placeholder: "title" });
text(s, "minimise   f(x) =", { x: M, y: 1.45, w: 5, h: 0.4, fontSize: 15, color: C.accent4 });
const terms = [
  ["Direct loss in untreated fields", "Σ  Dᵢ (1 − xᵢ)", H.lt2, C.text1],
  ["Re-infestation between untreated neighbours", "+  Σ  Wᵢⱼ (1 − xᵢ)(1 − xⱼ)", H.accent5, C.accent1],
  ["Chemical load of treatment", "+  λ Σ  Eᵢ xᵢ", H.lt2, C.text1],
];
terms.forEach(([lab, f, fill, col], i) => {
  const y = 1.95 + i * 1.12;
  card(s, M, y, 6.6, 0.95, fill, "term " + (i + 1));
  text(s, lab, { x: M + 0.3, y: y + 0.1, w: 6.0, h: 0.3, fontSize: 13, bold: true, color: col });
  text(s, f, { x: M + 0.3, y: y + 0.42, w: 6.0, h: 0.45, fontFace: "Cambria", fontSize: 22, color: C.text1 });
});
text(s, [
  { text: "subject to   ", options: { color: C.accent4, fontSize: 15 } },
  { text: "Σ xᵢ = K", options: { fontFace: "Cambria", fontSize: 22, bold: true } },
  { text: "   (the spray team's capacity)", options: { color: C.accent4, fontSize: 15 } },
], { x: M, y: 5.4, w: 6.6, h: 0.5, color: C.text1 });
text(s, "xᵢ = 1 means field i is treated. Dᵢ, Wᵢⱼ come from scouting data, field value and a wind-biased moth dispersal kernel.",
  { x: M, y: 6.0, w: 6.6, h: 0.6, fontSize: 12, color: C.accent4 });
// mapping column
const mx = 7.85;
text(s, "MAPPED TO QUBITS", { x: mx, y: 1.5, w: 4.5, h: 0.35, fontSize: 13, bold: true, color: C.accent1, charSpacing: 2 });
[["F", "Field i", "qubit i"], ["Z", "Spread link i – j", "ZZ coupling  (Ising Hamiltonian)"],
 ["K", "Budget of K sprays", "fixed Hamming weight"]].forEach(([g, a, b], i) => {
  const y = 2.05 + i * 1.12;
  chip(s, mx, y + 0.05, 0.7, g, H.accent1, C.background1);
  text(s, a, { x: mx + 0.95, y, w: 4.0, h: 0.4, fontSize: 18, bold: true, color: C.text1 });
  text(s, "→  " + b, { x: mx + 0.95, y: y + 0.42, w: 4.0, h: 0.4, fontSize: 15, color: C.text1 });
});
card(s, mx, 5.4, W - M - mx, 1.2, H.lt2, "size card");
text(s, [
  { text: "12 fields = 12 qubits\n", options: { bold: true, fontSize: 18, breakLine: true } },
  { text: "4,096 bitstrings, but only 495 are valid plans", options: { fontSize: 14, color: C.accent4 } },
], { x: mx + 0.3, y: 5.55, w: W - M - mx - 0.6, h: 0.9, color: C.text1, valign: "middle" });
s.addNotes(
  "One qubit per field. The objective: direct loss, re-infestation between untreated neighbours, and chemical load. " +
  "Re-infestation multiplies two decisions, so every spread link becomes a ZZ coupling. A natural QUBO.");

// ================================================================== 5. QUANTUM CIRCUIT
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
s.addText("Every shot is a valid spray plan", { placeholder: "title" });
const bw = 2.6, bh = 1.75, by = 1.95, gap = 0.47;
const boxes = [
  ["Dicke state", "|D₁₂,₄⟩", "all 495 valid plans in equal superposition", H.accent5, C.text1, C.accent1],
  ["Cost layer", [{ text: "exp(−iγ H" }, { text: "C", options: { subscript: true } }, { text: ")" }], "RZ + RZZ gates score loss and spread", H.accent1, C.background1, C.background1],
  ["XY mixer", [{ text: "exp(−iβ H" }, { text: "XY", options: { subscript: true } }, { text: ")" }], "moves a spray between fields, never adds one", H.accent1, C.background1, C.background1],
  ["Measure", "bitstring", "read out directly as a spray plan", H.accent5, C.text1, C.accent1],
];
boxes.forEach(([t1, f, d, fill, col, tcol], i) => {
  const x = M + i * (bw + gap);
  card(s, x, by, bw, bh, fill, "step " + t1);
  text(s, t1, { x: x + 0.22, y: by + 0.18, w: bw - 0.44, h: 0.35, fontSize: 16, bold: true, color: tcol });
  text(s, f, { x: x + 0.22, y: by + 0.55, w: bw - 0.44, h: 0.45, fontFace: "Cambria", fontSize: 19, color: col });
  text(s, d, { x: x + 0.22, y: by + 1.03, w: bw - 0.44, h: 0.62, fontSize: 13, color: col, valign: "top" });
  if (i < 3) arrow(s, x + bw + 0.06, by + bh / 2, x + bw + gap - 0.06, by + bh / 2, H.accent4, 2.25);
});
// "x p layers" bracket over boxes 2-3
const bx1 = M + (bw + gap), bx2 = M + 3 * bw + 2 * gap;
s.addShape(pres.shapes.LINE, { x: bx1, y: by - 0.22, w: bx2 - bx1, h: 0, line: { color: H.accent1, width: 1.5 } });
s.addShape(pres.shapes.LINE, { x: bx1, y: by - 0.22, w: 0, h: 0.14, line: { color: H.accent1, width: 1.5 } });
s.addShape(pres.shapes.LINE, { x: bx2, y: by - 0.22, w: 0, h: 0.14, line: { color: H.accent1, width: 1.5 } });
text(s, "repeated p times", { x: bx1, y: by - 0.58, w: bx2 - bx1, h: 0.3, align: "center", fontSize: 12,
  bold: true, color: C.accent1 });
// classical loop
const ly = 4.35;
card(s, bx1, ly, bx2 - bx1, 0.95, H.lt2, "classical loop");
text(s, [
  { text: "Classical optimiser  ", options: { bold: true } },
  { text: "COBYLA tunes γ, β on CVaR₀.₂, the mean cost of the best 20% of outcomes", options: {} },
], { x: bx1 + 0.25, y: ly + 0.1, w: bx2 - bx1 - 0.5, h: 0.75, fontSize: 14, color: C.text1, valign: "middle" });
arrow(s, bx1 + 0.9, by + bh + 0.06, bx1 + 0.9, ly - 0.06, H.accent4, 1.5);
arrow(s, bx2 - 0.9, ly - 0.06, bx2 - 0.9, by + bh + 0.06, H.accent4, 1.5);
text(s, "⟨cost⟩", { x: bx1 + 1.0, y: by + bh + 0.2, w: 1.2, h: 0.3, fontSize: 11, color: C.accent4 });
text(s, "γ, β", { x: bx2 - 1.6, y: by + bh + 0.2, w: 0.6, h: 0.3, fontSize: 11, color: C.accent4, align: "right" });
// takeaway
text(s, [
  { text: "Every gate conserves Σ xᵢ = K.  ", options: { bold: true, color: C.accent1 } },
  { text: "No penalty weight to tune, no shots wasted on impossible plans. Dicke circuit (Bärtschi & Eidenbenz 2019) implemented from scratch and unit-tested.", options: { color: C.text1 } },
], { x: M, y: 5.65, w: W - 2 * M, h: 0.9, fontSize: 15, valign: "top" });
s.addNotes(
  "The spray budget is built into the circuit. A Dicke state holds every plan with exactly K sprays. The XY mixer " +
  "moves sprays; it never adds one. Every shot is a valid plan. We train on CVaR: the best twenty percent of outcomes.");

// ================================================================== 6. RESULTS
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText(fmt(last(cv).amplification, 0) + "× more likely to return the optimal plan", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{
  name: "P(optimal plan) per shot",
  labels: ["Random valid plan", "Penalty QAOA", "XY-QAOA", "XY-QAOA + CVaR"],
  values: [uniformPct, 100 * last(pen).p_optimal, 100 * last(xy).p_optimal, 100 * last(cv).p_optimal],
}], Object.assign(chartBase(), {
  x: M, y: 1.4, w: 7.4, h: 5.2, barDir: "col", barGapWidthPct: 55,
  chartColors: [H.accent4, H.accent3, H.accent6, H.accent1],
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', dataLabelFontSize: 14,
  dataLabelColor: H.dk1, dataLabelFontBold: true,
  showTitle: true, title: "Probability that one shot is the optimal plan  (p = 4 layers, statevector)",
  valAxisLabelFormatCode: '0"%"', valAxisMaxVal: 14, valAxisMajorUnit: 2, showLegend: false,
  objectName: "P(optimal) chart",
}));
const sx = 8.55, sw = W - M - sx;
stat(s, sx, 1.4, sw, "100%", "of shots are valid plans.\nPenalty QAOA: " + fmt(100 * last(pen).p_feasible, 0) + "%", { size: 50 });
stat(s, sx, 3.15, sw, qs.optimal_shots + " / " + qs.shots, "Aer shots were the certified optimum (" +
  qs.objective + ", p = " + qs.p + ")", { size: 44 });
text(s, "Penalty QAOA finds the optimum no more often than random guessing. Transpiled circuit: " + qs.cx +
  " CX gates, depth " + qs.transpiled_depth + ".", { x: sx, y: 5.15, w: sw, h: 1.3, fontSize: 13, color: C.accent4, valign: "top" });
s.addNotes(
  "Textbook penalty QAOA wastes " + fmt(100 * (1 - last(pen).p_feasible), 0) + " percent of its shots and does no " +
  "better than chance. Ours: 100 percent valid. The optimal plan in " + qs.optimal_shots + " of " + qs.shots + " shots. " +
  fmt(last(cv).amplification, 0) + " times better than random.");

// ================================================================== 7. ROBUSTNESS + PARETO
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("It holds across villages and spray budgets", { placeholder: "title" });
const pf = S.pareto;
s.addChart(pres.charts.LINE, [
  { name: "Q-SHIELD optimum", labels: pf.map((f) => String(f.K)), values: pf.map((f) => Math.round(f.loss)) },
  { name: "Spray worst first", labels: pf.map((f) => String(f.K)), values: pf.map((f) => Math.round(f.g_loss)) },
], Object.assign(chartBase(), {
  x: M, y: 1.4, w: 7.4, h: 5.2, chartColors: [H.accent1, H.accent2], lineSize: 3, lineDataSymbol: "circle",
  lineDataSymbolSize: 8, showLegend: true, legendPos: "t", legendFontSize: 12, legendColor: H.dk1,
  showTitle: true, title: "Expected crop loss (USD) as the spray budget grows",
  showCatAxisTitle: true, catAxisTitle: "fields the team can spray (K)", showValAxisTitle: false,
  valAxisLabelFormatCode: '"$"#,##0', objectName: "budget trade-off chart",
}));
stat(s, sx, 1.4, sw, fmt(bs.greedy_gap_pct.mean, 1) + "%", "average extra loss from spraying the worst first, over 12 random villages (up to " +
  fmt(bs.greedy_gap_pct.max, 0) + "%)", { size: 50, labelH: 1.0, color: C.accent2 });
stat(s, sx, 3.55, sw, exactVillages + " / 12", "villages where QAOA's best of 1,024 shots is exactly optimal",
  { size: 50, labelH: 0.8 });
text(s, "QAOA matched the exact optimum at every budget tested (K = 2 to 6).", { x: sx, y: 5.55, w: sw, h: 0.8,
  fontSize: 13, color: C.accent4, valign: "top" });
s.addNotes(
  "Across 12 villages, spraying the worst first loses up to " + fmt(bs.greedy_gap_pct.max, 0) + " percent. Our best " +
  "sample is optimal in " + exactVillages + " of 12, and at every spray budget we tested.");

// ================================================================== 8. HONEST LIMITS
pres.addSection({ title: "Limits" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Limits" });
s.addText("What quantum does not do here, yet", { placeholder: "title" });
const nl = ["ideal", "0.1%", "0.3%", "1%"];
s.addChart(pres.charts.LINE, [
  { name: "Post-selected valid shots", labels: nl, values: noiseBest.map((r) => +(100 * r.p_opt_postselected).toFixed(2)) },
  { name: "All shots", labels: nl, values: noiseBest.map((r) => +(100 * r.p_opt).toFixed(2)) },
  { name: "Random valid plan", labels: nl, values: noiseBest.map(() => +uniformPct.toFixed(2)) },
], Object.assign(chartBase(), {
  x: M, y: 1.4, w: 6.6, h: 5.2, chartColors: [H.accent1, H.accent6, H.accent4], lineSize: 3,
  lineDataSymbol: "circle", lineDataSymbolSize: 8, showLegend: true, legendPos: "t", legendFontSize: 12,
  legendColor: H.dk1, showTitle: true, title: "P(optimal plan) per shot under simulated hardware noise",
  showCatAxisTitle: true, catAxisTitle: "two-qubit gate error rate", valAxisLabelFormatCode: '0"%"',
  objectName: "noise chart",
}));
const lx = 7.75, lw = W - M - lx - 0.85;
[["1", "No speed-up claimed", "At 12 fields, exact search over 495 plans takes milliseconds. Our claim is a correct, constraint-native formulation, not an advantage."],
 ["2", "Noise breaks the guarantee", "With post-selection, the signal survives up to 0.3% gate error (" +
   fmt(noiseBest[2].p_opt_postselected / noiseBest[2].uniform, 0) + "× random) and is gone by 1%."],
 ["3", "A model, not field data", "The dispersal kernel is calibrated from literature. Next: fit it to FAO FAMEWS trap data."]]
  .forEach(([n, h, d], i) => {
    const y = 1.5 + i * 1.65;
    chip(s, lx, y, 0.6, n, H.lt2, C.accent1);
    text(s, h, { x: lx + 0.85, y, w: lw, h: 0.4, fontSize: 18, bold: true, color: C.text1 });
    text(s, d, { x: lx + 0.85, y: y + 0.45, w: lw, h: 1.05, fontSize: 14, color: C.text1, valign: "top" });
  });
s.addNotes(
  "The limits. No speed-up at 12 fields; classical search is instant. Hardware noise erodes the guarantee beyond " +
  "0.3 percent error. And the spread model still awaits field data.");

// ================================================================== 9. CLOSE
pres.addSection({ title: "Close" });
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Close" });
s.addImage({ path: IMG("map_qshield.png"), x: 7.35, y: 0.75, w: 5.6, h: 5.0, transparency: 8,
  altText: "Q-SHIELD spray plan on the field network", objectName: "closing map" });
text(s, "Q-SHIELD", { x: M, y: 1.0, w: 7, h: 1.2, fontFace: THEME.headFontFace, fontSize: 66, bold: true,
  color: C.background1 });
text(s, [
  { text: "A real farming decision.", options: { breakLine: true } },
  { text: "A constraint-native quantum formulation.", options: { breakLine: true } },
  { text: "Fully reproducible in Qiskit.", options: {} },
], { x: M, y: 2.45, w: 6.6, h: 1.6, fontSize: 24, color: C.background1, paraSpaceAfter: 6 });
text(s, "NEXT", { x: M, y: 4.45, w: 3, h: 0.35, fontSize: 13, bold: true, color: C.accent6, charSpacing: 2 });
text(s, [
  { text: "Calibrate spread with FAO FAMEWS trap data", options: { bullet: { indent: 18 }, breakLine: true } },
  { text: "Run on IBM Heron with error mitigation", options: { bullet: { indent: 18 }, breakLine: true } },
  { text: "Multi-week plans and fairness between farmers", options: { bullet: { indent: 18 } } },
], { x: M, y: 4.85, w: 6.4, h: 1.2, fontSize: 15, color: "C9D1CC", paraSpaceAfter: 4 });
text(s, "github.com/asadsheikh91/q-shield", { x: M, y: 6.55, w: 6, h: 0.35, fontSize: 15, bold: true,
  color: C.accent6, hyperlink: { url: "https://github.com/asadsheikh91/q-shield" } });
s.addNotes(
  "Q-SHIELD. A real farming decision. A constraint-native quantum formulation. Fully reproducible. Thank you.");

// ------------------------------------------------------------------ write
(async () => {
  await pres.writeFile({ fileName: OUT });
  if (SKILL_THEME) {
    const { applyTheme } = require(SKILL_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("saved", OUT);
})();
