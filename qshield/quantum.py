"""Quantum component: constraint-preserving QAOA (Quantum Alternating Operator Ansatz) in Qiskit.

* Initial state : Dicke state |D^n_K>  = uniform superposition of every plan that treats exactly K fields
                  (Baertschi & Eidenbenz 2019 deterministic circuit, O(nK) gates, no post-selection)
* Cost layer    : exp(-i gamma H_C) with H_C the Ising form of the FAW-containment QUBO (RZ + RZZ gates)
* Mixer         : XY ring mixer  exp(-i beta (XX+YY)/2)  on neighbouring qubits (Hadfield et al. 2019).
                  It swaps excitations, so the Hamming weight sum(x)=K is conserved exactly:
                  every measured bitstring is a feasible spray plan.

For comparison we also build the textbook "penalty QAOA": |+>^n start, X mixer, and the
constraint added as A (sum x - K)^2.
"""
from __future__ import annotations

import time
import numpy as np
from scipy.optimize import minimize

from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import RYGate, XXPlusYYGate
from qiskit.quantum_info import Statevector

from .instance import FAWInstance


# ----------------------------------------------------------------------------- Dicke state
def _scs(qc: QuantumCircuit, m: int, k: int) -> None:
    """Split-and-cyclic-shift unitary SCS_{m,k} acting on (1-indexed) qubits m-k..m."""
    a, b = m - 2, m - 1                       # 0-indexed qubits m-1 and m
    qc.cx(a, b)
    qc.cry(2 * np.arccos(np.sqrt(1 / m)), b, a)
    qc.cx(a, b)
    for l in range(2, k + 1):
        c, d = m - l - 1, m - l               # 0-indexed qubits m-l and m-l+1
        qc.cx(c, b)
        qc.append(RYGate(2 * np.arccos(np.sqrt(l / m))).control(2), [b, d, c])
        qc.cx(c, b)


def dicke_state(n: int, k: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, name=f"Dicke({n},{k})")
    for q in range(n - k, n):
        qc.x(q)
    for m in range(n, k, -1):
        _scs(qc, m, k)
    for m in range(k, 1, -1):
        _scs(qc, m, m - 1)
    return qc


# ----------------------------------------------------------------------------- Hamiltonian
def qubo_to_ising(h: np.ndarray, J: np.ndarray):
    """x = (1 - z)/2.  Returns (a, b): H = sum a_i Z_i + sum_{i<j} b_ij Z_i Z_j  (+ const)."""
    n = len(h)
    Js = J + J.T
    a = -h / 2 - Js.sum(axis=1) / 4
    b = np.triu(J, 1) / 4
    return a, b


def penalty_qubo(inst: FAWInstance, A: float | None = None):
    h, J, c = inst.qubo()
    if A is None:
        A = float(np.max(np.abs(h) + np.abs(J).sum(0) + np.abs(J).sum(1)))
    n = inst.n
    K = inst.K
    h = h + A * (1 - 2 * K)
    J = J.copy()
    J[np.triu_indices(n, 1)] += 2 * A
    return h, J, c + A * K * K, A


