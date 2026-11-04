# s28 predictions for the fixture rerun (sealed before launch)

**The run.** One m5 comparison-mode run with the brief `FIXTURE_BRIEF.md` and the design `fixture_design.json` (this folder).
- Arms, fixtures, outputs and comparisons F-K1 to F-K12 are as in s27.
- 6 replicates, 0 warmup: 96 invocations.
- Notation follows `science/s27/TOLERANCE_RULE.md` §0. M1 to M6 are that rule's margins, applied unchanged.

**How each prediction resolves.** Each resolves from these files of the run:
- `control/stages/*.json`;
- `control/comparison_scored.json` (S);
- `agent/results/evaluate/comparison_compute.json` (Y);
- the fetched `out/docking.out` files.

A prediction is null only if the file it names is absent for a reason other than the outcome it predicts. A statement about "every present pair" with no present pair resolves null.

| id | statement | resolves from |
|---|---|---|
| Q1 | Reproduce PASS, evaluate PASS, and S is written. | stage records; S exists |
| Q2 | Every invocation in Y with status `ok` has `eval_status` `ok` (no evaluator timeout or failure). | Y invocations |
| Q3 | All 96 scheduled invocations in Y have status `ok` (none `not_run`, `failed`, `timeout` or `invalid`). | Y invocations |
| Q4 | Completeness Z of the s27 rule holds: every one of F-K1 to F-K12 has at least 4 present pairs for every fixture. | S pairs |
| Q5 | Every present pair of F-K2, F-K5, F-K8 and F-K11 (CPU self-agreement) has `agrees` true. | S pairs |
| Q6 | Flag G_T is false: every present F-K3 pair (GPU self-agreement, transforms) agrees. | S pairs |
| Q7 | Flag X_T is false: every present F-K1 pair (CPU vs GPU, transforms) agrees. | S pairs |
| Q8 | Every present F-K6 pair (GPU self-agreement, scores) agrees. | S pairs |
| Q9 | M3 (main K2 atol/rtol) is defensible under the s27 rule. | rule applied to S and A0 `docking.out` |
| Q10 | M2 (main K1 eps_xyz) is defensible under the s27 rule. | rule applied to S |
| Q11 | M4 (main K3 eps_eval) is defensible under the s27 rule, and so M5 and M6 are too. | rule applied to S |
| Q12 | M2, M3 and M4 are all defensible. | rule applied |
| Q13 | Y's `allocation.usd` (the final value when `final` is true, else the value written) is at most 12. | Y allocation |
| Q14 | Y's `allocation.type` names an H100 instance type. | Y allocation |
| Q15 | The largest `eval_wall_s` among invocations with `eval_status` `ok` is at most 60 s. | Y invocations |
| Q16 | The evaluate stage's `wall_s` is at most 14400 s. | `control/stages/evaluate.json` |
| Q17 | The largest `max_rel_error` over the present F-K4 pairs (CPU vs GPU scores) is at most 1e-4. | S pairs |

**Reasoning, stated before the run.**
- **Evaluator (Q2, Q15).** Run7's evaluator hung because PINDER's spawn pool cannot re-import a program read from standard input (`run7/.../eval/evaluator.log:1-15`; `pinder/core/utils/process.py:17,33`). With `parallel_io=False` no pool starts. The residual risk is that a freshly generated harness disregards the instruction, hence 0.70. Run4 measured the evaluator at no more than 2.573 s per case of 50 models (`s26/ASSESSMENT.md:38`). Serial reading and larger fixtures could raise that, but 60 s leaves a wide margin.
- **Completeness (Q3, Q4).** Q3 and Q4 depend on Q2 and on the GPU build check: a target mismatch now stops setup rather than producing outputs.
- **Agreement (Q5 to Q8).** CPU byte reproducibility held 20/20 in run6 (`s07/ASSESSMENT.md:116`). Run7's warmup files agree with that: A0 and A2 on f1glj have identical first rows. Those warmup files are an informal observation, not a rule input. GPU reproducibility is doubtful: run6 had 39 distinct `docking.out` hashes in 40 files. Run7's warmup A1 and A3 on f1glj differ in their first rows, but on a binary built for `sm_90` running on an `sm_86` device, so that observation may not carry over to a correctly built binary.
- **Margins (Q9 to Q12, Q17).** These follow the reasoning s27 sealed, unchanged.
- **Box type (Q14).** The last launch found no H100 or A100 capacity.
