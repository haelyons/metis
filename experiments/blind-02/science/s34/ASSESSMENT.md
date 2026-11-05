# s34 assessment: the main comparison run10, scored and checked (2026-11-05)

**Scope.** Offline: no network, no box, no git, no credentials. I wrote only into `science/s34/`. Python and jq were denied in this step, so every recomputation below uses values read with the file tools and arithmetic done by hand. I give the inputs of each sum so it can be checked.

**What I read:**
- the seed `m5/BRIEF.md`;
- s13 `FINAL.json` and `ASSESSMENT.md` (tiers, P4);
- s07 `ASSESSMENT.md:54-61, 99-107` (run6 tiers and rho);
- s27 `TOLERANCE_RULE.md`;
- s30 `ASSESSMENT.md`;
- s31 `ASSESSMENT.md` §A–§B4;
- s32 and s33 (design, brief, predictions, narrowing);
- `dut/pipeline/m5/SCHEMAS.md:115-203`;
- from run10: `args.json`, `control/{comparison.json (source fields), comparison_seal.json, comparison_scored.json, box.json, stages/evaluate.json, stages/reproduce.json, receipts/}`, `agent/results/evaluate/comparison_compute.json`, the A1/A2 `eval/dockq.json` files, the first lines of the r1 `docking.out` files, the A2 `log/cmd1.stdout` files, `agent/harness/{evaluate.sh, arms/A2.sh}` and `operator/OPERATOR_TAKEAWAY.md`;
- run9's `comparison_compute.json` `system` block (`m5/run9/agent/results/evaluate/comparison_compute.json:1301-1510`).

For s01–s06, s08–s12, s14–s26 and s28–s29 I relied on the summaries that s13, s27, s30 and s31 carry.

**Abbreviations.** R10 = `experiments/blind-02/m5/run10`, S = `R10/control/comparison_scored.json`, Y = `R10/agent/results/evaluate/comparison_compute.json`, F = `R10/agent/results/evaluate/comparison/`.

**Verdict:**
- run10 ran the sealed design completely. All 96 invocations and all 96 evaluator parts are ok, and the scorer's outcomes recompute.
- **Agreement at identical settings holds on all four cases.** GPU and CPU give identical ranked transforms, coordinates and DockQ, and scores differ by at most 3.56e-5 relative.
- **The GPU workflow is 2.35× faster than the CPU's**, with a 95% interval of [2.30, 2.40].
- **Dense sampling misses both CPU-derived budget tiers on every case and fits only tier 3.** These tiers were frozen on an H100 box (run6), so this result is cross-hardware.
- **Dense improves best-of-50 DockQ on all four cases.** Rank-1 DockQ is mixed: two cases gain, one shows no difference, and one (1nr5) loses 0.44.
- The software/hardware identity check of s27 §3 step 4 fails. The megadock-gpu binary differs from run9's, so every derived margin is labelled "not applicable to this main run".
- I stop with `no_justified_test` (§E).

## A. What run10 recorded

**Stages:**
- intake PASS;
- reproduce PASS, 394.8 s (`control/stages/reproduce.json:1`);
- profile, seal, propose and implement SKIPPED, as comparison mode prescribes (`SCHEMAS.md:159`);
- evaluate PASS, 4,430.4 s, gpu_s 647.6, USD 2.41 (`control/stages/evaluate.json:1`);
- takeaways PASS.

**Receipts:**
- `0008-comparison-users` has rc 0 and took 29 s (`receipts/0008-comparison-users.json:1`).
- `0202-comparison-private-remove` has rc 0 (`receipts/0202-…:1`).
- Receipts 0010–0201 are 96 `comparison-job` and 96 `comparison` commands.
- No receipt has a nonzero `rc`, `timed_out` true or `overrun` true (grep over `control/receipts/`: 0 matches).

**Box** (`control/box.json`; Y:1290-1302):
- `gpu_1x_a100_sxm4` at USD 1.99/h;
- NVIDIA A100-SXM4-40GB, driver 570.148.08, CUDA 12.8;
- AMD EPYC 7J13, 30 logical CPUs.

