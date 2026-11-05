# s30 assessment: run9 fixture results, s27's rule applied, the main comparison (2026-11-05)

**Scope.** Offline: no network, no box, no git, no credentials. I wrote only into `science/s30/`. Bash was denied, so I read every file with the file tools and did all arithmetic by hand from quoted values.

**What I read:**
- s29 (assessment, design, predictions);
- s27 `TOLERANCE_RULE.md`;
- s13 `ASSESSMENT.md`/`FINAL.json`, s15 `SHAPES.json`, s07 `ASSESSMENT.md` (run6 walls and tiers);
- `dut/pipeline/m5/SCHEMAS.md:115-203`;
- from run9: `control/comparison_scored.json`, `comparison_seal.json`, `stages/{reproduce,evaluate}.json`, `receipts/0008-comparison-users.json` and `0011-comparison.json`, `agent/results/evaluate/comparison_compute.json`, the 24 fetched A0 `docking.out` files, the sealed `agent/harness/fetch_private.sh` and `evaluate.sh`, and `operator/OPERATOR_TAKEAWAY.md`.

For s01–s12 and s14–s26 I relied on the summaries that s13, s27 and s29 carry.

Below, R9 = `experiments/blind-02/m5/run9`, S = `R9/control/comparison_scored.json` and Y = `R9/agent/results/evaluate/comparison_compute.json`.

**Verdict:**
- run9 is complete and valid.
- s27's rule, applied unchanged, makes all four derived margins defensible: eps_xyz 0.001 Å; atol 0.01 with rtol 0.0023; eps_eval 0.001; K6/K7 margin 0.012.
- The main comparison can be expressed in the contract and fits under USD 20 on any box type.
- It cannot be launched blind, because the sealed hardware-identity clause (rule §3 step 4) conflicts with the hardware of K5's sealed references. I stop with **`needs_owner`** (§D).

## A. What run9 recorded

**Stages:**
- reproduce PASS, 464.4 s (`R9/control/stages/reproduce.json:1`);
- evaluate PASS, 3,978.5 s, gpu_s 76.52 (`stages/evaluate.json:1`);
- `0008-comparison-users` rc 0, 29 s (`receipts/0008-comparison-users.json:1`).

S's `comparison_sha256` `f8379819…0086` equals `control/comparison_seal.json:2`.

**Box** (Y `system`, `allocation`; Y:1300-1312, 1564-1571):
- `gpu_1x_a100_sxm4`, NVIDIA A100-SXM4-40GB, driver 570.148.08, CUDA 12.8;
- AMD EPYC 7J13, 30 logical CPUs;
- USD 1.99/h. The allocation figure written is 1.338 h ≈ USD 2.66, non-final.

