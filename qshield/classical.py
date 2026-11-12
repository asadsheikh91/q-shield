"""Classical references: exact enumeration, field-practice greedy, network-aware greedy, simulated annealing."""
from __future__ import annotations

import time
import numpy as np

from .instance import FAWInstance, feasible_bitstrings


def exact(inst: FAWInstance) -> dict:
    """Exhaustive search over all C(n, K) feasible plans -> certified global optimum (and worst plan)."""
    t0 = time.perf_counter()
    best, best_x, worst = np.inf, None, -np.inf
    costs = []
    for x in feasible_bitstrings(inst.n, inst.K):
        c = inst.cost(x)
        costs.append(c)
        if c < best:
            best, best_x = c, x.copy()
        worst = max(worst, c)
    return {"x": best_x, "cost": best, "worst": worst, "n_feasible": len(costs),
            "costs": np.sort(np.array(costs)), "time_s": time.perf_counter() - t0}


def greedy_infestation(inst: FAWInstance) -> dict:
    """What happens today: spray the K most heavily infested / highest-value fields (ignores spread)."""
    score = inst.direct_loss()
    x = np.zeros(inst.n, dtype=int)
    x[np.argsort(-score)[: inst.K]] = 1
    return {"x": x, "cost": inst.cost(x)}


def greedy_marginal(inst: FAWInstance) -> dict:
    """Stronger heuristic: add the field with the largest marginal cost reduction, K times."""
    x = np.zeros(inst.n, dtype=int)
    for _ in range(inst.K):
        best_i, best_c = None, np.inf
        for i in np.flatnonzero(x == 0):
            x[i] = 1
            c = inst.cost(x)
            x[i] = 0
            if c < best_c:
                best_i, best_c = i, c
        x[best_i] = 1
    return {"x": x, "cost": inst.cost(x)}


def simulated_annealing(inst: FAWInstance, iters: int = 4000, T0: float = None, seed: int = 0) -> dict:
    """Swap-move SA that stays inside the feasible set (sum x = K)."""
    rng = np.random.default_rng(seed)
    x = np.zeros(inst.n, dtype=int)
    x[rng.choice(inst.n, inst.K, replace=False)] = 1
    c = inst.cost(x)
    T0 = T0 or max(1.0, 0.1 * abs(c))
    best_x, best_c = x.copy(), c
    for t in range(iters):
        T = T0 * (1 - t / iters) + 1e-9
        i = rng.choice(np.flatnonzero(x == 1))
        j = rng.choice(np.flatnonzero(x == 0))
        x[i], x[j] = 0, 1
        c2 = inst.cost(x)
        if c2 <= c or rng.random() < np.exp(-(c2 - c) / T):
            c = c2
            if c < best_c:
                best_x, best_c = x.copy(), c
        else:
            x[i], x[j] = 1, 0
    return {"x": best_x, "cost": best_c}
