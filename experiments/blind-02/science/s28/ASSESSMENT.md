# s28 assessment: fixture run run7 against s27's sealed rule (2026-11-04)

**Scope.** Offline step: no network, no box, no git, no credentials. Bash was denied after its first call, so I read with the file tools and wrote with the file tool. I hashed nothing and compared bytes only by reading. I wrote only into `science/s28/`.
- **Read:** s27 (assessment, `TOLERANCE_RULE.md`, `tolerance_rule.json`, `fixture_design.json`, `PREDICTIONS.md`, `FIXTURE_BRIEF.md`) and s26 §A. I did not reread s01 to s25 in this step; s27 summarizes what they establish.
- **Contract:** `dut/pipeline/m5/SCHEMAS.md:115-203`.
- **run7:** `control/` (seal, scored file, evaluate stage, receipts 0009-0037), `agent/results/evaluate/comparison_compute.json`, `agent/harness/evaluate.sh`, `agent/harness/setup.sh`, the operator takeaway, and a selected handful of fetched files.
- **Seed outputs:** none read. run7 never ran the seed cases.

**Verdict.**
- **What run7 recorded:** no scored data. A harness defect in the evaluator part, not invocation cost, ate the budget. All 13 invocations that ran belonged to the warmup round.
- **The rule:** s27's rule applies and gives **indefensible** for M2 to M6 (reason `fixture_incomplete`). M1's flags are empty.
- **Next test:** a corrected fixture rerun (m5), which is justified and fits the limits.

## A. What run7 recorded

**Schedule.**
- The design asked for 7 rounds (1 warmup + 6 replicates) × 4 arms × 4 fixtures = 112 invocations.
- `comparison_compute.json` lists those 112 rows. 13 have status `ok` and 99 are `not_run` (rows at lines 3-171 against 172-1458).
- All 13 executed invocations are in the **warmup** round. Their fetched folders are `agent/results/evaluate/comparison/w1/<arm>/<input>/`, and no `r<r>` folder exists.
- So no replicate invocation ran.

**The 13 invocations,** in run order (`comparison_compute.json:3-171`; walls in s). Every evaluator part has `eval_status` `timeout`; the eval wall is 901.0 for each, except invocation 13, which is noted in its row.

| k | arm | input | arm wall |
|---|---|---|---|
| 1 | A2 | f1glj | 19.98 |
| 2 | A0 | f1glj | 19.93 |
| 3 | A1 | f1a19 | 1.60 |
| 4 | A0 | f1ht8 | 39.05 |
| 5 | A1 | f1dtd | 2.37 |
| 6 | A0 | f1dtd | 9.79 |
| 7 | A2 | f1dtd | 9.79 |
| 8 | A1 | f1ht8 | 6.43 |
| 9 | A1 | f1glj | 3.32 |
| 10 | A2 | f1a19 | 2.52 |
| 11 | A3 | f1ht8 | 6.43 |
| 12 | A3 | f1glj | 3.27 |
| 13 | A2 | f1ht8 | 22.04 (eval wall 665.79, cut at the budget) |

**Coverage.**
- **By arm:** A0 3, A1 4, A2 4, A3 2.
- **Warmup pairs never reached:** A0 f1a19, A3 f1a19 and A3 f1dtd (rows 14-16 of round 1 are `not_run`).

**Which outputs have values.**
- Every executed invocation has `out/docking.out` and `out/model_1..50.pdb`; for example, `w1/A1/f1a19/out/`. Every arm command's `rc` is 0 (`w1/A1/f1a19/wrap.json:34,48`).
- No `eval/` folder holds a `dockq.json`. Each holds only `evaluator.log`.
- Warmup rounds are not scored (`SCHEMAS.md:190`), so `comparison_scored.json` has 0 present pairs in all 12 comparisons × 4 fixtures, and every unit is void with reason `missing_values`.
- Totals: supported 0, not_supported 0, inconclusive 0, void 48 (`comparison_scored.json:2861-2865`).
- The seal matches: `comparison_sha256` `c42b95cb…` in both `comparison_scored.json:2` and `comparison_seal.json:2`. Evaluate is PASS (`control/stages/evaluate.json`).