# ----------------------------------------------------------------------------- Ansatz
def build_qaoa(inst: FAWInstance, p: int, mode: str = "xy", A: float | None = None,
               include_init: bool = True):
    """Return (circuit, params, scale, extra). mode in {'xy', 'penalty'}."""
    n = inst.n
    if mode == "xy":
        h, J, _ = inst.qubo()
        extra = {}
    elif mode == "penalty":
        h, J, _, A = penalty_qubo(inst, A)
        extra = {"A": A}
    else:
        raise ValueError(mode)
    a, b = qubo_to_ising(h, J)
    scale = max(np.abs(a).max(), np.abs(b).max())
    a, b = a / scale, b / scale

    gam = ParameterVector("γ", p)
    bet = ParameterVector("β", p)
    qc = QuantumCircuit(n)
    if include_init:
        if mode == "xy":
            qc.compose(dicke_state(n, inst.K), inplace=True)
        else:
            qc.h(range(n))
        qc.barrier()
    ring = [(i, (i + 1) % n) for i in range(n)]
    even = [e for e in ring if e[0] % 2 == 0]
    odd = [e for e in ring if e[0] % 2 == 1]
    for layer in range(p):
        # cost unitary exp(-i gamma H_C)
        for i in range(n):
            if abs(a[i]) > 1e-12:
                qc.rz(2 * gam[layer] * a[i], i)
        for i in range(n):
            for j in range(i + 1, n):
                if abs(b[i, j]) > 1e-12:
                    qc.rzz(2 * gam[layer] * b[i, j], i, j)
        # mixer
        if mode == "xy":
            for group in (even, odd):            # parity-ordered ring XY mixer
                for (i, j) in group:
                    qc.append(XXPlusYYGate(2 * bet[layer]), [i, j])
        else:
            for i in range(n):
                qc.rx(2 * bet[layer], i)
        qc.barrier()
    qc.metadata = {"params": list(gam) + list(bet)}
    return qc, list(gam) + list(bet), scale, extra


# ----------------------------------------------------------------------------- Optimisation
class QAOARunner:
    """Exact statevector optimisation of the variational parameters, then shot-based sampling."""

    def __init__(self, inst: FAWInstance, mode: str = "xy", cvar_alpha: float | None = None):
        """cvar_alpha=None -> minimise mean energy <H_C>;  cvar_alpha in (0,1] -> minimise CVaR_alpha,
        the mean cost of the best alpha-fraction of outcomes (Barkoutsos et al., Quantum 4, 256, 2020)."""
        self.inst = inst
        self.mode = mode
        self.cvar_alpha = cvar_alpha
        self.cost_vec = inst.all_cost_vector()                # true objective for every bitstring
        self.hw = inst.hamming_weights()
        self.feasible = self.hw == inst.K
        if mode == "penalty":
            _, _, _, A = penalty_qubo(inst)
            self.train_vec = self.cost_vec + A * (self.hw - inst.K) ** 2
        else:
            self.train_vec = self.cost_vec
        self._order = np.argsort(self.train_vec)
        n = inst.n
        init = dicke_state(n, inst.K) if mode == "xy" else _plus(n)
        self.init_sv = Statevector(init)
        self.nfev = 0

    def _probs(self, qc, theta):
        # bind by name: Qiskit sorts parameters alphabetically (β before γ), so never bind by position
        bound = qc.assign_parameters(dict(zip(qc.metadata["params"], theta)))
        return self.init_sv.evolve(bound).probabilities()

    def energy(self, theta, qc):
        self.nfev += 1
        probs = self._probs(qc, theta)
        if self.cvar_alpha is None:
            return float(probs @ self.train_vec)
        a = self.cvar_alpha
        ps = probs[self._order]
        cum = np.cumsum(ps)
        k = int(np.searchsorted(cum, a))
        w = ps.copy()
        w[k + 1:] = 0.0
        w[k] = a - (cum[k - 1] if k > 0 else 0.0)
        return float(w @ self.train_vec[self._order] / a)

    def optimise(self, p_max: int = 5, maxiter: int = 300, grid: int = 20, seed: int = 0):
        """Layer-by-layer INTERP strategy (Zhou et al. 2020) seeded by a p=1 grid search."""
        history = []
        theta = None
        landscape = None
        for p in range(1, p_max + 1):
            qc, params, scale, extra = build_qaoa(self.inst, p, self.mode, include_init=False)
            t0 = time.perf_counter()
            if p == 1:
                gs = np.linspace(0, np.pi, grid)
                bs = np.linspace(0, np.pi / 2, grid)
                landscape = np.array([[self.energy([g, bb], qc) for g in gs] for bb in bs])
                bi, gi = np.unravel_index(np.argmin(landscape), landscape.shape)
                x0 = np.array([gs[gi], bs[bi]])
                landscape = {"gammas": gs, "betas": bs, "E": landscape}
            else:
                g_prev, b_prev = theta[: p - 1], theta[p - 1:]
                x0 = np.concatenate([_interp(g_prev), _interp(b_prev)])
            res = minimize(self.energy, x0, args=(qc,), method="COBYLA",
                           options={"maxiter": maxiter, "rhobeg": 0.2})
            theta = res.x
            probs = self._probs(qc, theta)
            history.append(self.metrics(probs, p, theta, time.perf_counter() - t0, qc))
        return history, landscape

    def metrics(self, probs, p, theta, secs, qc) -> dict:
        feas = self.feasible
        fc = self.cost_vec[feas]
        c_min, c_max = fc.min(), fc.max()
        opt_mask = feas & np.isclose(self.cost_vec, c_min)
        p_feas = probs[feas].sum()
        exp_feas = (probs[feas] @ self.cost_vec[feas]) / max(p_feas, 1e-12)
        approx = (c_max - exp_feas) / (c_max - c_min)          # 1 = optimal, 0 = worst feasible plan
        n_feas = feas.sum()
        # top-1% plans
        thresh = np.quantile(fc, 0.01) if n_feas >= 100 else c_min
        top = feas & (self.cost_vec <= thresh + 1e-9)
        tq = transpile(self.full_circuit(theta, p), basis_gates=["rz", "sx", "x", "cx"], optimization_level=1)
        return {
            "p": p,
            "theta": [float(t) for t in theta],
            "p_feasible": float(p_feas),
            "p_optimal": float(probs[opt_mask].sum()),
            "p_optimal_uniform_feasible": float(opt_mask.sum() / n_feas),
            "amplification": float(probs[opt_mask].sum() / (opt_mask.sum() / n_feas)),
            "p_top1pct": float(probs[top].sum()),
            "approx_ratio": float(approx),
            "expected_cost_feasible": float(exp_feas),
            "cx_count": int(tq.count_ops().get("cx", 0)),
            "depth": int(tq.depth()),
            "opt_seconds": float(secs),
            "probs": probs,
        }

    def full_circuit(self, theta, p):
        qc, params, _, _ = build_qaoa(self.inst, p, self.mode, include_init=True)
        return qc.assign_parameters(dict(zip(params, theta)))


