# Sealed predictions scored, measure run m2

Sealed before any agent ran: `SEALED_PREDICTIONS.md` sha256 169bb51e31dc9c25d2ae76a6c21e153f8c2522b9b46edceb8dde4df15c58032e
(out/SEALS.txt, first line). Scored against `results_m2/out/records/` and `results_m2/out/rows/` on 2026-10-20 10:05Z.
"Held" = the predicted event occurred; "did not occur" = it did not (a low forecast that did not occur is a good forecast).

| # | Prediction | p | Outcome | Measured | Brier term |
|---|---|---|---|---|---|
| P1 | nvcc present, kernels compile on launch 1 | 0.75 | held | /usr/bin/nvcc 12.8, compiled in 2 s with -arch=sm_80 | 0.0625 |
| P2 | E1 anchor passes (residuals <= 1e-10, references agree) | 0.80 | held | E1 PASS; I1 x3 PASS | 0.0400 |
| P3 | E2: card residual guess 1e-13 too pessimistic by > 10x | 0.65 | held | max relative residual 3.11e-16 (320x below the guess) | 0.1225 |
| P4 | E3 resolves if_lever by the card's rule | 0.95 | held | speedups 8.5 / 95.9 / 517.5 / 395.4 / 348.3; slope of ln(speedup) 0.256 > 0 | 0.0025 |
| P5 | E5: speedup at 2^24 >= 28 (point 150, range 30 to 1,000) | 0.85 | held | 348.3x (12.4x the card's proxy) | 0.0225 |
| P6 | E4: crossover at N = 1,024 | 0.75 | held | 1,024, labelled launch-bound (launch fraction 0.775 at 2^10) | 0.0625 |
| P7 | E7: PCR vs CPU dgtsv at 2^24 below 20x | 0.70 | held, thin | 416.7 ms / 21.8 ms = 19.1x | 0.0900 |
| P7b | ... below 2x | 0.20 | did not occur | 19.1x | 0.0400 |
| P8 | E6: PCR per-doubling growth 2^22 -> 2^24 at least 1.7x | 0.80 | held | g = 2.135 (4.79 ms -> 21.8 ms for 4x N): super-linear, "linear-like" | 0.0400 |
| P9 | E10: sweep under 20 min; "need 2 h" high by > 3x | 0.80 | held | 0.119 h = 7.1 min; 16.8x below the card's need | 0.0400 |
| P10 | E9: this PCR within 3x of cuSPARSE gtsv2_nopivot at 2^24 | 0.55 | did not occur | cuSPARSE 2.94 ms vs PCR 21.8 ms: 7.4x | 0.3025 |
| P11 | first launch completes with no halt | 0.50 | held | rc=0, 12 stages, 35 records, run_valid true | 0.2500 |

**Brier score: 1.075 / 12 = 0.090** (m1: 0.177). Twelve resolved, none unresolved.

## Where the forecast was weakest

- P10: the hand-written PCR is 7.4x slower than NVIDIA's hybrid at the top level and 2.4x at the bottom. The one-kernel-per-round
  PCR over global memory is far from the library's shared-memory hybrid; the card's E3 speedup is against the card's own
  baseline and would be about 2,580x with cuSPARSE as the parallel arm.
- P11 and P1: the toolchain risk did not materialise this time (nvcc, scipy, cuSPARSE all on the image).
- P7 held by 0.9x of margin: the practical sequential floor (one CPU core, OpenBLAS LAPACK dgtsv) is 19x slower than this PCR at
  2^24, 0.6x at 2^10 (the CPU wins below about 2^12).