**Executables** (Y:1314-1538):
- megadock `4b85db6e…` (the same CPU hash as run4 and run6);
- megadock-gpu `52e2d705…` (run6's H100 build was `a8375a2a…`, `s07/ASSESSMENT.md:72`);
- evaluator python `06dbd62e…`, pinder `0.0.0+gebeb28a2`.

**Invocation status.**
- Y lists 96 invocations, 24 per arm (Y:1252-1292). Each arm covers 4 fixtures × replicate rounds 1-6, with warmup 0.
- The keys `"status": "ok"` and `"eval_status": "ok"` together occur 192 times. No row has `failed`, `timeout`, `not_run` or `invalid` (grep, 0 matches).
- So every (arm, input, round) is ok with an ok evaluator.

**Outputs with values.**
- S has 12 comparisons × 4 fixtures, each with `n` 6 and `n_missing` 0.
- No pair has `missing` true, and no error field is null (grep, 0 matches).
- All 288 pairs are present: 240 have `agrees` true and 48 have `agrees` false.
- All four outputs (transforms, scores, coords, dockq) have values in every invocation.

**Self-agreement and arm-to-arm differences** (F-K ids as in s27 §0):

| output | cross F-A1 vs F-A0 | CPU self F-A2 vs F-A0 | GPU self F-A3 vs F-A1 |
|---|---|---|---|
| transforms | F-K1 24/24 identical | F-K2 24/24 | F-K3 24/24 |
| scores | F-K4 **0/24** | F-K5 24/24 | F-K6 **0/24** |
| coords | F-K7 24/24 | F-K8 24/24 | F-K9 24/24 |
| dockq | F-K10 24/24 | F-K11 24/24 | F-K12 24/24 |

Score differences, max_abs / max_rel per pair (S:738-952 for F-K4, S:1214-1428 for F-K6):

| fixture | F-K4 (cross) | F-K6 (GPU self) |
|---|---|---|
| f1a19 | 0.02-0.03 / 7.03e-6 to 8.92e-6 | 0.02 / 5.95e-6 to 7.05e-6 |
| f1dtd | 0.40 / 1.1174e-4, all six | 0.01-0.02 / 2.96e-6 to 5.99e-6 |
| f1glj | 5.01 / 1.13258e-3, all six | 0.02-0.03 / 4.95e-6 to 7.39e-6 in r1-r5; **r6: 4.98 / 1.12581e-3** |
| f1ht8 | 0.57 / 1.2813e-4 in r1-r5; r6: 0.26 / 6.236e-5 | 0.02-0.05 / ≤ 1.20e-5 in r1-r5; **r6: 0.57 / 1.2813e-4** |

Reading of this table (no rule applied):
- GPU transforms, ranks, reconstructed coordinates and DockQ were byte-identical against the CPU and against themselves.
- Only the printed scores differ.
- In two replicate-6 pairs, the GPU's own run-to-run score difference reached the size of the CPU/GPU difference.
- This is the same non-reproducibility run6 saw in GPU `docking.out` hashes (`s07/ASSESSMENT.md:117`), now located in the score field.

**Isolation.** I see no sign of interference:
- the users step passed;
- CPU self-agreement is byte-exact in 96/96 pairs;
- GPU deviations are confined to scores, as run6 predicted.

So `isolation_concern` is `none`.

**Walls of the parts** (Y rows and Y:1252-1298):
- Arm-part totals: A0 311.8 s, A2 311.6 s (mean 13.0 s), A1 79.2 s, A3 79.1 s (mean 3.3 s).
- Per-fixture arm walls: A0 2.75 s (f1a19), 10.8 s (f1dtd), 14.4 s (f1glj), 24.0 s (f1ht8); A1 2.66 s (f1dtd), 3.51 s (f1glj), 5.25 s (f1ht8).
- Evaluator walls: 2.07-7.23 s, total 424.0 s.
- GPU busy: A1 41.5 s, A3 40.7 s.
- All parts sum to 1,205.7 s over 96 invocations (12.6 s each). The evaluate stage took 3,978.5 s, about 41.4 s per invocation, so about 29 s per invocation was spent outside the parts. Example: the first invocation's parts took 5.4 s against a 29 s `comparison` receipt (`receipts/0011-comparison.json:1`), plus the job receipt (median 7 s).

## B. s27's rule applied exactly as sealed

**V0 and Z hold:**
- V0: S exists, its sha256 equals the seal, and evaluate is PASS.
- Z: every F-K1 to F-K12 has 6 present pairs per fixture (≥ 4).

**M1 (main K1, transform identity): exact, no tolerance.**
- X_T = false (F-K1 24/24 agree).
- C_T = false (F-K2 24/24 agree).
- G_T = false (F-K3 24/24 agree).

**M2 (eps_xyz).**
- Q is all 72 coords pairs, because every paired transforms pair agrees. No pair in Q disagrees, so there is no count mismatch.
- F-K8 has 6 pairs per fixture in Q (≥ 4).
- Mxyz = 0, since every pair agrees.
- eps_xyz = up2(max(0.001, 2·0)) = **0.001 Å**.
- Defensible: Mxyz 0 ≤ 0.001.

**M3 (atol, rtol).**
- *Print resolution d.* In all 24 present `O(A0, f, r)`, the 7-field rows number 1,200 (50 per file). All 1,200 last-field tokens have exactly 2 decimals: a pattern ending `\.[0-9]{2}` matches 1,200 of 1,200 (e.g. `r1/A0/f1glj/out/docking.out:5`, `8131.88`). So d = 2 and **atol = 0.01**.
- *Grid size N_f* (first token of r1's file): f1a19 84, f1dtd 126, f1glj 144, f1ht8 154.
- *Count mismatch.* Every disagreeing F-K4/F-K6 pair has a numeric max_rel_error, so there is none.
- *Per-fixture maxima.* MRc_f = 0 for every fixture (F-K5 all agree).

  | fixture | MRx_f | MRg_f |
  |---|---|---|
  | f1a19 | 8.9188e-6 | 7.0475e-6 |
  | f1dtd | 1.11741e-4 | 5.9933e-6 |
  | f1glj | 1.132580e-3 | 1.125805e-3 |
  | f1ht8 | 1.28129e-4 | 1.28129e-4 |

  MR = 1.1325796e-3.
- *rtol* = up2(max(2 × 1.1325796e-3, 1e-6)) = up2(2.26516e-3) = **0.0023** (m 23, e −4; 0.0022 < 2.265e-3).
- *Analytic bound.* A_rel(N) = (9·log2 N + 1)·5u·N^1.5, with 5u = 2.98023e-7:
  - N 84: 58.531 × 769.87 × 5u = **0.01343**
  - N 126: 63.796 × 1414.35 × 5u = **0.02689**
  - N 144: 65.529 × 1728 × 5u = **0.03375**
  - N 154: 66.401 × 1911.09 × 5u = **0.03782**
- *Defensible.* Each fixture's maximum is at or below its bound: 8.92e-6 ≤ 0.01343, 1.117e-4 ≤ 0.02689, 1.1326e-3 ≤ 0.03375, 1.281e-4 ≤ 0.03782.

**M4 (eps_eval).**
- Q_e is all 72 dockq pairs. All agree, so there is no count mismatch.
- F-K11 has 6 pairs per fixture in Q_e.
- Me = 0, so eps_eval = up2(max(0.001, 0)) = **0.001**.
- Defensible: 0.001 ≤ e_ceiling 0.01.

**M5 and M6 (main K6/K7).** The margin is 0.01 + 2·0.001 = **0.012**, defensible because M4 is.

**Summary.**
- The rule applied to every margin, and every margin is defensible now. No margin keeps an "indefensible" uncertainty.
- Two uncertainties remain, both stated by the rule itself rather than by a margin, and both carry over to the main report:
  - §4: there is no independent check of DockQ's absolute accuracy.
  - §3 step 5: grid-size extrapolation is disclosed after the main run.
- **Condition for use:** under §3 step 4, these margins apply only to a main run whose megadock, megadock-gpu and evaluator sha256 values and library rows, driver/CUDA versions and GPU name equal run9's, as listed in §A.

## C. s29's predictions scored (`outcomes.json`)

| id | outcome | evidence |
|---|---|---|
| Q1 | true | `stages/reproduce.json`, `stages/evaluate.json` PASS; S exists |
| Q2 | true | `receipts/0008-comparison-users.json` rc 0 |
| Q3 | true | Y: 96 `eval_status` ok |
| Q4 | true | Y: 96 `status` ok, none other |
| Q5 | true | S: n 6, n_missing 0 in all 48 rows |
| Q6 | true | S: F-K2, F-K5, F-K8, F-K11 all agree |
| Q7 | true | S: F-K3 24/24 agree |
| Q8 | true | S: F-K1 24/24 agree |
| Q9 | **false** | S: F-K6 0/24 agree (S:1214-1428) |
| Q10 | true | §B M3 |
| Q11 | true | §B M2 |
| Q12 | true | §B M4 |
| Q13 | true | §B |
| Q14 | true | Y:1570 usd 2.663 (non-final value written) ≤ 12 |
| Q15 | **false** | Y:1565 `gpu_1x_a100_sxm4` |
| Q16 | true | the largest Y `eval_wall_s` is 7.227 s ≤ 60 |
| Q17 | true | `stages/evaluate.json` wall_s 3,978.5 ≤ 14,400 |
| Q18 | **false** | S: F-K4 f1glj max_rel_error 1.1326e-3 > 1e-4 (S:858) |
| Q19 | true | `R9/agent/harness/fetch_private.sh:3-14` carries its data inline. `evaluate.sh:4-38` writes `score.py` under `CMP_EVAL_OUT` and runs the venv interpreter on it. Neither reads a file under `harness/`. The scorer checked these bytes against `arms_seal.json` (`SCHEMAS.md:190`) and wrote S. |

Result: 19 of 19 resolved, 16 true and 3 false.

## D. Next test: the main comparison, pending one owner decision

**What the main design would be.** The design is fixed by s13, s15 and s27 §3. Every number below is sealed in the design and appears nowhere in the view:
- **Arms:**
  - A0 and A1: F-A0's and F-A1's commands and `env` byte for byte, with the seed cases' prepared paths.
  - A2: A1 with the seed's documented dense rotation set (54,000 rotations; argv as run6 used it, `science/s06/CALIBRATION_BRIEF.md:387-391`).
- **Inputs:** the four seed cases 1aua, 1ax2, 1dv1, 1nr5.
- **Outputs:** run9's four outputs byte for byte.
- **Evaluator:** run9's `spec` byte for byte, except for the private data's reference names.
- **Metrics:** `wall` (trusted_wall); rank-1 DockQ and best-of-50 DockQ (sealed_extraction from `eval/dockq.json`, reduce `first` and `max`, expect_count 50).
- **Comparisons:**
  - K1 transforms `exact`.
  - K2 coords `{abs 0.001}`.
  - K3 scores `{abs 0.01, rel 0.0023}`.
  - K4 dockq `{abs 0.001}`, all A1 vs A0, per_input_all.
  - K5: A1 vs A0 wall, `ratio_at_least` 1.05, strict, pooled_mean, bootstrap 0.95, given K1-K4.
  - K6-K8: A2 vs reference, run6's tiers 1/2/3 (`s07/ASSESSMENT.md:56-59`), non_inferiority lower_better, per_input_each.
  - K9 (rank-1) and K10 (best-of-50): A2 vs A1, superiority two_sided, unpaired, all_pairs, `{abs 0.012}`, given K1-K4.
- **Sizing:** 10 comparisons; `replicates` 7 and `warmup` 1 (the card's 7 blocks plus 1 warm-up, PC:30); `bootstrap_resamples` 10000; `timeout_s` 300; `evaluator.timeout_s` 180; `budget_s` 12,600.

**The conflict that needs the owner.** Two sealed rules tie the main comparison to two different boxes:
1. **The margins need the A100.** Rule §3 step 4 makes every margin "not applicable" unless the GPU name, driver and executables equal run9's. That is an A100-SXM4-40GB with megadock-gpu `52e2d705…`, built per box compute capability; the H100 build was `a8375a2a…`.
2. **K5's tiers need the H100.** K5's sealed reference tiers were frozen from run6's walls on a `gpu_1x_h100_pcie` box with a Xeon 8480+ CPU (`s07/ASSESSMENT.md:75`). The card requires common tiers on the same hardware (`s13/ASSESSMENT.md:65`).

No box satisfies both. The launcher picks the box type, and NEXT.json cannot pin it. run9 landed on an A100 only because no H100 was available. An unpinned launch therefore voids at least one part, and most likely the agreement margins on which K5 and K9/K10 are gated. Box pinning was raised as an owner decision in s28 §D and s29 §D and is still open. This is a decision, not a contract gap.

**Options:**
- **(b) Pin `gpu_1x_h100_pcie` (recommended).**
  - First repeat run9's fixture design unchanged on that box, with new order and bootstrap seeds only. s27's rule then derives the margins mechanically. run9's A100 result stays recorded as it is.
  - Then run the main comparison on the same box type.
  - This keeps every sealed reference (run6 tiers, run4/run6 walls) on one hardware frame.
  - Extra cost: about 1.3 h, about USD 4.2 expected (run9's 4,567 s total wall at USD 3.29/h); at most USD 16.1 (s29 §D worst case).
- **(a) Pin `gpu_1x_a100_sxm4`** and run the main comparison next with run9's margins. K5 then has no same-hardware tiers. Either:
  - (a1) keep run6's tiers, with K5 reported as cross-hardware;
  - (a2) first run a run6-style timing calibration on the A100 (about USD 2) and freeze A100 tiers by the card's formula (tier1 = 1.5·M_cpu and tier2 = 2·M_cpu, which reproduce `s07:56-59`; tier3 = 2·M_dense);
  - (a3) drop K5. That is a narrowing of the affordability part, which `NARROWING.md` would have to state.
- **(c) Launch unpinned** and accept §3 step 4 as sealed. I do not recommend this: it most likely spends the run without an agreement claim.

**Sizing of the main run.** Cost per invocation is about 36 s outside the parts (per the step brief: `comparison-job` median 7 s plus `comparison` overhead) plus the arm and evaluator walls. Arm walls come from run6 (`s07:38-41`): A0 9.0-14.5 s, A1 2.7-4.3 s, A2 16.2-21.9 s. Evaluator walls are 1.8-7.2 s (run4, run9).

The run is 3 arms × 4 cases × 8 rounds = 96 invocations:

| case | per invocation | evaluate | with pre/post (≈0.3 h) | H100 3.29 | A100 1.99 | A10 1.29 |
|---|---|---|---|---|---|---|
| expected | 36 + 11.7 + 2.5 ≈ 50 s | 4,820 s ≈ 1.34 h | ≈ 1.65 h | USD 5.4 | USD 3.3 | USD 2.1 |
| pessimistic (arms ×1.5, eval 7.2, overhead 45) | ≈ 70 s | 6,700 s ≈ 1.86 h | ≈ 2.2 h | USD 7.1 | USD 4.3 | — |
| A10 (GPU arms ×3) | ≈ 77 s | 7,360 s ≈ 2.05 h | ≈ 2.35 h | — | — | USD 3.0 |
| worst (budget exhausted) | — | 12,600 s = 3.5 h | ≈ 3.8 h | USD 12.5 | USD 7.6 | USD 4.9 |

How it holds on each box:
- Every case stays under 6 h and under USD 20 on every box type.
- `budget_s` 12,600 is below 19,800 and leaves 1.8× headroom over the pessimistic case.
- `timeout_s` 300 is at least 4.5× the largest arm wall expected, including dense on an A10.

**What each result would decide for the seed's question.**
- K1-K4 all supported: GPU and CPU agree within justified tolerances on the seed cases. Otherwise the agreement result is negative and recorded, and K5, K9 and K10 are void as `not_eligible`.
- K5 supported: the GPU workflow is at least 1.05× faster. Not supported: no acceleration claim.
- K6-K8: whether dense finishes within each tier, per case. A missed tier is "unavailable", never DockQ 0.
- K9/K10, per case: dense improves (sign higher), worsens (lower), shows no difference beyond 0.012 (not supported) or is unresolved (inconclusive), separately for rank-1 and best-of-50.

## E. Do the main runs fit the USD 88.90 left?

- **Option (b):** 88.90 − 16.1 (fixture run, worst) − 12.5 (main run, worst) = **USD 60.3** left. With expected costs: 88.90 − 4.2 − 5.4 = USD 79.3.
- **Option (a2):** 88.90 − 2 − 7.6 = USD 79.3.

So **yes**. The card's earlier USD 49.48 plan was a DESIGN timer estimate (`s13/ASSESSMENT.md:86`). The measured costs replace it, and the main run projects under the USD 20 approval line.

## F. Narrowing

Unchanged: no narrowing (`NARROWING.md`). Option (a3) would narrow the question and would have to be stated there.
