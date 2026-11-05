# Predictions for the main comparison (s31), sealed before launch

s32: these are s31's predictions copied unchanged, ids and probabilities included. s32's run is the same run: same arms' effect, inputs, outputs, metrics, comparisons and sealed numbers. Only the visible form of the design and brief changed (`ASSESSMENT.md` §B).

These predictions cover the run that `NEXT.json` requests: the design `main_design.json` with the brief `MAIN_BRIEF.md`.

**Abbreviations.** Paths are relative to the run's folder:
- S = `control/comparison_scored.json`, or the run's `C/comparison_scored.json`;
- Y = `agent/results/evaluate/comparison_compute.json`, or the run's `A/results/evaluate/comparison_compute.json`;
- E = the evaluate stage record (`control/stages/evaluate.json`).

**Comparison ids** are the design's (`ASSESSMENT.md` §B2).

**Resolution conventions:**
- A statement about S or Y resolves **false** when the file is missing because the run failed. It resolves **null** only when the statement cannot be evaluated for another reason.
- A row with outcome void has sign null.

| id | p | statement (true iff …) | how it resolves |
|---|---|---|---|
| Q1 | 0.85 | Evaluate is PASS, and S exists with `comparison_sha256` equal to `comparison_seal.json`. | E status; S; seal file |
| Q2 | 0.75 | All 96 scheduled invocations in Y have `status` "ok" and `eval_status` "ok". | count over `Y.invocations` |
| Q3 | 0.35 | The GPU name in `Y.system.gpus[0].name` contains "A100-SXM4". | Y.system |
| Q4 | 0.25 | s27 §3 step 4 holds against run9's `Y.system`: (a) equal sha256 values and library sets for megadock, megadock-gpu and the evaluator; (b) equal driver and CUDA versions; (c) equal GPU name. | compare both runs' Y.system |
| Q5 | 0.75 | K1's outcome in S is "supported". | S, K1 |
| Q6 | 0.72 | K8's outcome in S is "supported". | S, K8 |
| Q7 | 0.65 | K2's outcome in S is "supported". | S, K2 |
| Q8 | 0.72 | K3's outcome in S is "supported". | S, K3 |
| Q9 | 0.60 | K4's outcome in S is "supported". | S, K4 |
| Q10 | 0.80 | In Y's `arms` rows, (A0 `wall_s` + `eval_wall_s`) / (A1 `wall_s` + `eval_wall_s`) ≥ 1.5. Both arms have the same number of invocations. | Y.arms |
| Q11 | 0.75 | K5's row for input 1aua has outcome "not_supported". | S, K5 rows |
| Q12 | 0.30 | K5's row for input 1dv1 has outcome "supported". | S, K5 rows |
| Q13 | 0.40 | All four of K9's rows have outcome "supported". | S, K9 rows |
| Q14 | 0.65 | All four of K10's rows have outcome "supported". | S, K10 rows |
| Q15 | 0.40 | At least one of K6's rows has outcome "supported" with sign "higher". | S, K6 rows |
| Q16 | 0.50 | At least one of K7's rows has outcome "supported" with sign "higher". | S, K7 rows |
| Q17 | 0.60 | None of K7's rows has sign "lower". | S, K7 rows |
| Q18 | 0.90 | `Y.allocation.usd` ≤ 12, as the value is written when the file is final or at takeaways. | Y.allocation |
| Q19 | 0.90 | The evaluate stage's `wall_s` ≤ 10,800. | E |
| Q20 | 0.90 | No invocation in Y has `status` "timeout". | Y.invocations |

**Reasoning, briefly:**
- **Q5–Q8:** run9 found transforms, coordinates and DockQ byte-identical on fixtures, and score differences within the sealed rtol (s30 §A). Apo seed cases have their own grid sizes and possible score ties, so I do not treat agreement as certain. K2 is the most fragile comparison, because GPU self-variation reached 1.13e-3 relative on one fixture.
- **Q9 and Q10:** K4 depends on the agreement gate. run6's workflow ratios including the evaluator were 2.3–2.6 (`s07:64`).
- **Q11–Q14:** these come from run6's rho values (`s07:56-59`), adjusted down for an unknown box. Dense has never been timed on an A100 or an A10.
- **Q15–Q17:** I have no prior on apo-case DockQ shifts. The gate can void these rows.
