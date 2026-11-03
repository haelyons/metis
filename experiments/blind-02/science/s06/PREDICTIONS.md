# Predictions before the s06 relaunch of the s04 timing-only calibration

The next test is in `NEXT.json` (m5, `--stop-after-reproduce`) and `CALIBRATION_BRIEF.md`, which is intended to be a byte-for-byte copy of `science/s04/CALIBRATION_BRIEF.md`. This step launched nothing. The operator commits these files before launch, which seals them. The IDs are local to s06. s05 sealed none, so `outcomes.json` is empty.

**Run conditions assumed.** Codex is at its usage limit until 2026-11-07 23:30 UTC, so intake, harness authoring and repairs run on the Claude Opus understudy. The operator's `new_run.py --brief-from=s06` copies the brief into `<run_root>/brief/` and passes that folder in `args.add_dirs`.

## Definitions

These are the brief's definitions, unchanged from `science/s04/PREDICTIONS.md`:

- **W[c,a,b]**: production wall for case c, arm a, block b.
- **D**: docking process wall.
- **P**: printed "Elapsed time".
- **E[c]**: run4's per-case evaluator maximum (1.97287, 1.77213, 2.57327, 2.42460 s).
- **M[c,a]**: max over blocks 1–3 of W[c,a] + E[c].
- **rho[c]**: M[c,gpu_dense] / max(M[c,cpu_standard], M[c,gpu_standard]).

Retained blocks are 1–3.

**When an item is null.** An item is null if its inputs are missing. Its inputs are the jobs, receipts or transcripts it names, and for Q6–Q11 the retained jobs of all four cases in the arms involved. Partial completion makes an item null unless a valid witness already decides it: a timeout lower bound, or completed walls that settle the inequality.

## Forecasts

Q1–Q12 have the same statements and resolution rules as s04. Q1 and Q2 have lower probabilities because Claude now authors the intake and the harness. Q3 is lowered slightly because the GPU build is new to a Claude-authored harness. Q13 and Q14 are new.

| ID | p | Checkable statement | Resolution |
|---|---:|---|---|
| Q1 | 0.80 | Intake passes with `data:"available"`. | True iff `control/stages/intake.json` is PASS and the intake reply has `data:"available"`. False if intake completes with FAIL or another data value, whatever the cause. Null if there is no completed intake. |
| Q2 | 0.65 | All 48 primary-schedule jobs (blocks 0–3) have status complete with valid outputs, and the reproduce stage is PASS. | From `out/timing_calibration.json` and `control/stages/reproduce.json`. False if any primary job failed, was invalid or timed out, or if reproduce did not pass. Null if the file is missing. |
| Q3 | 0.80 | The GPU arms really ran on the GPU: every GPU-arm docking log prints 1 GPU, and the anchors receipt has `gpu_busy_known:true` with `gpu_busy_s > 0`. | True iff both hold. False if either is contradicted. Null if the receipt or the logs are missing. |
| Q4 | 0.80 | For every case, every retained CPU-standard P is within ±10% of run4's (9.14, 7.14, 11.98, 11.86 s). | 12 values are checked. |
| Q5 | 0.75 | For every case, the median over retained blocks of GPU-dense P is within ±15% of run2's GPU-dense docking time (16.60, 13.88, 19.38, 19.52 s). | 4 medians are checked. |
| Q6 | 0.88 | rho[c] ≤ 2.0 for all four cases, so dense is eligible at physical tier 2. | From the job records and E. False if any case has rho > 2.0, or a dense timeout lower bound + E above 2 × max(M_cpu, M_gpu). |
| Q7 | 0.20 | rho[c] ≤ 1.5 for all four cases, so dense is eligible at all physical tiers. | Same inputs as Q6. |
| Q8 | 0.95 | For every case, max over blocks 1–3 of W[c,gpu_dense] ≤ max over blocks 1–3 of W[c,cpu_standard] + 60 s. | From the job records. |
| Q9 | 0.92 | For every case, the median over blocks 1–3 of (W_cpu + E)/(W_gpu + E), paired by block, is ≥ 1.05. | From the job records. |
| Q10 | 0.60 | For every case, the median over blocks 1–3 of W_cpu/W_gpu, paired by block, is < 3.0. | From the job records. |
| Q11 | 0.55 | For every retained GPU-standard job, D − P ≥ 0.5 s. | The 12 retained gpu_standard jobs are checked. |
| Q12 | 0.85 | The operator takeaway's Totals usd is ≤ 5.00. | From `operator/OPERATOR_TAKEAWAY.md` Totals. This is the stage-wall estimate, as written; it is not an invoice. |
| Q13 | 0.88 | The intake agent could read the brief: no intake-call transcript (primary or understudy) records a permission denial for a Read of the brief or its copy, and `agent/intake/brief.md` exists. | True iff both hold. False if any intake transcript lists such a denial or `intake/brief.md` is absent after a completed intake. Null if intake did not run. |
| Q14 | 0.65 | Setup passes with at most one harness repair: at most one `*-harness-repair` agent call precedes the first setup receipt with rc 0. | From `agent/wf/agents/` and `control/receipts/`. False if two or more repairs were needed, or setup never passed. Null if no harness was authored. |

## Correlations

Q1 depends on Q13. Q2 depends on Q14. Q6, Q7 and Q8 are correlated through the dense walls. Q9 and Q10 are correlated through the GPU-standard walls.

## Limits

No item resolves agreement, acceleration verdicts, affordability verdicts or quality. These forecasts authorise no further run.
