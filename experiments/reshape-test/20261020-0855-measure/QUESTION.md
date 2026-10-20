# QUESTION: does the PCR card's decision rule resolve to if_lever on its own hardware, and do its measured-later numbers hold?

## The question

The card "Cyclic reduction (PCR) · Parallel cyclic reduction" (P arm, planted root) predicts that feeding a GPU's width
to one tridiagonal Newton correction shortens its wall-clock (`expected: if_lever`). Its decision rule: "Lever if
median PCR time < median Thomas time at n_max = 2^24 by at least 2x, and the PCR/Thomas speedup grows with N;
otherwise not." Thomas is the card's sequential baseline: a hand-written CUDA kernel, one thread per system, forward
elimination then back substitution. PCR is parallel cyclic reduction, log2(N) rounds, one thread per equation per
round. **Time both on one rented A100 SXM4 40 GB box at N in {2^10, 2^14, 2^18, 2^22, 2^24}, five seeds each, after
both match two independent references at N = 2^10 and 2^14, and read the card's rule.** Also read the card's three
measured-later numbers: `res_measured` (GUESS 1e-13), `crossover_n` (GUESS 1,024), `speedup_at_nmax` (PROXY 28), and its
cost line's "need 2 h".

Both outcomes are informative. if_lever confirms the card as written. if_not refutes it. A guess wrong by more than
10x (residual) or a crossover above the first level is a finding about the pipeline's estimates whichever way the
decision falls. Two further readings are reported beside the card's rule and do not decide it: the shape of PCR's
time against N (the card's if_lever sentence says "grows like log2(N)"), and the card's rule re-read against the CPU
floor the card itself names (LAPACK dgtsv on the instance CPU).

## Committed data

No file is downloaded. The systems are generated on the box by a committed rule:

| Item | Rule |
|---|---|
| Matrix | tridiagonal, N equations; off-diagonals a_i, c_i of unit magnitude with seed-fixed random signs; diagonal b_i = 3 (so |b| - |a| - |c| = 1, the card's "diagonal dominance margin 1.0"); float64 |
| Right-hand side | d_i standard normal, float64 |
| Generator | numpy `default_rng(seed)`, seeds 0, 1, 2, 3, 4 (one per timing repeat); the anchor uses seed 0 |
| Record | every generated system is reproducible from (N, seed); the first 8 values of a, b, c, d and the sha256 of each array are written per row |

The card record itself is the committed input: `../20261019-2344-tree/out/result.json`
sha256 `48ac464c98a73069aab7af8efbd53021ca5439a193af666a2e1ac6d0d32ac6ae` (PLAN in
`out/agents/0008-R1_physical_top_producer/reply.txt`, sha256 `5edcb633490ee446d7a77a8f32cf246efae31aab79919fe6b21ac4f6aa411b33`).

## Anchor

The card's own `p1_anchor`: at N = 2^10 and 2^14, the hand-written Thomas and PCR solutions must each have relative
residual ||A x - d||_2 / ||d||_2 **<= 1e-10** (the card's `res_tol`), computed in float64 on the CPU from the generated
arrays, and must agree with two independent references on the same systems: NVIDIA cuSPARSE `gtsv2_nopivot` on the GPU
and scipy `solve_banded` (LAPACK) on the CPU, each to **< 1e-8** relative difference in x (the card's `checks`). The two
references must also agree with each other to < 1e-8 (the card's fourth check; validates the references).

Out of band on either solver: that solver's timing rows are "descriptive only; anchor failed" and the card's rule is
not read (the card's own gate text applies: "Fix the kernels and re-run the anchor before starting the sweep"; no
kernel is fixed mid-run).

## What would refute each claim

- Claim A (card GUESS `res_measured = 1e-13`): the measured max relative residual over the anchor levels and both
  hand-written solvers. Holds if within [1e-14, 1e-12]; refuted outside (10x either way).
- Claim B (card GUESS `crossover_n = 1,024`, "PCR should already win at the smallest level"): the crossover is the
  smallest sweep level at which the lower quartile of the PCR/Thomas speedup over the five seeds exceeds 1 (the card's
  noise rule). Holds if the crossover is 2^10; refuted if it is higher or does not occur.
- Claim C (card `expected: if_lever`): refuted if, at N = 2^24, median Thomas ms / median PCR ms < 2, OR the speedup
  does not grow with N. "Grows with N" is read as: speedup at 2^24 > speedup at 2^10 AND the least-squares slope of
  log(speedup) against log2(N) over the five levels is positive. The noise rule: the lower quartile of the speedup at
  2^24 must also exceed 2 for the lever reading to be "a real difference" in the card's words; if the median passes and
  the lower quartile does not, the reading is if_lever with the label "within noise".
- Claim D (card PROXY `speedup_at_nmax = 28`, from a 2009 GTX 280 against CPU LAPACK): the measured speedup at 2^24.
  Holds if within [9.3, 84] (3x either way); refuted outside. A PROXY is cited for a different setting; this is a
  report on how far it travelled, not a card prediction.
- Claim E (card cost line: "6 h time box; need 2 h" for anchor plus sweep): the on-box wall-clock from the first anchor
  solve to the last sweep row. Holds if within [0.67, 6] h; refuted if below 0.67 h (the plan over-bought by more than
  3x) or above 6 h.
- Shape reading (report only; tests the card's if_lever sentence "wall-clock grows like log2(N)", not its rule): the
  per-doubling growth factor g = (median PCR ms at 2^24 / median PCR ms at 2^22)^(1/2). "log-like" if g <= 1.15,
  "linear-like" if g >= 1.7, "between" otherwise.
- CPU-floor reading (report only): the card's rule with median scipy `dgtsv` ms on the box's CPU in place of the
  one-thread GPU Thomas. Reported as if_lever or if_not under that baseline, with the speedup at each level.
- Copies reading (report only; the card's `baseline_copies` check): K independent systems solved at once by the
  Thomas kernel, one thread per system, K = min(256, 2^28 / N). The card's claim holds if the batched solve's time is
  within [0.9, 3] x the single-system time at every level (width raises throughput, one system's latency stays O(N)).
- cuSPARSE reading (report only): median cuSPARSE `gtsv2_nopivot` ms at each level and its ratio to the hand-written PCR.

## Scope

One GPU (A100 SXM4 40 GB, the card's hardware, at the card's rate of USD 1.99/h), one CPU core for the floor, float64,
one right-hand side, scalar tridiagonal systems with the generated structure. The card's phases `p1_anchor` and
`p2_sweep` only. Out of scope: block-tridiagonal systems (`p3_block`), multi-GPU PCR (`p4_multi`), the parallel-in-time
Newton loop the solve would sit inside, non-dominant or ill-conditioned matrices, float32, multiple right-hand sides,
any tuning of the Thomas kernel beyond the card's "one thread per system" with the recurrence kept in registers.

## Declared construct risks

- The card's sequential baseline is one GPU thread. Against it, any parallel method wins at large N by construction;
  the rule tests whether PCR is slower than the slowest arrangement of the sequential algorithm, not whether it is
  faster than the sequential algorithm as anyone would run it. The CPU-floor reading is added so the reader can see the
  difference; it does not change the card's verdict.
- The Thomas kernel's constant factor depends on how the builder writes it (register use, loads per step). The card
  says "tuned with a register-cached recurrence and #pragma unroll"; the build keeps the recurrence in registers and
  reads each input once per step. Stated as "the one-thread Thomas this build wrote", not "the fastest one-thread Thomas".
- Timing a sub-millisecond solve needs a block of back-to-back solves; the per-solve time then includes no host
  synchronisation but does include kernel-launch gaps. Blocks are sized so each timed block is at least 50 ms; the
  block size is recorded per row.
- PCR's per-round kernels are the builder's; a different PCR (shared-memory tiling, hybrid with Thomas below a cutoff,
  as cuSPARSE does) would be faster. The cuSPARSE reading bounds how far this PCR is from NVIDIA's.
- The CPU floor is one core running LAPACK through scipy 1.8.0 as the image ships it (OpenBLAS or MKL unknown until
  read on the box; recorded). It is a floor for "sequential on this box", not the best CPU.

## How the card maps onto this record

| Card (PLAN) field | Here |
|---|---|
| `anchor`, `checks` 1-4, `phases[p1_anchor].gate` | Anchor section; Claim A |
| `predictions.decision_rule`, `expected`, `noise_rule` | Claim C |
| `numbers[res_measured]` GUESS, `measured_by: p1_anchor` | Claim A |
| `numbers[crossover_n]` GUESS, `measured_by: p2_sweep` | Claim B |
| `numbers[speedup_at_nmax]` PROXY, `measured_by: p2_sweep` | Claim D |
| `cost.lines[l_anchor_sweep]` hours 6, need 2 | Claim E |
| `predictions.if_lever` sentence ("grows like log2(N)"), `checks` 5 | Shape reading |
| `restructuring.baseline_sequential` ("MKL dgtsv on the instance CPU as a floor") | CPU-floor reading |
| `restructuring.baseline_copies`, arm a4, `checks` 6 | Copies reading |
| arm a3 (cuSPARSE as independent reference) | Anchor; cuSPARSE reading |
| `held_fixed` | Scope |
| `phases[p3_block]`, `phases[p4_multi]` | not run |