def _plus(n):
    qc = QuantumCircuit(n)
    qc.h(range(n))
    return qc


def _interp(v):
    """INTERP initialisation for p+1 layers from optimal p-layer angles."""
    p = len(v)
    v = np.asarray(v)
    out = np.zeros(p + 1)
    for i in range(p + 1):
        left = v[i - 1] if i - 1 >= 0 else 0.0
        right = v[i] if i < p else 0.0
        out[i] = (i / p) * left + ((p - i) / p) * right
    return out


# ----------------------------------------------------------------------------- Sampling
def sample(circuit: QuantumCircuit, shots: int = 4096, noise: float | None = None, seed: int = 11):
    """Run on Qiskit Aer. noise = two-qubit depolarising error rate (1q = noise/10), None = ideal."""
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

    qc = circuit.copy()
    qc.measure_all()
    if noise:
        nm = NoiseModel()
        nm.add_all_qubit_quantum_error(depolarizing_error(noise / 10, 1), ["sx", "x", "rz"])
        nm.add_all_qubit_quantum_error(depolarizing_error(noise, 2), ["cx"])
        ro = noise / 2
        nm.add_all_qubit_readout_error(ReadoutError([[1 - ro, ro], [ro, 1 - ro]]))
        sim = AerSimulator(noise_model=nm, seed_simulator=seed, shot_branching_enable=True)
    else:
        sim = AerSimulator(seed_simulator=seed)
    tqc = transpile(qc, sim, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1, seed_transpiler=seed)
    counts = sim.run(tqc, shots=shots).result().get_counts()
    return counts, tqc


def decode(bitstring: str) -> np.ndarray:
    """Qiskit bitstrings are big-endian (qubit 0 is the rightmost character)."""
    return np.array([int(c) for c in bitstring[::-1]])