**Invocations by arm, input and round.**
- Y lists 96 rows: 3 arms × 4 inputs × (1 warm-up `w1` + 7 replicate rounds `r1`–`r7`). The 8 rounds are fetched under F.
- `"status": "ok"` and `"eval_status": "ok"` together occur 192 times in Y. That is every row, for both the arm part and the evaluator part.
- All 96 fetched `wrap.json` files contain `"status": "ok"` (grep count 96 of 96).
- Y `arms` rows: each arm has 28 replicate invocations (Y:1252-1282).
- No status is failed, timeout, invalid or not_run.

**The sealed design ran as sealed.**
- `control/comparison.json` records `source` = `science/s33/main_design.json` and `source_sha256` = `950309d1…8b9b`. That is the sha256 of s33's (and s32's) `main_design.json`, which I recomputed with `sha256sum`.
- `comparison_seal.json` gives `4d0229a5…5df5`, the sha256 of `control/comparison.json`, which I recomputed. S's `comparison_sha256` (S:2) is the same value.
- The run's brief `R10/brief/MAIN_BRIEF.md` has sha256 `80600032…7417`, equal to s33's.
- The scored comparisons appear in the design's order: K1, K8, K2, K3, K4, K5, K9, K10, K6, K7. Their margins and references are the design's:
  - K6/K7 `margin_value` is 0.012;
  - K4 `threshold` is 1.05;
  - the K5/K9/K10 references are run6's tiers (`comparison.json:600, 631, 662`).
- The rounds match the design: 7 replicates and 1 warm-up, with n = 7 per agreement unit and n = 49 (7 × 7 unpaired) per K6/K7 unit.
- A2 used the dense set. Every A2 log prints `# Set 54,000 rotational angles (6 degree)` (e.g. `F/r1/A2/1aua/log/cmd1.stdout:14`).

**Isolation: no concern.**
- The users step passed. It hash-checks the sealed harness against `arms_seal.json`, blocks the arm user's network and keeps the evaluator's private data out of the arm user's reach (`SCHEMAS.md:161-170`).
- The sealed `evaluate.sh` reads only `CMP_INPUT_SPEC`, the native under `CMP_PRIVATE` (checked by size and sha256) and `model_1.pdb`…`model_50.pdb` under `CMP_ARM_OUT`. Nothing it reads names the arm (`agent/harness/evaluate.sh:4-37`).
- The A2 adapter only checks that the prepared input files exist (`agent/harness/arms/A2.sh`).
- No result looks like leakage:
  - CPU and GPU outputs at identical settings are identical apart from score rounding;
  - every arm's DockQ array is constant over its 8 rounds;
  - the evaluator gave identical values to identical models of A0 and A1 (K3 max_abs_error 0.0).

## B. K1–K7 as scored in S, and my check

s13's ids map to the design's entries as in `s31/ASSESSMENT.md:100-111`:
- s13 K1 = design K1 (transforms) + K8 (coords);
- s13 K5 = design K5/K9/K10 (tiers 1/2/3).

**Margin applicability (s27 §3 step 4, applied as sealed).** I compared Y.system (Y:1290-1492) with run9's (`run9/…/comparison_compute.json:1301-1510`):
- **(a) executables:**
  - megadock (A0) sha256 `4b85db6e…e600` is equal in both runs.
  - The evaluator python `06dbd62e…44d7` is equal.
  - **megadock-gpu (A1, A2) differs: run10 `25311e42…7f4f` (Y:1345, 1407) against run9 `52e2d705…3c26` (run9:1355, 1454).** Both report version `9575280c…2616`, and their library rows have the same names and sha256s.
  - So (a) fails.
- (b) driver 570.148.08 and CUDA 12.8 are equal.
- (c) the GPU name is equal.

The rule says: "every margin is reported as 'not applicable to this main run (software or hardware differs from the fixture run)', and the outcomes are recorded unchanged." That applies to K8, K2, K3, K6 and K7 below. K1 (exact) and the K4 threshold are not derived margins (s31 §B4, `:212`). The likeliest reason is that megadock-gpu was rebuilt per box, but the records do not establish why the binary differs.

