# Sealed predictions, measure run m2 (written 2026-10-20 08:5x UTC, before any agent or box ran)

Author: the operating session (Claude). Not shown to the triage, gate, build or post agents. Hash in out/SEALS.txt.

Card under test: P arm, R1 · physical · "Cyclic reduction (PCR)", `expected: if_lever`, decision rule "lever if median
PCR time < median Thomas time at n_max = 2^24 by at least 2x, and the PCR/Thomas speedup grows with N".

| # | Prediction | Probability |
|---|---|---|
| P1 | The box has nvcc (CUDA toolkit) and the kernels compile on the first launch | 0.75 |
| P2 | E1 anchor passes: Thomas and PCR relative residuals <= 1e-10 at N = 2^10 and 2^14 against cuSPARSE and scipy | 0.80 |
| P3 | E2: the card's residual guess 1e-13 is too pessimistic by more than 10x (measured max relative residual below 1e-14) | 0.65 |
| P4 | E3: the card's decision rule resolves if_lever (PCR >= 2x faster than the one-thread GPU Thomas at 2^24, speedup growing with N) | 0.95 |
| P5 | E5: PCR/Thomas speedup at 2^24 is at least 28 (the card's proxy). Point estimate 150x, range 30 to 1,000x | 0.85 |
| P6 | E4: crossover at the first level: PCR already beats one-thread GPU Thomas at N = 1,024 (card guess holds) | 0.75 |
| P7 | E7: against the CPU LAPACK dgtsv floor at N = 2^24, PCR's speedup is below 20x | 0.70 |
| P7b | ... and below 2x (the card's own threshold would say if_not against that baseline) | 0.20 |
| P8 | E6: PCR wall-clock is not log-like at the top: per-doubling growth between 2^22 and 2^24 is at least 1.7x (work-bound, not depth-bound) | 0.80 |
| P9 | E10: the whole on-box sweep (anchor plus all levels) takes under 20 minutes; the card's "need 2 h" is high by more than 3x | 0.80 |
| P10 | E9: the hand-written PCR is within 3x of cuSPARSE gtsv2_nopivot at 2^24 | 0.55 |
| P11 | The run completes its first launch with no halt | 0.50 |

## Reasoning, in one paragraph

The card's baseline is one CUDA thread walking 2^24 dependent steps twice; at a few hundred cycles per step that is
seconds per solve. PCR touches all N equations in each of its 24 rounds, so on one GPU its time is bandwidth-bound:
tens of milliseconds at 2^24. The ratio is therefore large, and the card's rule is near-certain to say if_lever;
the rule cannot easily fail because its baseline is the slowest possible sequential arrangement, not the practical
one (a CPU core running LAPACK dgtsv, about 0.1 s at 2^24). The interesting measured facts are elsewhere: PCR's time
grows about linearly with N at the top (depth is log N but work is N log N and the GPU's width is finite), which
contradicts the card's if_lever prose "wall-clock grows like log2(N)" even while the decision rule holds; and the CPU
floor shows what the restructure buys against the sequential alternative anyone would use.

## What would change my mind

P4 fails only if the Thomas kernel is written as something other than one thread per system. P8 fails if the GPU is
far from saturated at 2^22 (it is not: 4 million threads per round). P7 fails if dgtsv on the box's CPU is slow (an
old MKL-less LAPACK at over 1 s for 2^24 would push PCR past 20x). P1 is the P9 analogue from m1: a toolchain
assumption about the Lambda image.
