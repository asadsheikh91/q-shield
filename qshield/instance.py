"""Problem model: area-wide Fall Armyworm (FAW) containment on a network of smallholder fields.

Decision variable
    x_i = 1  -> field i is treated (spray / biopesticide) in this control window
    x_i = 0  -> field i is left untreated

Objective (minimise expected loss + weighted chemical load)
    f(x) = sum_i D_i (1 - x_i)                         direct loss in untreated infested fields
         + sum_{i<j} W_ij (1 - x_i)(1 - x_j)          re-infestation spread between untreated neighbours
         + lam * sum_i E_i x_i                          environmental / chemical load of treatment

Constraint
    sum_i x_i = K                                       one community spray team can treat K fields
                                                        inside the ~72 h early-instar window

The (1-x_i)(1-x_j) spread term is what makes the problem genuinely quadratic:
treating a field protects its neighbours too, so the best set is NOT simply
"the K most infested fields".
"""
from __future__ import annotations

from dataclasses import dataclass, field
import itertools
import numpy as np


@dataclass
class FAWInstance:
    names: list[str]
    xy: np.ndarray            # (n, 2) field centroids in km
    area: np.ndarray          # ha
    infest: np.ndarray        # scouted infestation probability p_i
    value: np.ndarray         # crop value at stake, USD
    chem: np.ndarray          # chemical-load units if treated (area x dose x toxicity proxy)
    beta: np.ndarray          # (n, n) directed spread probability i -> j
    K: int
    lam: float = 0.0
    loss_frac: float = 0.30   # yield fraction lost when infested (CABI farmer surveys: 26-35 %)
    meta: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.names)

    # ---------- objective pieces ----------
    def direct_loss(self) -> np.ndarray:
        return self.value * self.infest * self.loss_frac

    def spread_matrix(self) -> np.ndarray:
        """Symmetric W_ij = expected loss on j from i plus on i from j (both untreated)."""
        S = (self.infest[:, None] * self.beta) * (self.value[None, :] * self.loss_frac)
        S = S * (1 - self.infest[None, :])      # only fields not already infested can be newly infested
        W = S + S.T
        np.fill_diagonal(W, 0.0)
        return W

    def qubo(self) -> tuple[np.ndarray, np.ndarray, float]:
        """Return (h, J, c) with f(x) = c + h.x + sum_{i<j} J_ij x_i x_j  (J upper-triangular)."""
        D = self.direct_loss()
        W = self.spread_matrix()
        n = self.n
        c = D.sum() + np.triu(W, 1).sum()
        h = -D + self.lam * self.chem
        J = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                # W (1-xi)(1-xj) = W - W xi - W xj + W xi xj
                h[i] -= W[i, j]
                h[j] -= W[i, j]
                J[i, j] = W[i, j]
        return h, J, c

    def cost(self, x) -> float:
        x = np.asarray(x, dtype=float)
        u = 1 - x
        W = self.spread_matrix()
        return float(self.direct_loss() @ u + 0.5 * u @ W @ u + self.lam * self.chem @ x)

    def breakdown(self, x) -> dict:
        x = np.asarray(x, dtype=float)
        u = 1 - x
        W = self.spread_matrix()
        return {
            "direct_loss_usd": float(self.direct_loss() @ u),
            "spread_loss_usd": float(0.5 * u @ W @ u),
            "expected_loss_usd": float(self.direct_loss() @ u + 0.5 * u @ W @ u),
            "chemical_load": float(self.chem @ x),
            "treated": [self.names[i] for i in np.flatnonzero(x)],
        }

    def all_cost_vector(self) -> np.ndarray:
        """Cost of every one of the 2^n bitstrings, indexed in Qiskit little-endian order
        (bit i of the integer index = qubit i = field i)."""
        n = self.n
        h, J, c = self.qubo()
        idx = np.arange(2 ** n)
        X = ((idx[:, None] >> np.arange(n)[None, :]) & 1).astype(float)
        return c + X @ h + np.einsum("bi,ij,bj->b", X, J, X)

    def hamming_weights(self) -> np.ndarray:
        idx = np.arange(2 ** self.n)
        return np.array([bin(i).count("1") for i in idx])


def make_instance(n: int = 12, K: int = 4, lam: float = 0.0, seed: int = 7,
                  wind_deg: float = 45.0, spread_scale_km: float = 0.6,
                  beta0: float = 0.8) -> FAWInstance:
    """Synthetic but literature-calibrated smallholder maize cluster (~2.5 x 2.5 km).

    * field size 0.4-2.0 ha (most African/South-Asian maize smallholders farm < 2 ha)
    * maize yield ~3 t/ha at ~USD 260/t
    * infestation p_i from scouting / pheromone trap counts, 0.05-0.65, spatially clustered
      around an outbreak hotspot
    * spread beta_ij = beta0 * exp(-d_ij / L) * (1 + 0.6 cos(angle(i->j) - wind))   (moth drift downwind)
    """
    rng = np.random.default_rng(seed)
    xy = rng.uniform(0, 2.5, size=(n, 2))
    area = rng.uniform(0.4, 2.0, size=n).round(2)
    value = (area * 3.0 * 260).round(0)
    hotspot = np.array([0.6, 0.7])
    dist_hot = np.linalg.norm(xy - hotspot, axis=1)
    infest = np.clip(0.65 * np.exp(-dist_hot / 1.1) + rng.normal(0, 0.05, n), 0.05, 0.65).round(2)
    chem = (area * rng.uniform(0.8, 1.2, n)).round(2)

    d = np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=2)
    vec = xy[None, :, :] - xy[:, None, :]
    ang = np.arctan2(vec[..., 1], vec[..., 0])
    wind = np.deg2rad(wind_deg)
    beta = beta0 * np.exp(-d / spread_scale_km) * (1 + 0.6 * np.cos(ang - wind))
    beta = np.clip(beta, 0, 0.95)
    np.fill_diagonal(beta, 0.0)

    names = [f"F{i+1}" for i in range(n)]
    return FAWInstance(names, xy, area, infest, value, chem, beta, K, lam,
                       meta={"seed": seed, "wind_deg": wind_deg, "L_km": spread_scale_km, "beta0": beta0})


def feasible_bitstrings(n: int, K: int):
    for combo in itertools.combinations(range(n), K):
        x = np.zeros(n, dtype=int)
        x[list(combo)] = 1
        yield x
