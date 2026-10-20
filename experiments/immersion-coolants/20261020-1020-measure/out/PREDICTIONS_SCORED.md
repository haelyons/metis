# Sealed predictions scored, measure run m3

Sealed before any agent, box build or box ran: `SEALED_PREDICTIONS.md` sha256
9d9bdf5cc68db6ed694cf0da2194e7729f4c8e31b4efd16c4f9b6f42343568a5 (out/SEALS.txt, first line). Scored against
`results_m3/out/` (launch 2) and `out/launch1/` on 2026-10-20 14:05Z. "Held" = the predicted event occurred.

| # | Prediction | p | Outcome | Measured | Brier term |
|---|---|---|---|---|---|
| P1 | The committed builder packs the box at 0.3 g/cm3 on the first try | 0.85 | held | exit 0 in 12 s (the one failed attempt was the operator's PATH, not the builder) | 0.0225 |
| P2 | The conda-forge LAMMPS CUDA build installs on the box within 15 min | 0.60 | did not occur | never attempted: the conda-forge CUDA builds have the GPU package off (build 2's finding); LAMMPS was compiled from source instead, in 115 s | 0.3600 |
| P3 | The production deck as written runs with the GPU package | 0.40 | held | E6 RUNS (the equilibration deck, not covered by P3, needed its load-balancing lines removed) | 0.3600 |
| P4 | E3 below 150 ns/day, gate fails (point 90, range 30 to 250) | 0.65 | held | 12.60 ns/day; below the stated range | 0.1225 |
| P5 | No-sampling variant between 150 and 400 ns/day | 0.55 | did not occur | 18.43 ns/day | 0.3025 |
| P6 | Density after NPT within 4% of 0.805 | 0.70 | held | 0.79503 (-1.24%) | 0.0900 |
| P7 | Sampling costs at least 30%: no-sampling / as-written >= 1.4 | 0.70 | held | 1.462 | 0.0900 |
| P8 | Card plan re-priced with the measured throughput exceeds USD 1,000 | 0.75 | held | USD 18,670.63 | 0.0625 |
| P9 | First launch completes with no halt | 0.40 | did not occur | the cost/time guard stopped launch 1 before equilibration | 0.1600 |

**Brier score: 1.570 / 9 = 0.174** (m1 0.177, m2 0.090). Nine resolved, none unresolved.

## Where the forecast was weakest

- P2 and P5 carried the same wrong picture: a conda-forge engine with the GPU package, running the pure MD at 150 to 400
  ns/day. The engine fact was in the coolant pilot's log and was missed; the pure-MD rate on one process is 18 ns/day,
  because bonds, angles, dihedrals and SHAKE for 11,250 atoms run on one CPU thread while the GPU does pair and k-space.
  Direction right (P4, P7, P8 held), magnitude wrong by 7x on the point estimate.
- P3 was under-confident: the GPU package accepted the per-atom centroid stress compute; what it refused was `fix
  balance` with `pppm/gpu`, in the equilibration deck.