**Grid-size disclosure (§3 step 5).**
- The run's grids are N = 126 (1aua), 120 (1ax2), 140 (1dv1) and 140 (1nr5) (first line of `F/r1/A0/<case>/out/docking.out`).
- All are ≤ run9's largest fixture grid, 154 (s30 §B M3), so the score margin was not extrapolated in grid size.

| design id (s13 id) | outcome in S | per-input estimate [lo, hi] / errors | margin or threshold | label |
|---|---|---|---|---|
| K1 (K1 transforms) | **supported** | every one of the 28 pairs identical; max_abs 0.0 (S:5-268) | exact | – |
| K8 (K1 coords) | **supported** | 28/28 agree, max_abs_error 0.0 (S:270-534) | abs 0.001 Å | margin not applicable to this main run (software differs) |
| K2 (K2 scores) | **supported** | 28/28 agree. Max abs / rel per input: 1aua 0.04 / 1.056e-5; 1ax2 0.03 / 9.26e-6; 1dv1 0.04 / 1.08e-5; 1nr5 0.14 / 3.562e-5 (S:536-800) | abs 0.01 + rel 0.0023 | margin not applicable to this main run |
| K3 (K3 DockQ) | **supported** | 28/28 agree, max_abs_error 0.0 (S:802-1066) | abs 0.001 | margin not applicable to this main run |
| K4 (K4 workflow speed) | **supported** | ratio mean(A0)/mean(A1) 2.3482 [2.3033, 2.4013], n 7 (S:1068-1090) | > 1.05, strict | – (eligible: K1, K8, K2, K3 supported) |
| K5 (K5 tier 1) | per_input: **not_supported ×4** | A2 − tier, s: 1aua 12.478 [11.539, 13.684]; 1ax2 8.771 [8.116, 9.855]; 1dv1 9.311 [8.788, 10.133]; 1nr5 9.303 [8.821, 10.292] (S:1092-1156) | margin 0; tier1 17.330 / 16.152 / 25.509 / 25.413 s | cross-hardware (H100 tiers, A100 run) |
| K9 (K5 tier 2) | per_input: **not_supported ×4** | 1aua 6.701 [5.762, 7.907]; 1ax2 3.387 [2.732, 4.471]; 1dv1 0.808 [0.285, 1.630]; 1nr5 0.833 [0.351, 1.822] (S:1158-1222) | tier2 23.107 / 21.536 / 34.012 / 33.883 s | cross-hardware |
| K10 (K5 tier 3) | per_input: **supported ×4** | 1aua −10.728 [−11.667, −9.522]; 1ax2 −11.011 [−11.666, −9.927]; 1dv1 −14.068 [−14.591, −13.246]; 1nr5 −13.960 [−14.442, −12.971] (S:1224-1288) | tier3 40.536 / 35.934 / 48.888 / 48.676 s | cross-hardware |
| K6 (K6 rank-1 DockQ, A2 − A1) | per_input | 1aua −0.00141 **not_supported**; 1ax2 +0.01593 **supported, higher**; 1dv1 +0.08373 **supported, higher**; 1nr5 −0.43954 **supported, lower** (lo = hi everywhere, n 49; S:1290-1354) | abs 0.012 | margin not applicable to this main run |
| K7 (K7 best-of-50 DockQ, A2 − A1) | per_input: **supported, higher ×4** | 1aua +0.13925; 1ax2 +0.88502; 1dv1 +0.09726; 1nr5 +0.10742 (lo = hi; S:1356-1420) | abs 0.012 | margin not applicable to this main run |

- S totals: 28 supported, 9 not_supported, 0 inconclusive, 0 void (S:1423-1428).
- Every reason is null, so no unit was voided or made not_eligible.

