"""Sanity tests: run with  `python -m pytest -q`  or  `python tests/test_core.py`."""
import os
import sys
from math import comb

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qiskit.quantum_info import Statevector  # noqa: E402

from qshield.instance import make_instance  # noqa: E402
from qshield.quantum import dicke_state, build_qaoa  # noqa: E402
from qshield.classical import exact  # noqa: E402


def test_dicke_is_uniform_over_weight_k():
    for n, k in [(4, 2), (6, 3), (8, 3)]:
        probs = Statevector(dicke_state(n, k)).probabilities()
        w = np.array([bin(i).count("1") for i in range(2 ** n)])
        assert np.allclose(probs[w == k], 1 / comb(n, k), atol=1e-9)
        assert probs[w != k].sum() < 1e-9


def test_qubo_matches_direct_cost():
    inst = make_instance(n=8, K=3, lam=50.0, seed=3)
    vec = inst.all_cost_vector()
    rng = np.random.default_rng(0)
    for _ in range(20):
        idx = int(rng.integers(0, 2 ** inst.n))
        x = [(idx >> i) & 1 for i in range(inst.n)]
        assert np.isclose(vec[idx], inst.cost(x))


def test_xy_qaoa_preserves_feasibility():
    inst = make_instance(n=8, K=3, seed=3)
    qc, params, _, _ = build_qaoa(inst, p=2, mode="xy")
    probs = Statevector(qc.assign_parameters(np.random.default_rng(1).uniform(0, 3, len(params)))).probabilities()
    w = np.array([bin(i).count("1") for i in range(2 ** inst.n)])
    assert probs[w == inst.K].sum() > 1 - 1e-9


def test_exact_is_optimal():
    inst = make_instance(n=8, K=3, seed=3)
    vec = inst.all_cost_vector()
    w = np.array([bin(i).count("1") for i in range(2 ** inst.n)])
    assert np.isclose(exact(inst)["cost"], vec[w == inst.K].min())


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