**Parts' walls against the comparison receipts.** Each `comparison` receipt minus the invocation's arm and eval walls gives the overhead of the wrapper, cleanups and fetch:

| receipt | wall | arm + eval walls | overhead |
|---|---|---|---|
| 0012 | 961 | 921.0 | 40 |
| 0014 | 964 | 921.0 | 43 |
| 0016 | 945 | 902.6 | 42 |
| 0018 | 989 | 940.1 | 49 |
| 0036 | 732 | 687.8 | 44 |

- Each `comparison-job` receipt took 23 to 31 s (for example `0013-comparison-job.json`: 23 s).
- **Fixed cost per invocation outside the parts:** about 63 to 80 s, against s27's assumed ~30 s.
- **Other evaluate-stage commands:** users 49 s (`0009`); `comparison-private-remove` 23 s (`0037`).

**Why it covered what it did.** The evaluator part hung on every invocation until its 900 s cap.
- `evaluate.sh:11` runs the evaluator as `"$VPY" - <<'PY'` (Python code read from standard input).
- `BiotiteDockQ` defaults to `parallel_io=True` (`pinder/eval/dockq/biotite_dockq.py:226`, in the fetched venv), which calls `multiprocessing.get_context("spawn").Pool` (`pinder/core/utils/process.py:17,33`).
- Spawned workers re-import the main module from its path, and the path is `<stdin>`. Every worker dies with `FileNotFoundError: … '/tmp/m5-…/<stdin>'` (`w1/A1/f1a19/eval/evaluator.log:1-15`, repeated), and the pool waits forever.
- **Cost:** about 13 × (901 + ~70) s ≈ 12,600 s, the whole `budget_s`. The evaluate stage took 12,695 s against 12,600 s.
- **Not the cause: the box.** The arm parts took 1.6 to 39 s. On an H100 the evaluator would have hung the same way.
- **Not the cause: a real per-invocation cost.** run4 measured complete 50-model evaluations at no more than 2.573 s (`s26/ASSESSMENT.md:38`).
- **Not the cause: s27's projection.** It was wrong on overhead (about 70 s, not 30 s), but that alone would have cost about 112 × 100 s ≈ 3.1 h, within the budget.
- **Cause:** failures of the evaluator part (a harness defect).
- **Bill:** run box USD 4.84 at USD 1.29/h on `gpu_1x_a10` (operator takeaway, Totals). The allocation was 3.83 h and USD 4.94 when the compute file was written, `final` false (`comparison_compute.json:1772-1779`).

**A second defect, seen in passing: GPU build target.**
- `setup.sh:50-51` builds `megadock-gpu` with `-arch=sm_90` (H100), but the box was an A10 (compute capability 8.6; `comparison_compute.json:1517`).
- Code built for `sm_90` cannot run custom kernels on an `sm_86` device. cuFFT, a library with its own device code, can.
- The GPU arm still exited 0 (`w1/A1/f1a19/log/cmd1.stdout:5,60`; `cmd1.stderr` empty).
- Its warmup rows do not resemble the CPU arm's:
  - f1glj first row: A0 and A2 both `0.000000 1.875281 0.107086 114 21 127 8131.88`; A1 `… 4284.78` and A3 `… 5257.64`, which also differ from each other (`w1/<arm>/f1glj/out/docking.out:5`);
  - f1a19: A2 `3806.08` against A1 `3167.72`.
- I cannot establish from the files whether the kernels failed silently. A1/A3 outputs from run7 should be treated as **suspected invalid**.
- These are warmup files, never inputs to the rule. I state them as an observation only and draw no tolerance from them.

**Isolation.** None of the files I read suggests a breach.
- Users setup passed (`0009` rc 0) and private-data removal passed (`0037` rc 0).
- The evaluator's failure is a hang inside its own part.

## B. s27's sealed rule applied to run7, unchanged

Inputs per §0: S = `control/comparison_scored.json`, the seal in `control/comparison_seal.json`, and the evaluate stage record.

1. **V0** (S exists, seal matches, evaluate PASS): **holds**. The hash is `c42b95cb460ac3e2…` in both files, and the stage status is `PASS`.
2. **Z** (every F-Kn has at least 4 present pairs for every fixture): **fails**. Every comparison has 0 present pairs on every fixture: each row has `"n": 0, "n_missing": 6`, and all 6 pairs are `"missing": true` (for example `comparison_scored.json:14-66`). By §1, M2 to M6 are **indefensible** with reason `fixture_incomplete`.

