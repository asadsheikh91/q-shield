"""Q-SHIELD end-to-end demo.

    python run_demo.py            # full run (~ a few minutes on a laptop)
    python run_demo.py --quick    # smaller sweep for a fast check

Outputs land in ./results : summary.json, plan table, and all figures used in the report.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from math import comb

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from qshield.instance import make_instance  # noqa: E402
from qshield.classical import exact, greedy_infestation, greedy_marginal, simulated_annealing  # noqa: E402
from qshield.quantum import QAOARunner, sample, decode  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
C_Q, C_P, C_G, C_E = "#6929C4", "#9F1853", "#B28600", "#198038"   # quantum / penalty / greedy / exact
plt.rcParams.update({"figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 10})


def plan_str(inst, x):
    return ", ".join(inst.names[i] for i in np.flatnonzero(x))


def best_from_counts(inst, counts):
    best_x, best_c = None, np.inf
    feas_shots = 0
    for bs, c in counts.items():
        x = decode(bs)
        if x.sum() != inst.K:
            continue
        feas_shots += c
        cost = inst.cost(x)
        if cost < best_c:
            best_x, best_c = x, cost
    return best_x, best_c, feas_shots


# ----------------------------------------------------------------------------- figures
def fig_map(inst, plans, path):
    fig, axes = plt.subplots(1, len(plans), figsize=(5.2 * len(plans), 4.8))
    W = inst.spread_matrix()
    wmax = W.max()
    for ax, (title, x, cost) in zip(axes, plans):
        for i in range(inst.n):
            for j in range(i + 1, inst.n):
                if W[i, j] > 0.04 * wmax:
                    ax.plot(*inst.xy[[i, j]].T, color="#8D8D8D", lw=0.4 + 3.5 * W[i, j] / wmax,
                            alpha=0.55, zorder=1)
        sc = ax.scatter(*inst.xy.T, s=180 + 260 * inst.area, c=inst.infest, cmap="YlOrRd", vmin=0, vmax=0.7,
                        edgecolors=["#0F62FE" if xi else "#393939" for xi in x],
                        linewidths=[3.5 if xi else 0.8 for xi in x], zorder=2)
        for i in range(inst.n):
            ax.annotate(inst.names[i], inst.xy[i], ha="center", va="center", fontsize=7.5, zorder=3)
        ax.set_title(f"{title}\nexpected loss + load = {cost:,.0f}", fontsize=10)
        ax.set_xlabel("km"); ax.set_ylabel("km"); ax.set_aspect("equal")
        ax.annotate("", xy=(2.45, 2.45), xytext=(2.15, 2.15),
                    arrowprops=dict(arrowstyle="->", color="#0F62FE", lw=1.5))
        ax.text(2.0, 2.5, "wind", color="#0F62FE", fontsize=8)
    fig.colorbar(sc, ax=axes, shrink=0.75, label="scouted infestation probability")
    fig.suptitle("Fields treated (blue ring) — edge width = re-infestation risk between neighbours", y=1.0)
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)


def fig_layers(hist_xy, hist_pen, path, hist_cv=None):
    p = [h["p"] for h in hist_xy]
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    ax[0].plot(p, [h["approx_ratio"] for h in hist_xy], "o-", color=C_Q, label="XY-mixer QAOA (ours)")
    ax[0].plot(p, [h["approx_ratio"] for h in hist_pen], "s--", color=C_P, label="penalty QAOA")
    if hist_cv:
        ax[0].plot(p, [h["approx_ratio"] for h in hist_cv], "D-.", color="#1192E8", label="XY + CVaR(0.2)")
        ax[1].plot(p, [h["p_feasible"] for h in hist_cv], "D-.", color="#1192E8")
        ax[2].semilogy(p, [h["p_optimal"] for h in hist_cv], "D-.", color="#1192E8")
    ax[0].axhline(0.5, color="#8D8D8D", ls=":", lw=1); ax[0].text(p[-1], 0.51, "random feasible", ha="right", fontsize=8)
    ax[0].set_title("Approximation ratio (feasible part)"); ax[0].set_xlabel("QAOA layers p"); ax[0].set_ylim(0, 1.02)
    ax[0].legend(fontsize=8)
    ax[1].plot(p, [h["p_feasible"] for h in hist_xy], "o-", color=C_Q)
    ax[1].plot(p, [h["p_feasible"] for h in hist_pen], "s--", color=C_P)
    ax[1].set_title("Probability a shot is a feasible plan"); ax[1].set_xlabel("QAOA layers p"); ax[1].set_ylim(0, 1.05)
    ax[2].semilogy(p, [h["p_optimal"] for h in hist_xy], "o-", color=C_Q)
    ax[2].semilogy(p, [h["p_optimal"] for h in hist_pen], "s--", color=C_P)
    ax[2].axhline(hist_xy[0]["p_optimal_uniform_feasible"], color="#8D8D8D", ls=":", lw=1)
    ax[2].text(p[0], hist_xy[0]["p_optimal_uniform_feasible"] * 1.15, "uniform over feasible plans", fontsize=8)
    ax[2].set_title("Probability of the optimal plan per shot"); ax[2].set_xlabel("QAOA layers p")
    for a in ax:
        a.set_xticks(p)
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)


def fig_distribution(runner, h_best, path):
    feas = runner.feasible
    costs = runner.cost_vec[feas]
    order = np.argsort(costs)
    pq = h_best["probs"][feas][order]
    unif = np.full(feas.sum(), 1 / feas.sum())
    fig, ax = plt.subplots(figsize=(9, 3.4))
    rank = np.arange(1, len(order) + 1)
    ax.bar(rank, pq, width=1.0, color=C_Q, alpha=0.85, label=f"QAOA p={h_best['p']} output")
    ax.plot(rank, unif, color="#8D8D8D", lw=1.2, label="Dicke start (uniform)")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(1e-6, 1)
    ax.set_xlabel("feasible spray plans ranked by true cost (1 = optimal)")
    ax.set_ylabel("probability")
    ax.set_title("QAOA concentrates probability on the best spray plans")
    ax.legend(); fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)


def fig_landscape(land, path):
    fig, ax = plt.subplots(figsize=(4.8, 3.8))
    im = ax.imshow(land["E"], origin="lower", aspect="auto", cmap="viridis",
                   extent=[land["gammas"][0], land["gammas"][-1], land["betas"][0], land["betas"][-1]])
    ax.set_xlabel("γ (cost angle)"); ax.set_ylabel("β (XY-mixer angle)")
    ax.set_title("p = 1 energy landscape ⟨H_C⟩")
    fig.colorbar(im, ax=ax, label="expected cost (USD)")
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)


def fig_pareto(front, path):
    fig, ax = plt.subplots(figsize=(6.4, 4))
    k = [f["K"] for f in front]
    ax.plot([f["chem"] for f in front], [f["loss"] for f in front], "o-", color=C_E, label="exact optimum per K")
    ax.plot([f["g_chem"] for f in front], [f["g_loss"] for f in front], "^:", color=C_G, label="spray-most-infested")
    qa = [f for f in front if f.get("q_loss") is not None]
    ax.scatter([f["q_chem"] for f in qa], [f["q_loss"] for f in qa], s=110, facecolors="none",
               edgecolors=C_Q, linewidths=2, label="QAOA best sample", zorder=5)
    for f in front:
        ax.annotate(f"K={f['K']}", (f["chem"], f["loss"]), textcoords="offset points", xytext=(5, 4), fontsize=7)
    ax.set_xlabel("chemical load (treated-area units)"); ax.set_ylabel("expected crop loss (USD)")
    ax.set_title("Trade-off: crop loss vs chemical load")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)


def fig_noise(rows, path):
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
    for lab, col in zip(dict.fromkeys(r["circuit"] for r in rows), [C_Q, C_P]):
        rr = [r for r in rows if r["circuit"] == lab]
        x = [max(r["noise"], 3e-4) for r in rr]
        ax[0].plot(x, [r["p_opt"] for r in rr], "o-", color=col, label=lab)
        ax[0].plot(x, [r["p_opt_postselected"] for r in rr], "o:", color=col, alpha=0.6, label=lab + " (post-selected)")
        ax[1].plot(x, [r["p_feasible"] for r in rr], "o-", color=col, label=lab)
    ax[0].axhline(rows[0]["uniform"], color="#8D8D8D", ls=":", lw=1)
    ax[0].text(3e-4, rows[0]["uniform"] * 1.4, "uniform over feasible plans", fontsize=8)
    for a in ax:
        a.set_xscale("log"); a.set_xlabel("2-qubit depolarising error (leftmost point = noiseless)")
    ax[0].set_yscale("symlog", linthresh=1e-3); ax[0].set_ylim(0, 0.3); ax[0].set_ylabel("P(optimal plan)"); ax[0].set_title("Optimal-plan probability under noise")
    ax[1].set_ylabel("P(feasible)"); ax[1].set_ylim(0, 1.05); ax[1].set_title("Feasibility guarantee erodes with noise")
    ax[0].legend(fontsize=7); fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)


def fig_bench(bench, path):
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
    sd = [b["seed"] for b in bench]
    ax[0].bar(sd, [b["greedy_gap_pct"] for b in bench], color=C_G)
    ax[0].set_title("Extra loss of 'spray most infested' vs optimum"); ax[0].set_xlabel("village (random seed)")
    ax[0].set_ylabel("% above optimal cost")
    ax[1].bar(sd, [b["qaoa_p3_approx"] for b in bench], color=C_Q)
    ax[1].axhline(0.5, color="#8D8D8D", ls=":"); ax[1].set_ylim(0, 1)
    ax[1].set_title("XY-QAOA (p=3) approximation ratio per village"); ax[1].set_xlabel("village (random seed)")
    fig.tight_layout(); fig.savefig(path, bbox_inches="tight"); plt.close(fig)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--K", type=int, default=4)
    ap.add_argument("--seed", type=int, default=6)
    ap.add_argument("--pmax", type=int, default=4)
    args = ap.parse_args()
    global OUT
    if args.quick:
        args.pmax = 3
        OUT = os.path.join(OUT, "quick")      # never overwrite the full results used by the report
    os.makedirs(OUT, exist_ok=True)
    t_start = time.perf_counter()
    summary = {}

    inst = make_instance(n=args.n, K=args.K, seed=args.seed)
    print(f"Instance: {inst.n} fields, K={inst.K} sprays, {comb(inst.n, inst.K)} feasible plans "
          f"out of {2 ** inst.n} bitstrings")
    summary["instance"] = {
        "n": inst.n, "K": inst.K, "seed": args.seed, "fields": [
            {"name": inst.names[i], "x_km": round(float(inst.xy[i, 0]), 3), "y_km": round(float(inst.xy[i, 1]), 3),
             "area_ha": float(inst.area[i]), "infestation": float(inst.infest[i]),
             "value_usd": float(inst.value[i]), "chem_load": float(inst.chem[i])} for i in range(inst.n)],
        "meta": inst.meta}

    # ---- classical references
    ex = exact(inst)
    g1 = greedy_infestation(inst)
    g2 = greedy_marginal(inst)
    sa = simulated_annealing(inst, seed=1)
    summary["classical"] = {
        "exact": {"plan": plan_str(inst, ex["x"]), "cost": ex["cost"], "worst": ex["worst"],
                  "time_s": ex["time_s"], **inst.breakdown(ex["x"])},
        "greedy_most_infested": {"plan": plan_str(inst, g1["x"]), "cost": g1["cost"], **inst.breakdown(g1["x"])},
        "greedy_marginal": {"plan": plan_str(inst, g2["x"]), "cost": g2["cost"]},
        "simulated_annealing": {"plan": plan_str(inst, sa["x"]), "cost": sa["cost"]},
    }
    print(f"Exact optimum      : {ex['cost']:9.1f}  [{plan_str(inst, ex['x'])}]")
    print(f"Spray-most-infested: {g1['cost']:9.1f}  [{plan_str(inst, g1['x'])}]  "
          f"(+{100 * (g1['cost'] / ex['cost'] - 1):.1f}% loss vs optimum)")
    print(f"Marginal greedy    : {g2['cost']:9.1f}")
    print(f"Simulated annealing: {sa['cost']:9.1f}")

    # ---- quantum: XY-mixer QAOA vs penalty QAOA
    rq = QAOARunner(inst, "xy")
    hist_xy, land = rq.optimise(p_max=args.pmax)
    rp = QAOARunner(inst, "penalty")
    hist_pen, _ = rp.optimise(p_max=args.pmax)
    rc = QAOARunner(inst, "xy", cvar_alpha=0.2)
    hist_cv, _ = rc.optimise(p_max=args.pmax)
    for h in hist_cv:
        print(f"  CVaR p={h['p']}: approx={h['approx_ratio']:.3f}  P(opt)={h['p_optimal']:.4f} "
              f"(x{h['amplification']:.1f} vs uniform)")
    for h in hist_xy:
        print(f"  XY  p={h['p']}: approx={h['approx_ratio']:.3f}  P(opt)={h['p_optimal']:.4f} "
              f"(x{h['amplification']:.1f} vs uniform)  feasible={h['p_feasible']:.3f}  CX={h['cx_count']}")
    for h in hist_pen:
        print(f"  PEN p={h['p']}: approx={h['approx_ratio']:.3f}  P(opt)={h['p_optimal']:.4f}  "
              f"feasible={h['p_feasible']:.3f}  CX={h['cx_count']}")
    strip = lambda hs: [{k: v for k, v in h.items() if k != "probs"} for h in hs]  # noqa: E731
    summary["qaoa_xy"] = strip(hist_xy)
    summary["qaoa_penalty"] = strip(hist_pen)
    summary["qaoa_xy_cvar"] = strip(hist_cv)

    # ---- shot-based run of the best XY circuit on Aer
    cands = [("mean-energy", rq, h) for h in hist_xy] + [("CVaR(0.2)", rc, h) for h in hist_cv]
    best_obj, best_runner, best = max(cands, key=lambda c: c[2]["p_optimal"])
    circ = best_runner.full_circuit(best["theta"], best["p"])
    counts, tqc = sample(circ, shots=4096)
    qx, qc_cost, feas_shots = best_from_counts(inst, counts)
    opt_shots = sum(c for bs, c in counts.items() if np.isclose(inst.cost(decode(bs)), ex["cost"])
                    and decode(bs).sum() == inst.K)
    summary["qaoa_sampled"] = {"p": best["p"], "objective": best_obj, "shots": 4096, "feasible_shots": feas_shots,
                               "optimal_shots": opt_shots, "best_plan": plan_str(inst, qx),
                               "best_cost": qc_cost, "matches_exact": bool(np.isclose(qc_cost, ex["cost"])),
                               "transpiled_depth": tqc.depth(), "cx": tqc.count_ops().get("cx", 0)}
    print(f"Aer 4096 shots ({best_obj}, p={best['p']}): best plan [{plan_str(inst, qx)}] cost {qc_cost:.1f}; "
          f"optimal plan seen {opt_shots}x; feasible {feas_shots}/4096")
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
    summary["qaoa_top_samples"] = [{"plan": plan_str(inst, decode(b)), "count": c, "cost": inst.cost(decode(b))}
                                   for b, c in top]
    try:
        rq.full_circuit(hist_xy[0]["theta"], 1).decompose().draw("mpl", fold=40, scale=0.45,
                                                               filename=os.path.join(OUT, "fig_circuit_p1.png"))
    except Exception as exc:  # drawing is cosmetic
        print("circuit drawing skipped:", exc)

    # ---- figures
    fig_map(inst, [("Common practice: spray most infested", g1["x"], g1["cost"]),
                   ("Q-SHIELD (QAOA sample) = exact optimum" if np.isclose(qc_cost, ex["cost"])
                    else "Q-SHIELD (QAOA best sample)", qx, qc_cost)], os.path.join(OUT, "fig_map.png"))
    fig_layers(hist_xy, hist_pen, os.path.join(OUT, "fig_qaoa_layers.png"), hist_cv)
    fig_distribution(best_runner, best, os.path.join(OUT, "fig_distribution.png"))
    fig_landscape(land, os.path.join(OUT, "fig_landscape.png"))

    # ---- Pareto front: sweep spray capacity K
    front = []
    k_quantum = range(2, 7) if not args.quick else [3, 4]
    for K in range(1, inst.n):
        ik = make_instance(n=args.n, K=K, seed=args.seed)
        e = exact(ik)
        g = greedy_infestation(ik)
        row = {"K": K, "loss": ik.breakdown(e["x"])["expected_loss_usd"], "chem": float(ik.chem @ e["x"]),
               "g_loss": ik.breakdown(g["x"])["expected_loss_usd"], "g_chem": float(ik.chem @ g["x"]),
               "greedy_gap_pct": 100 * (g["cost"] / e["cost"] - 1) if e["cost"] > 0 else 0.0}
        if K in k_quantum:
            r = QAOARunner(ik, "xy", cvar_alpha=0.2)
            hk, _ = r.optimise(p_max=3)
            bk = max(hk, key=lambda h: h["p_optimal"])
            cnt, _ = sample(r.full_circuit(bk["theta"], bk["p"]), shots=2048)
            xk, ck, _ = best_from_counts(ik, cnt)
            row.update({"q_loss": ik.breakdown(xk)["expected_loss_usd"], "q_chem": float(ik.chem @ xk),
                        "q_matches_exact": bool(np.isclose(ck, e["cost"])), "q_p_opt": bk["p_optimal"],
                        "q_amplification": bk["amplification"]})
            print(f"  Pareto K={K}: exact {e['cost']:.1f}, QAOA {ck:.1f} "
                  f"({'match' if np.isclose(ck, e['cost']) else 'gap'}), P(opt)={bk['p_optimal']:.3f}")
        front.append(row)
    summary["pareto"] = front
    fig_pareto(front, os.path.join(OUT, "fig_pareto.png"))

    # ---- noise study: best circuit (and the p=1 mean-energy circuit) under depolarising noise
    rows = []
    circuits = [("best: " + best_obj + f" p={best['p']}", circ, best["p_optimal_uniform_feasible"]),
                ("mean-energy p=1", rq.full_circuit(hist_xy[0]["theta"], 1), hist_xy[0]["p_optimal_uniform_feasible"])]
    for label, circ_p, unif in circuits:
        for nz in ([0.0, 0.001, 0.003, 0.01] if not args.quick else [0.0, 0.003]):
            cnt, _ = sample(circ_p, shots=2048, noise=nz or None)
            opt = sum(c for bs, c in cnt.items() if decode(bs).sum() == inst.K
                      and np.isclose(inst.cost(decode(bs)), ex["cost"]))
            fea = sum(c for bs, c in cnt.items() if decode(bs).sum() == inst.K)
            rows.append({"circuit": label, "p": label, "noise": nz, "p_opt": opt / 2048, "p_feasible": fea / 2048,
                         "p_opt_postselected": opt / max(fea, 1), "uniform": unif})
    summary["noise"] = rows
    fig_noise(rows, os.path.join(OUT, "fig_noise.png"))
    for r in rows:
        print(f"  noise [{r['circuit']}] e2q={r['noise']:.3f}: P(opt)={r['p_opt']:.4f} feasible={r['p_feasible']:.3f} "
              f"P(opt|feasible)={r['p_opt_postselected']:.4f}")

    # ---- robustness benchmark over 12 random villages
    bench = []
    seeds = range(1, 13) if not args.quick else range(1, 4)
    for sd in seeds:
        ib = make_instance(n=args.n, K=args.K, seed=sd)
        e = exact(ib)
        g = greedy_infestation(ib)
        gm = greedy_marginal(ib)
        r = QAOARunner(ib, "xy")
        hb, _ = r.optimise(p_max=3)
        b3 = hb[-1]
        rcv = QAOARunner(ib, "xy", cvar_alpha=0.2)
        c3 = rcv.optimise(p_max=3)[0][-1]
        cnt, _ = sample(r.full_circuit(b3["theta"], 3), shots=1024, seed=sd)
        xb, cb, _ = best_from_counts(ib, cnt)
        bench.append({"seed": sd, "exact": e["cost"], "greedy_gap_pct": 100 * (g["cost"] / e["cost"] - 1),
                      "marginal_greedy_gap_pct": 100 * (gm["cost"] / e["cost"] - 1),
                      "qaoa_p3_approx": b3["approx_ratio"], "qaoa_p3_amplification": b3["amplification"],
                      "cvar_p3_approx": c3["approx_ratio"], "cvar_p3_amplification": c3["amplification"],
                      "qaoa_best_of_1024_gap_pct": 100 * (cb / e["cost"] - 1)})
        print(f"  bench seed {sd}: greedy +{bench[-1]['greedy_gap_pct']:.1f}%  QAOA p=3 approx "
              f"{b3['approx_ratio']:.3f} amp x{b3['amplification']:.1f} | CVaR amp x{c3['amplification']:.1f} | best-of-1024 gap "
              f"{bench[-1]['qaoa_best_of_1024_gap_pct']:.2f}%")
    summary["benchmark"] = bench
    summary["benchmark_stats"] = {k: {"mean": float(np.mean([b[k] for b in bench])),
                                      "min": float(np.min([b[k] for b in bench])),
                                      "max": float(np.max([b[k] for b in bench]))}
                                  for k in bench[0] if k not in ("seed", "exact")}
    fig_bench(bench, os.path.join(OUT, "fig_benchmark.png"))

    summary["runtime_s"] = time.perf_counter() - t_start
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    print(f"Done in {summary['runtime_s']:.1f}s -> {OUT}")


if __name__ == "__main__":
    main()
