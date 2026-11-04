# Tolerance rule for the main comparison's margins (science step s27, sealed before any fixture result)

This rule turns the fixture run's recorded values (`fixture_design.json` in this folder, run by m5 in comparison mode) and the analytic budget (`ASSESSMENT.md` §B) into the margins of the main comparison. It is fixed now. No constant, condition or step below may change after any fixture or main result exists. A later step applies it mechanically: every quantity is read from named files, and every decision is a comparison of numbers.

## 0. Names

**Main comparison.** These are s13's `FINAL.json` K1–K3 and K6/K7 (A1 against A0, and A2 against A1) on the four seed cases.
- Main K1 has two parts: transform identity (the card's exact criterion) and reconstructed coordinates within `eps_xyz`.
- Main K2 compares scores within `atol + rtol·max(|a|,|b|)`.
- Main K3 compares per-model DockQ within `eps_eval`.
- Main K6/K7 use the margin `0.01 + 2·eps_eval` (PC:29).

**Fixture run arms.** In `fixture_design.json`:
- F-A0 is main A0 (CPU standard);
- F-A1 is main A1 (GPU standard);
- F-A2 runs F-A0's commands again;
- F-A3 runs F-A1's commands again.

**Fixture comparisons.** These are the design's ids K1–K12, written F-K1 … F-K12 here so they are not confused with the main K ids. Every one is `exact`. The scorer records for each (fixture, replicate) pair: `agrees` (byte identity of the selected content), `missing`, `max_abs_error` and `max_rel_error`. The errors are computed over the parsed numbers, with rel = |a−b| / max(|a|,|b|) (`dut/pipeline/m5/score_comparison.py:469–504`).

| output | cross: F-A1 vs F-A0 | CPU self: F-A2 vs F-A0 | GPU self: F-A3 vs F-A1 |
|---|---|---|---|
| transforms | F-K1 | F-K2 | F-K3 |
| scores | F-K4 | F-K5 | F-K6 |
| coords | F-K7 | F-K8 | F-K9 |
| dockq | F-K10 | F-K11 | F-K12 |

For each output row, `t(n)` is the transforms comparison of the same arm pair:
- t(7) = t(10) = 1;
- t(8) = t(11) = 2;
- t(9) = t(12) = 3.

**Files.** All are in the fixture run's folder:
- `S` = `control/C/comparison_scored.json`, or the run's `C/comparison_scored.json` wherever the run keeps `C/`;
- `O(arm, f, r)` = the fetched `A/results/evaluate/comparison/r<r>/<arm>/<f>/out/docking.out`;
- `Y` = `A/results/evaluate/comparison_compute.json`.

**Pairs.** `pairs(n, f)` is the `pairs` list of the row with `input == f` of comparison F-Kn in `S`. A pair is *present* when `missing` is false. The fixtures are f1a19, f1dtd, f1glj and f1ht8.

**Constants (all fixed now).**

| symbol | value | basis |
|---|---|---|
| u | 2^-24 | IEEE-754 binary32 unit roundoff. Both arms' FFTs are single precision: `-lfftw3f` on the CPU and cuFFT with `-use_fast_math` on the GPU (`science/s06/CALIBRATION_BRIEF.md:361–369`). |
| k | 2 | DESIGN. Headroom from the maximum over the fixture sample (4 fixtures × 6 replicates × 50 values per output) to new inputs. |
| r_floor | 1e-6 | ≈ 17u. This covers two independent binary32 roundings plus a few operations. Below it, a relative tolerance is not resolvable in single precision. |
| xyz_unit | 0.001 Å | One unit in the last place of PDB coordinates (%8.3f). |
| e_floor | 0.001 | DESIGN. The smallest DockQ difference the study reports (three decimals). |
| e_ceiling | 0.01 | DESIGN. This equals the card's K6/K7 quality margin (PC:29, 270–274). An evaluator that disagrees with itself on identical models by more than the study's quality margin cannot support K6/K7. |
| A_rel(N) | (3·log2(N³) + 1) · 5u · N^1.5 | A worst-case relative error of one correlation peak from three single-precision FFTs on an N³ grid (`ASSESSMENT.md` §B, source 1). |
| m_q | 0.01 | The card's DESIGN quality margin for K6/K7 (PC:29), used unchanged. |

**Rounding.** `up2(x)` is the smallest number of the form m·10^e (m an integer from 10 to 99, e an integer) that is ≥ x. Every margin is reported as `up2` of its formula, except `atol` and `xyz_unit`, which are exact powers of ten.

## 1. Validity and completeness (applied first)

- **V0.** `S` exists, and its `comparison_sha256` equals the run's `C/comparison_seal.json`. The run's evaluate stage is PASS.
  - If V0 fails, every margin M2–M6 is **indefensible** with reason `fixture_run_failed`. M1 keeps its exact criterion, and its flags are `unknown`.
- **Z.** For every n in 1..12 and every fixture f, `pairs(n, f)` holds at least 4 present pairs.
  - If Z fails, M2–M6 are **indefensible** with reason `fixture_incomplete`. M1's flags are computed on the present pairs and marked `incomplete`.

## 2. The margins

### M1: main K1, transform identity (exact; no tolerance)
- **Margin.** `null`, with comparator `exact`. The card seals exact ranked rotation/translation identity, including rank 1 and cutoff membership, and "Tie mismatch fails this strict gate" (PC:58). The card also says "any relaxed policy requires new prospective plan" (PC:66). The fixture run derives no tolerance here.
- **Flags** (always reported):
  - `X_T` = some present F-K1 pair has `agrees` false;
  - `C_T` = the same for F-K2;
  - `G_T` = the same for F-K3.
- **Use in the main report.** If `G_T` is true, the main report must state that GPU-standard transforms were not reproducible against themselves on disjoint fixtures. A main K1 "not supported" then cannot be attributed to CPU/GPU disagreement alone.
- M1 is a sealed criterion, not a derived tolerance, so it has no defensibility test.

### M2: main K1, coordinates, `eps_xyz` (abs, Å)
1. **Qualifying pairs.** Q = the present coords pairs (n ∈ {7,8,9}, f, r) whose pair (t(n), f, r) is present with `agrees` true.
2. **Count mismatch.** If any pair in Q has `agrees` false and `max_abs_error` null, the margin is **indefensible** with reason `coords_count_mismatch`.
3. **CPU baseline.** If any fixture has fewer than 4 F-K8 pairs in Q, the margin is **indefensible** with reason `no_cpu_self_baseline`.
4. **Measured value.** Mxyz = the maximum `max_abs_error` over Q, with a pair that agrees counting 0.
5. **Margin.** `eps_xyz = up2(max(xyz_unit, k·Mxyz))`.
6. **Defensible iff** steps 2–3 pass and Mxyz ≤ xyz_unit. Otherwise it is **indefensible** with reason `reconstruction_not_deterministic`.

### M3: main K2, scores, `{abs: atol, rel: rtol}`
1. **Print resolution.**
   - d = the maximum number of digits after the decimal point among the last-field tokens of the 7-field rows of every present `O(A0, f, r)`. d is 0 if no token has a point.
   - `atol = 10^-d`.
2. **Grid size.** N_f = `int(float(t))`, where t is the first whitespace-separated token of the first line of `O(A0, f, r_min)`, and r_min is the lowest replicate whose file exists.
3. **Count mismatch.** If any present pair of F-K4, F-K5 or F-K6 has `agrees` false and `max_rel_error` null, the margin is **indefensible** with reason `score_count_mismatch`.
4. **Per-fixture maxima.** For each f:
   - MRx_f = the maximum `max_rel_error` over the present F-K4 pairs of f;
   - MRc_f = the same over F-K5;
   - MRg_f = the same over F-K6.
   - A pair that agrees counts 0.
   - MR = the maximum of all of them.
5. **Margin.** `rtol = up2(max(k·MR, r_floor))`.
6. **Defensible iff** step 3 passes and, for every fixture f, max(MRx_f, MRc_f, MRg_f) ≤ A_rel(N_f). Otherwise it is **indefensible** with reason `score_difference_exceeds_analytic_bound`.

### M4: main K3, DockQ, `eps_eval` (abs)
1. **Qualifying pairs.** Q_e = the present dockq pairs (n ∈ {10,11,12}, f, r) whose pair (t(n), f, r) is present with `agrees` true.
2. **Count mismatch.** If any pair in Q_e has `agrees` false and `max_abs_error` null, the margin is **indefensible** with reason `dockq_count_mismatch`.
3. **CPU baseline.** If any fixture has fewer than 4 F-K11 pairs in Q_e, the margin is **indefensible** with reason `no_cpu_self_baseline`.
4. **Measured value.** Me = the maximum `max_abs_error` over Q_e, with a pair that agrees counting 0.
5. **Margin.** `eps_eval = up2(max(e_floor, k·Me))`.
6. **Defensible iff** steps 2–3 pass and eps_eval ≤ e_ceiling. Otherwise it is **indefensible** with reason `evaluator_not_repeatable`.

### M5 and M6: main K6 (rank-1 DockQ) and main K7 (best-of-50 DockQ), `{abs: m_q + 2·eps_eval}`
- The margin is `m_q + 2·eps_eval`.
- It is defensible iff M4 is defensible. Otherwise it is **indefensible** with reason `eps_eval_indefensible`.

## 3. Applying the margins to a main run (no judgment)

1. **Carrying the margins.** The science step that writes the main agreement design copies the following into the main comparisons' `margin` fields, unchanged:
   - `eps_xyz` → main K1 coords, `elementwise_abs`;
   - `{atol, rtol}` → main K2, `elementwise_abs_plus_rel_max`;
   - `eps_eval` → main K3, `elementwise_abs`;
   - `m_q + 2·eps_eval` → main K6/K7.
2. **Matching definitions.** The main design reuses, byte for byte:
   - the four outputs (`name`, `format`, `select`);
   - F-A0's and F-A1's commands and `env` for main A0 and A1, with the main inputs' prepared paths in place of the fixtures';
   - the evaluator `spec`, apart from the private data's source.
3. **Indefensible margins.** For each indefensible margin, the main comparison still records the output with comparator `exact`, so its errors are recorded. The report states "no defensible tolerance (reason …)" and claims neither agreement nor disagreement for that comparison. Whether dependent comparisons proceed without it is the owner's decision (`ASSESSMENT.md` §E).
4. **Software and hardware identity.** After the main run, the later step checks the following against the fixture run's `Y.system`. If any check fails, every margin is reported as "not applicable to this main run (software or hardware differs from the fixture run)", and the outcomes are recorded unchanged.
   - (a) `executables` for megadock (A0), megadock-gpu (A1) and the evaluator have the same `sha256`, and the same set of library (`name`, `sha256`) rows;
   - (b) `driver_version` and `cuda_version` are equal;
   - (c) the GPU `name` is equal.
5. **Grid size disclosure.** After the main run, if any main input's grid N (the first token of A0's `docking.out`) exceeds max_f N_f, the report states that the score margin was extrapolated in grid size. The margin is still applied.

## 4. What this rule does not do
- It never reads an output of the main inputs.
- It never uses the main arms' differences.
- It never widens a margin after a main result.
- It does not validate the evaluator's absolute accuracy against an independent DockQ implementation, which the card's "independent DockQ-component checker" (PC:59) asks for. No published arm on this route provides one, so that uncertainty is kept and stated (`ASSESSMENT.md` §B, source 9).