**My check of the scorer (recomputed from Y and F; it agrees on every outcome I recomputed).**
- **K1 (spot check).** `F/r1/A0/1nr5/out/docking.out:5-12` and `F/r1/A1/1nr5/out/docking.out:5-12` have identical rotation/translation fields, and their scores differ by 0.00–0.06 (4776.35 against 4776.34, 4369.13 against 4369.19). This matches K1 agreement and K2's small score error.
  - I did not byte-compare all 28 pairs by hand. The scorer's all-zero errors agree with the constant DockQ arrays below.
- **K3.** A0's and A1's rank-1 DockQ are equal in every round on every case (grep of the first value of all 96 `eval/dockq.json`):
  - 1aua 0.005533357;
  - 1ax2 0.007395016;
  - 1dv1 0.739216597;
  - 1nr5 0.462499287.
- **K4.**
  - The ratio of means equals the ratio of the arm sums, because both arms have 28 replicate invocations. Y:1256-1270 gives (361.8015 + 111.3470) / (90.9593 + 110.5342) = 473.1485 / 201.4935 = **2.3482**, equal to S's estimate.
  - lo 2.303 > 1.05, so the outcome is supported.
  - I did not recompute the bootstrap interval (seeded resampling needs code). Its lower bound would have to fall below 1.05, more than 50% under the estimate, to change the outcome.
- **K5/K9/K10.** A2's replicate trusted walls (`wall_s + eval_wall_s`; Y rows of rounds r1–r7) are below, in s.
  - **1aua:** 29.718, 31.014, 28.869, 29.074, 30.190, 30.650, 29.143.
    - Mean 29.808. Mean − 17.330 = 12.478, and min/max − 17.330 = 11.539 / 13.684, equal to S.
    - Against tier 2 (23.107): 6.701 [5.762, 7.907], equal.
    - Against tier 3 (40.536): −10.728 [−11.667, −9.522], equal.
  - **1ax2:** 26.007, 25.805, 24.268, 24.383, 24.687, 24.775, 24.538.
    - Mean 24.923; min/max − 16.152 = 8.116 / 9.855, equal.
  - **1dv1:** 35.642, 35.259, 34.297, 34.699, 34.756, 34.645, 34.444.
    - Mean 34.820; min/max − 25.509 = 8.788 / 10.133, equal.
    - The minimum, 34.297, is above tier 2 (34.012) by 0.285, equal to K9's lo.
  - **1nr5:** 35.060, 35.705, 34.332, 34.922, 34.234, 34.262, 34.494.
    - Mean 34.716; min − 33.883 = 0.351, equal to K9's lo.
  - Applying `SCHEMAS.md:198` (lower_better non-inferiority: supported iff hi ≤ 0, not supported iff lo > 0):
    - K5 and K9: lo > 0 on all four cases, so **not_supported ×8**;
    - K10: hi < 0 on all four, so **supported ×4**.
- **K6.**
  - Every A1 and A2 rank-1 value is constant over all 8 rounds (96-file grep), so all 49 unpaired differences are equal and lo = hi:
    - A2 rank-1: 1aua 0.004127948, 1ax2 0.023328163, 1dv1 0.822950303, 1nr5 0.022959271.
  - Differences A2 − A1:
    - 1aua −0.001405 → |d| ≤ 0.012 → not_supported;
    - 1ax2 +0.015933 > 0.012 → higher;
    - 1dv1 +0.083734 → higher;
    - 1nr5 −0.439540 < −0.012 → lower.
  - All four equal S.
- **K7.** Best-of-50 is the maximum of each r1 array (`F/r1/A{1,2}/<case>/eval/dockq.json:1`):
  - 1aua: A1 0.758679, A2 0.897932, difference +0.139253;
  - 1ax2: A1 0.037121, A2 0.922143, difference +0.885022;
  - 1dv1: A1 0.771112, A2 0.868375, difference +0.097263;
  - 1nr5: A1 0.462499, A2 0.569918, difference +0.107418.
  - All four equal S. For the maximum I read only round r1; the scorer's lo = hi shows that the other rounds give the same value.

So `scorer_check = agrees`.

## C. s33's predictions scored (`outcomes.json`)