| margin | value the rule gives | missing values | defensible now |
|---|---|---|---|
| M1 (K1 transforms, exact) | Comparator `exact`, margin null. X_T, C_T and G_T are computed on present pairs; there are none, so each is false only vacuously, marked `incomplete`. | every F-K1/F-K2/F-K3 replicate pair | not applicable (sealed criterion); flags uninformative |
| M2 (eps_xyz) | indefensible, `fixture_incomplete`; no value | F-K7/F-K8/F-K9 pairs, so Mxyz | no |
| M3 (atol, rtol) | indefensible, `fixture_incomplete`; no rtol (MR undefined). §3 step 1 defines `atol = 10^-d` from present A0 replicate files, and none exist. | F-K4/F-K5/F-K6 pairs; A0 replicate `docking.out` | no |
| M4 (eps_eval) | indefensible, `fixture_incomplete` | F-K10/F-K11/F-K12 pairs, which would also have needed `dockq.json` | no |
| M5, M6 (0.01 + 2·eps_eval) | indefensible, `eps_eval_indefensible` | as M4 | no |

- **Main comparison now:** by §3 step 3, it could claim no tolerance for any margin.
- **Rule status:** unchanged. The next run uses the same arms, commands, outputs, comparisons and F-K ids, so the rule applies to it verbatim. Its warmup is 0, and the rule reads replicate pairs only.

## C. s27's predictions scored (`outcomes.json`)

| id | outcome | evidence |
|---|---|---|
| Q1 | true | reproduce PASS and evaluate PASS (`control/stages/`, operator takeaway lines 8 and 13); S written |
| Q2 | false | Z fails: 0 present pairs everywhere (S, every row) |
| Q3 | null | no present F-K2/5/8/11 pair; the statement is only vacuously true |
| Q4 | null | no present F-K6 pair |
| Q5 | null | no present F-K3 pair |
| Q6 | null | no present F-K1 pair |
| Q7 | null | maximum over no F-K4 pair is undefined |
| Q8 | null | both maxima undefined |
| Q9 | null | per-fixture maxima undefined |
| Q10 | false | M3 indefensible (`fixture_incomplete`), §B |
| Q11 | false | M2 indefensible, §B |
| Q12 | false | M4 indefensible, §B |
| Q13 | false | none of M2 to M4 defensible |
| Q14 | true | `allocation.usd` 4.944528075 ≤ 10 (`comparison_compute.json:1778`); run box USD 4.84 (operator Totals) |
| Q15 | false | 99 of 112 rows `not_run`; the 13 `ok` rows all have `eval_status` `timeout` |
| Q16 | null | the rule derives no rtol: MR is undefined without present pairs |

Resolved: 9 of 16 (2 true, 7 false). Unresolvable: 7, because the run produced no replicate pair.

## D. The next test: a corrected fixture rerun (m5)

**Why this test and not another.**
- The margins still have no fixture data, so the main comparison cannot run with any defensible tolerance.
- Both causes are fixable within the existing contract: the evaluator invocation and the GPU build target are harness and brief matters, so there is no `contract_gap`.
- The cost is small and under the standing USD 20 rule.
- Stopping would leave the seed's agreement question unanswerable for no good reason.

**Design:** `fixture_design.json`, in the exact schema of `SCHEMAS.md:117-141`. It equals s27's design except:
- `evaluator.spec.invocation`: new text requiring `parallel_io=False` and a script file, not standard input;
- `evaluator.timeout_s` 180;
- `timeout_s` 300;
- `warmup` 0;
- `budget_s` 16200;
- `order_seed` 28281 and `bootstrap_seed` 28282.

**Brief:** `FIXTURE_BRIEF.md`.
- Lines 1-310 are meant to be byte-identical to `m5/b01_materials/BRIEF_run1.md:1-310`. They were written with the file tool from the read text, not copied, so the operator should verify byte equality before sealing.
- Then one section, `## Comparison request (science step s28)`, which adds two instructions:
  - build `megadock-gpu` for the box's own compute capability (read with `nvidia-smi --query-gpu=compute_cap`), and stop setup if `cuobjdump --list-elf` lacks it;
  - run the evaluator with `parallel_io=False` from a file.
