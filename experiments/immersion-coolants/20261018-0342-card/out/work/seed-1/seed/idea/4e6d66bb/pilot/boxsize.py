#!/usr/bin/env python3
"""Reference arithmetic for the ester MD verification plan (DERIVED numbers).

Not a measured GPU run; documents the box-size and cost arithmetic.
Saturated acyclic monoester R-COO-R' with n carbons has formula C_n H_2n O_2,
so atoms/molecule = 3n + 2. A ~15,000-atom box (the size used by the closest
prior, Ogbomo et al. 2026) holds between ~163 (n=30) and ~469 (n=10) molecules,
matching the prior's stated 163-349 molecule range.

Cost arithmetic (DERIVED in the plan record), A100 proxy throughput 267.5 ns/day:
  ns_per_candidate = 3 equil + 3 replicas x 5 ns = 18 ns
  usd_per_candidate = 18 / 267.5 * 24 * 1.99 = 3.214 USD
  usd_anchor = 112 / 267.5 * 24 * 1.99 = 20.0 USD
  usd_100 = 100 * 3.214 = 321.4 USD
  usd_300_extra = 200 * 3.214 = 642.8 USD
  usd_storage = 2 * 0.2 / 12 = 0.033 USD
  total_stated ~= 984.2 USD (cap 1000)
"""
print("n_carbons atoms_per_molecule molecules_per_15000atoms")
for n in [4, 6, 8, 10, 14, 18, 22, 26, 30]:
    atoms = 3 * n + 2
    mol = 15000 / atoms
    print(f"{n:>10} {atoms:>19} {mol:>27.1f}")