| id | p | outcome | evidence |
|---|---|---|---|
| Q1 | 0.85 | true | `control/stages/evaluate.json` PASS; S:2 = `comparison_seal.json:2` |
| Q2 | 0.75 | true | Y: 192 `ok` for `status` and `eval_status`, 96 rows |
| Q3 | 0.35 | true | Y:1299 "NVIDIA A100-SXM4-40GB" |
| Q4 | 0.25 | **false** | megadock-gpu sha256 differs: Y:1345 against run9 Y:1355 (b and c hold) |
| Q5 | 0.75 | true | S K1 supported |
| Q6 | 0.72 | true | S K8 supported |
| Q7 | 0.65 | true | S K2 supported |
| Q8 | 0.72 | true | S K3 supported |
| Q9 | 0.60 | true | S K4 supported |
| Q10 | 0.80 | true | Y:1256-1270: 473.149 / 201.494 = 2.348 ≥ 1.5, 28 invocations each |
| Q11 | 0.75 | true | S K5 1aua not_supported |
| Q12 | 0.30 | **false** | S K5 1dv1 not_supported |
| Q13 | 0.40 | **false** | S K9: all four not_supported |
| Q14 | 0.65 | true | S K10: all four supported |
| Q15 | 0.40 | true | S K6: 1ax2 and 1dv1 supported, higher |
| Q16 | 0.50 | true | S K7: all four supported, higher |
| Q17 | 0.60 | true | S K7: no row has sign lower |
| Q18 | 0.90 | true | Y:1519 usd 2.917 (final false) ≤ 12 |
| Q19 | 0.90 | true | `stages/evaluate.json` wall_s 4,430.4 ≤ 10,800 |
| Q20 | 0.90 | true | Y: no `timeout` status |

20 of 20 resolved: 17 true and 3 false (Q4, Q12, Q13). The three misses are all about hardware and timing:
- the GPU binary was not identical to run9's;
- dense ran slower on this A100 box than on run6's H100. A2's arm part took 21–31 s here, against 16.2–21.9 s on the H100 (`s31:146`, from `s07:38-41`).

## D. What the main comparison decides for the seed's question

The seed keeps three conclusions separate (`m5/BRIEF.md:21`).

**1. Scientific agreement at identical settings: supported on all four cases.**
- MEGADOCK's GPU build gives the same ranked rotations and translations as the CPU build on 1aua, 1ax2, 1dv1 and 1nr5. Rank 1 and top-50 membership are included, in all 7 replicates (K1, an exact criterion that needs no margin).
- The reconstructed models are identical to the last coordinate digit, and DockQ is identical: K8 and K3 errors are exactly 0.
- Only the printed scores differ, by at most 0.14 (3.56e-5 relative, 1nr5).
- *Uncertainty kept.* The derived margins (s30: 0.001 Å, 0.01 + 0.0023·max, 0.001, 0.012) are "not applicable to this main run", because the megadock-gpu binary differs from run9's (§B).
  - This does not weaken K1, K8 or K3, whose observed errors are exactly zero and would also pass an exact comparator.
  - K2 is the one result that rests on a margin. Its largest relative error, 3.56e-5, is 65× below the sealed rtol and 32× below the GPU-self score variation run9 measured on fixtures (1.13e-3, s30 §A), but it is not validated for this binary.
- There is still no independent check of DockQ's absolute accuracy (s27 §4).

**2. Execution acceleration: supported.**
- The complete GPU workflow (adapter, docking, 50 reconstructions and the evaluator) is 2.35× faster than the CPU workflow, 95% bootstrap interval [2.30, 2.40], against a sealed threshold of 1.05 (K4).
- Breakdown (descriptive, Y:1252-1282):
  - The arm parts alone are 361.8 s against 91.0 s over 28 invocations, a ratio of 3.98.
  - The evaluator takes about 4 s per invocation on both arms, which pulls the workflow ratio toward 1.
