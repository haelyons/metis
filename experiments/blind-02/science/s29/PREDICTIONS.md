# s29 predictions for the fixture rerun (written before launch; sealed when the operator commits them)

**The run.** One m5 comparison-mode run with the brief `FIXTURE_BRIEF.md` and the design `fixture_design.json` (this folder): arms, fixtures, outputs and comparisons F-K1 to F-K12 as in s27/s28; 6 replicates, 0 warmup, 96 invocations. Notation follows `science/s27/TOLERANCE_RULE.md` §0; M1 to M6 are that rule's margins, applied unchanged.

**Files each prediction resolves from** (the run's folder, laid out as run7/run8): `control/stages/*.json`; `control/receipts/*-comparison-users.json`; `control/comparison_scored.json` (S); `agent/results/evaluate/comparison_compute.json` (Y); the fetched `out/docking.out` files; the sealed harness files in `agent/harness/`.

**Resolution conventions.** A prediction is null only if the file it names is absent for a reason other than the outcome it predicts. A statement about "every present pair" (or every `ok` invocation) with none present resolves null. A statement that requires something to exist or to hold for all scheduled items resolves false when the run failed before producing it.

| id | statement | resolves from |
|---|---|---|
| Q1 | Reproduce PASS, evaluate PASS, and S is written. | stage records; S exists |
| Q2 | The `comparison-users` receipt has rc 0 (so `fetch_private.sh` exited 0 and the private data passed steps 6-8). | `control/receipts/*-comparison-users.json` |
| Q3 | Every invocation in Y with status `ok` has `eval_status` `ok`. | Y invocations |
| Q4 | All 96 scheduled invocations in Y have status `ok` (none `not_run`, `failed`, `timeout` or `invalid`). | Y invocations |
| Q5 | Completeness Z of the s27 rule holds: every one of F-K1 to F-K12 has at least 4 present pairs for every fixture. | S pairs |
| Q6 | Every present pair of F-K2, F-K5, F-K8 and F-K11 (CPU self-agreement) has `agrees` true. | S pairs |
| Q7 | Flag G_T is false: every present F-K3 pair (GPU self-agreement, transforms) agrees. | S pairs |
| Q8 | Flag X_T is false: every present F-K1 pair (CPU vs GPU, transforms) agrees. | S pairs |
| Q9 | Every present F-K6 pair (GPU self-agreement, scores) agrees. | S pairs |
| Q10 | M3 (main K2 atol/rtol) is defensible under the s27 rule. | rule applied to S and A0 `docking.out` |
| Q11 | M2 (main K1 eps_xyz) is defensible under the s27 rule. | rule applied to S |
| Q12 | M4 (main K3 eps_eval) is defensible under the s27 rule, and so M5 and M6 are too. | rule applied to S |
| Q13 | M2, M3 and M4 are all defensible. | rule applied |
| Q14 | Y's `allocation.usd` (the final value when `final` is true, else the value written) is at most 12. | Y allocation |
| Q15 | Y's `allocation.type` names an H100 instance type. | Y allocation |
| Q16 | The largest `eval_wall_s` among invocations with `eval_status` `ok` is at most 60 s. | Y invocations |
| Q17 | The evaluate stage's `wall_s` is at most 14400 s. | `control/stages/evaluate.json` |
| Q18 | The largest `max_rel_error` over the present F-K4 pairs (CPU vs GPU scores) is at most 1e-4. | S pairs |
| Q19 | Neither the sealed `fetch_private.sh` nor the sealed `evaluate.sh` reads, sources or executes any file under `harness/` other than itself (read from their bytes in `agent/harness/`, whose hashes match `control/arms_seal.json`). | sealed harness files |

**Reasoning, stated before the run.**
- **Harness self-containment (Q2, Q19).** run8 failed because the harness agent split data and code into `inputs.json` and `evaluate_dockq.py`, which the pipeline never uploads (`pipeline.js:342-343,834-836`), and s28's brief told it such a file would be "uploaded with the harness" (`s28/FIXTURE_BRIEF.md:349`). The new section states the upload list and requires self-contained scripts; run7's harness agent wrote a self-contained `fetch_private.sh` without being told (run8_fetchfail §C). The residual risk is an agent that disregards the instruction; nothing in the pipeline checks it before the box. Hence 0.85.
- **Evaluator (Q3, Q16).** run8's evaluator code already used `parallel_io=False` (`run8/agent/harness/evaluate_dockq.py`), so the s28 correction was followed once. It has still never run to completion on this route: the program's later lines (`model_name` reindexing, chain mapping) are untested here. run4 measured at most 2.573 s per case (`s26/ASSESSMENT.md:38`, as quoted in s28).
- **Completeness (Q4, Q5)** depends on Q2 and Q3; the GPU build check worked in run8 (`run8/agent/results/reproduce/0008-setup.log:24-25`, `sm_90` cubins on an H100).
- **Agreement and margins (Q6 to Q13, Q18)** are unchanged in reasoning from s28 (CPU byte reproducibility 20/20 in run6; GPU 39 distinct `docking.out` hashes in 40 files in run6), with Q9 raised slightly from s28's 0.20 because a correctly built binary has not yet been observed.
- **Box (Q14, Q15).** run8 landed on an H100 (USD 3.29/h); expected H100 cost about USD 9.5, pessimistic about 12.5 (ASSESSMENT §D).
