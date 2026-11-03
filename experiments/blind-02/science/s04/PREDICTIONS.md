# Predictions before the s04 timing-only calibration

The next test is defined in `NEXT.json` and `CALIBRATION_BRIEF.md` (m5, `--stop-after-reproduce`). This step launched nothing. The operator commits these files before launch, which seals them. The IDs are local to s04; s03's IDs are resolved in `outcomes.json`. Probabilities are forecasts, not acceptance criteria. The sealed decision rule is in the brief.

## Definitions

These are the brief's definitions:

- **W[c,a,b]**: production wall for case c, arm a, block b.
- **D**: docking process wall.
- **P**: printed "Elapsed time".
- **E[c]**: run4's per-case evaluator maximum (1.97287, 1.77213, 2.57327, 2.42460 s).
- **M[c,a]**: max over blocks 1–3 of W[c,a] + E[c].
- **rho[c]**: M[c,gpu_dense] / max(M[c,cpu_standard], M[c,gpu_standard]).

Retained blocks are 1–3.

**When an item is null.** An item is null if its inputs are missing. Its inputs are the jobs or receipts it names, and for Q6–Q11 the retained jobs of all four cases in the arms involved. Partial completion makes an item null unless a valid witness already decides it: a timeout lower bound or completed walls that settle the inequality.

## Forecasts

| ID | p | Checkable statement | Resolution |
|---|---:|---|---|
| Q1 | 0.85 | Intake passes with `data:"available"`. | True iff the stage is PASS and the reply has `data:"available"`. False if intake completes with FAIL or another data value. Null if there is no completed intake. |
| Q2 | 0.75 | All 48 primary-schedule jobs (blocks 0–3) have status complete with valid outputs, and the reproduce stage is PASS. | Taken from `out/timing_calibration.json` and `control/stages/reproduce.json`. False if any primary job is failed, invalid or timed out, or if reproduce fails. Null if the file is missing. |
| Q3 | 0.85 | The GPU arms actually ran on the GPU: every GPU-arm docking log prints 1 GPU, and the anchors receipt has `gpu_busy_known:true` with `gpu_busy_s > 0`. | True iff both hold. False if either is contradicted. Null if the receipt or logs are missing. |
| Q4 | 0.80 | For every case, every retained CPU-standard P is within ±10% of run4's (9.14, 7.14, 11.98, 11.86 s). | 12 values are checked. |
| Q5 | 0.75 | For every case, the median over retained blocks of GPU-dense P is within ±15% of run2's GPU-dense docking time (16.60, 13.88, 19.38, 19.52 s). | 4 medians are checked. |
| Q6 | 0.88 | rho[c] ≤ 2.0 for all four cases, so dense is eligible at physical tier 2. | Computed from the job records and E. False if any case has rho > 2.0, or has a dense timeout lower bound + E above 2 × max(M_cpu, M_gpu). |
| Q7 | 0.20 | rho[c] ≤ 1.5 for all four cases, so dense is eligible at all physical tiers. | Same inputs as Q6. |
| Q8 | 0.95 | For every case, max over blocks 1–3 of W[c,gpu_dense] ≤ max over blocks 1–3 of W[c,cpu_standard] + 60 s, which makes C2's primary cap non-discriminating. | Computed from the job records. |
| Q9 | 0.92 | For every case, the median over blocks 1–3 of (W_cpu + E)/(W_gpu + E), paired by block, is ≥ 1.05. | Computed from the job records. |
| Q10 | 0.60 | For every case, the median over blocks 1–3 of W_cpu/W_gpu, paired by block, is < 3.0. Whole-workflow production speedup stays well below the docking-only ratio of 5.3–6.3. | Computed from the job records. |
| Q11 | 0.55 | For every retained GPU-standard job, D − P ≥ 0.5 s: process overhead outside MEGADOCK's printed timer, such as CUDA initialisation, is at least 0.5 s. | 12 retained gpu_standard jobs are checked. |
| Q12 | 0.85 | The operator takeaway's Totals usd is ≤ 5.00. | Read from `operator/OPERATOR_TAKEAWAY.md` Totals. This is the stage-wall estimate, not an invoice; it is checkable as written. |

## Correlations

Q6, Q7 and Q8 are correlated through dense walls. Q9 and Q10 are correlated through GPU-standard walls.

## Limits

No item resolves agreement, acceleration verdicts, affordability verdicts or quality. No further run is authorised by these forecasts.