- GPU activity:
  - A1 used 40.6 GPU-busy s in 91.0 s of arm wall (about 45%);
  - A2 used 525.2 s in 754.8 s (about 70%);
  - the evaluator used 0 GPU-busy s.
- Billed cost: the run's own box share is USD 2.74 (`operator/OPERATOR_TAKEAWAY.md`, totals). The allocation, not final, is 1.466 h = USD 2.92 (Y:1513-1520). The invocation-attributed cost is USD 0.98 for all 96 invocations (Y:1288).
- This holds on one A100-SXM4 box with a 30-vCPU EPYC host, 26 OpenMP threads for the CPU arm (`main_design.json` env), and these four cases.

**3. Affordability of denser search at a fixed budget: negative at both CPU-derived tiers, cross-hardware.**
- Dense GPU sampling (54,000 rotations) did not finish within tier 1 (1.5 × the CPU-standard envelope) or tier 2 (2 ×) on any case, in any replicate (K5, K9 not_supported ×8). It finished within tier 3 everywhere (K10).
- **Limits of this result:**
  - The tiers were frozen from run6's walls on a `gpu_1x_h100_pcie` box with a different CPU (s07:56-59, s31:213). This run was on an A100 with an EPYC host, so the result is **cross-hardware**: it compares A100 dense walls with an H100-box budget.
  - On run6's own box, dense had fit tier 2 on every case and tier 1 on 1dv1 and 1nr5 (s07:56-60). The two boxes therefore disagree about tier 2. Affordability at a CPU-derived budget depends on the hardware, and no sealed same-box test settles it on the A100.
  - Tier 3 is 2 × max(M_cpu, M_gpu, M_dense), so it is built from dense's own wall. Fitting it shows little more than "dense did not run more than 2× slower than on the H100".
- *Descriptive same-box figures (not a sealed test; reported only, no criterion changed):*
  - On this box the mean workflow wall of dense divided by CPU-standard's is about 2.04 for 1aua (29.81 / 14.64 s), 2.09 for 1ax2 (24.92 / 11.93), 1.70 for 1dv1 (34.82 / 20.44) and 1.69 for 1nr5 (34.72 / 20.59). The A0 means are from the replicate rows of Y.
  - Run6's sealed rho was 1.44–1.75 (s07:56-59).
  - So on the A100, dense for 1aua and 1ax2 sits at about the 2× line.

**4. Quality from additional search (only where dense is available, i.e. tier 3 on every case).**
- **Best-of-50 DockQ improves on all four cases** (K7, sign higher):
  - 1aua: 0.759 → 0.898;
  - 1ax2: 0.037 → 0.922;
  - 1dv1: 0.771 → 0.868;
  - 1nr5: 0.462 → 0.570.
- **Rank-1 DockQ does not improve consistently** (K6):
  - 1dv1 gains: 0.739 → 0.823;
  - 1ax2 gains formally: 0.007 → 0.023 (+0.016, just over the 0.012 margin). Both values are far below 0.23, the conventional DockQ acceptability cut-off, which is not a sealed criterion here.
  - 1aua shows no difference beyond the margin: 0.0055 → 0.0041, both near zero.
  - **1nr5 loses**: 0.462 → 0.023 (−0.440). This negative result is kept.
- The DockQ arrays are identical across all 8 rounds of each arm, so the replicates measure determinism, not sampling variation. Each case's quality difference is a single deterministic value. With four cases, nothing can be said about a population of targets (`BRIEF.md:23`).
- The K6/K7 margin is "not applicable to this main run" (§B). Every supported row except 1ax2 rank-1 clears it by far, by 0.072 to 0.873. 1ax2 rank-1 clears it by only 0.004.
- No biological efficacy is inferred.

**Overall answer.**
- *"Can MEGADOCK's GPU implementation make denser docking search affordable?"*
  - On run10's A100, the GPU makes standard search 2.35× faster with identical results.
  - Dense GPU search still costs about 1.7–2.1× the CPU-standard workflow on that box. It did not fit the CPU-derived tiers 1 and 2 frozen on the H100.
  - Whether it fits a same-hardware 2× budget is not established by a sealed test.