- Neither the brief section nor the view text states a margin, threshold, expected result or rule.

**Sizing, from run7's measured costs.**
- **Fixed cost per invocation:** 63 to 80 s (job plus wrapper and fetch).
- **Arm part:** CPU 2.5 to 39 s (mean over fixtures ≈ 16 s); GPU 1.6 to 6.4 s.
- **Evaluator:** unmeasured on this route. run4 measured ≤ 2.6 s; I allow ≤ 30 s.
- **Expected per invocation:** ≈ 72 + 9.5 + 10 ≈ 92 s; pessimistic ≈ 122 s.
- **96 invocations** (no warmup, which run7 showed buys nothing for exact-agreement outputs): expected ≈ 8,800 s (2.45 h), pessimistic ≈ 11,700 s (3.25 h).
- **`budget_s` 16200 (4.5 h):** covers 132 invocations at 122 s.
- **`timeout_s` 300:** about 7.7× the largest arm wall (39 s).
- **`evaluator.timeout_s` 180:** about 70× run4's evaluator wall. It caps the cost of a repeat hang at about 260 s per invocation rather than 970 s.

**Box and price.**

| case | hours | A10 (USD 1.29/h) | H100 (USD 3.29/h) |
|---|---|---|---|
| expected | 2.8 | 3.6 | 9.2 |
| pessimistic | 3.6 | 4.7 | 11.9 |
| worst (budget exhausted) | 4.9 | 6.3 | 16.1 |

- Pre- and post-evaluate time is about 0.35 h (run7: allocation start 18:10:08, users receipt 18:28:56).
- Worst case: 0.35 + 4.5 + ~0.05 h ≈ 4.9 h, under the 6 h limit, and USD 16.1 at most, under USD 20.
- On an A10 the CPU arm walls above are measured. On an H100 box (26 threads), run6's CPU walls were similar (9.0 to 14.5 s on seed cases; `s07:38-41`) and its GPU walls shorter. The fixed cost per invocation is box-independent, so the budget holds on both.

**What each result decides** (as sealed in s27 §E, unchanged).
- **M2 to M4 defensible:** the next step writes the main agreement design with the margins from §3.
- **G_T true:** `needs_owner` on the exact transform gate.
- **Some margin indefensible:** `needs_owner` on whether dependent comparisons proceed.
- **V0 or Z fails again:** I diagnose. A repeat harness defect would point to a contract gap: `SCHEMAS.md` "Evaluate, comparison mode" runs no evaluator check before the first invocation and has no early stop on repeated evaluator timeouts. I record that weakness now; the evaluator timeout cap mitigates it.

**Box-identity constraint for the main run.**
- Rule §3 step 4 makes the margins not applicable when the main run's GPU name, driver or executables differ from the fixture run's.
- With a per-box build target, the fixture run and the main run must land on the same GPU type.
- The launcher takes any type up to USD 3.29/h, and the last launch had no H100 or A100 capacity. Whether to pin the main run's box type to the fixture run's is a decision for the owner before the main run. It does not block this step.

## E. Do the main runs still fit after the next step?

- **After the next step (worst case):** USD 93.36 − 16.1 = **USD 77.26**.
- **Main agreement run** (A0 and A1 on the four seed cases, 6 replicates, 48 invocations): ≈ 48 × 95 s ≈ 1.3 h + 0.4 h ≈ 1.7 h, or about USD 5.6 on an H100.
- **Physical card's planned study:** USD 49.48 (`s13/ASSESSMENT.md:86`).
- **Left:** 77.26 − 5.6 − 49.48 = **USD 22.2**. So **yes**.
- **Caveat:** run7 measured about 70 s of fixed cost per invocation, against the ~30 s assumed earlier. If the card's plan assumed less, each 100 extra invocations add ≈ 1.2 h ≈ USD 4.1 on an H100. I could not recount the card's invocations in this step, so the USD 22.2 reserve is the margin against that.

## F. Narrowing

Unchanged: no narrowing (`NARROWING.md`).

## Predictions

17 predictions for the rerun are sealed in `PREDICTIONS.md` and `predictions.json`.