- *"Does that improve pose recovery within a fixed budget?"*
  - Where dense is available (tier 3), the best of 50 improves on all four cases.
  - The top-ranked pose improves on one case (1dv1) in a way that matters by the conventional cut-off. It improves formally on one more (1ax2), shows no difference on one (1aua) and gets substantially worse on one (1nr5).

**What stays open:**
- same-hardware affordability at tiers 1–2 (the H100 frame is not met on the A100, and the box cannot be pinned);
- the validity of the derived margins for run10's megadock-gpu binary;
- absolute DockQ accuracy (no independent checker);
- anything beyond these four apo cases.

**Evidence limits:**
- one box (A100-SXM4-40GB, EPYC 7J13, 30 vCPU);
- four inputs;
- 7 replicates plus 1 warm-up, deterministic in every output except small score jitter (and timing);
- margins derived on four holo fixtures (run9), on a different megadock-gpu binary;
- tiers frozen on a different box type.

## E. Is a further test justified? No: `no_justified_test`

Each candidate test, and whether it could change the answer:

1. **A fixture rerun on run10's binary, to make the margins applicable** (about USD 3 on an A100, from run9's USD 2.66).
   - It cannot change K1, K8 or K3, whose errors are zero.
   - K2 could flip only if the new fixtures gave GPU-self score noise below about 1.8e-5 relative (rtol = 2 × the maximum, and the observed value is 3.56e-5). run9 saw up to 1.13e-3.
   - It could change K6/K7 only if eps_eval rose enough to push the margin past 0.0159, for 1ax2 rank-1. That needs evaluator self-disagreement of at least 0.002 on identical models, where run9 and run10 both show exactly 0.
   - The box also cannot be pinned, so a rerun need not land on the same binary.
   - Conclusion: not informative enough to justify a run.
2. **A same-hardware affordability test**, which would settle point 3 of §D.
   - It needs a timing calibration and a main run on one known box type. The route cannot guarantee that: the m5 run arguments carry no box type (`R10/args.json:1-14`), the launcher picks the box, and capacity has twice forced an A100 instead of an H100 (s30 §D, s31 §A, this run).
   - On an A100, the tier-2 outcome for 1aua and 1ax2 sits at the 2× line (ratios about 2.04 and 2.09). With the sealed all_pairs worst-case rule, the expected result there is "inconclusive" or "not supported". That would not change the answer "not established at tier 2", and I have already seen the A2 walls, so predictions sealed now would not be blind.
   - The change that would make this test decisive is a box-type pin in the m5 launch arguments. That is a launcher capability, not a scientific decision I can make or a test I can design within the route.
3. **More cases or more replicates.** The seed limits the study to these four cases (`BRIEF.md:3, 23`). Replicates are deterministic in every output that carries the quality conclusions.

So the question is answered as far as this route can answer it, and I write `NEXT.json` `{"action": "stop", "reason": "no_justified_test"}` with no predictions.

**Pipeline limitation, reported as the seed asks (`BRIEF.md:21-22`).** It does not replace the scientific question.
- The m5 run arguments (`R10/args.json`; `SCHEMAS.md:117` `args.comparison` is exactly `{design}`) cannot pin the box type or the GPU build.
- Two kinds of rule therefore cannot be guaranteed to apply to the run they were sealed for:
  - a comparison whose sealed references come from one box type (K5/K9/K10, from run6's H100);
  - a comparison whose tolerances are tied to one binary (s27 §3 step 4).
- The contract can express the comparisons; it cannot guarantee they run on the hardware frame that makes their references and margins valid.
- Closing this would need an owner-approved launcher or contract change, adding a box type to the run arguments. Until then, the same-hardware affordability part stays open.

## F. Narrowing

Unchanged: **no narrowing** (`NARROWING.md`). Every part of the seed's question was tested in run10. The hardware labels (margins not applicable; tiers cross-hardware) are reporting rules that were sealed before the run (s27 §3 step 4; s31 §B4). They limit how strongly two parts can be claimed. They drop no part of the question.
