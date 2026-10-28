# positive-openmm run8: outcome against sealed predictions (predictions/run8.md, 895a89a)

Run committed a945f8e. Box gpu_1x_a10, USD 1.29/h; run_box_usd 1.74; 1.89M tokens in; wall 4,868 s; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Implement FAIL. The right verdict for the wrong reason: the frozen equivalence test could not pass for any method, so both attempts failed with `missing_output`. No evidence was recorded against the method itself.

- Intake to propose passed on an A10, the first run on that box. Sequential ensemble 62.0 s. MPS concurrency factor 1.30. The seal's margins are one baseline SD per metric, cited from reproduce's `ensemble.json` (543.8 kJ/mol final, 123.2 mean), not SD/sqrt(8). The paired rule is 32 held-out seeds, 32 repetitions, budgets [120, 240, 480], with Bonferroni across the two metrics. Propose approved `ensembles` 5 of 5, expected 1.125.
- U29 held: the harness `run_evaluation.sh` and the method's adapter both iterate `EVAL_INPUTS.ids` and validate both `EVAL_SEEDS` shapes.
- Implement: patch applied, method ran (76 s per attempt), six of seven cases passed both times (drops, duplicates, ordering, tail, seeds, schema). The `equivalence` case reported `missing_output` both times. The repair was used and failed identically; review was not reached.
- Root cause: the test author applied the seal's full evaluation rule inside implement. Its equivalence check reads `evaluation.json` records under `METHOD_OUT` and `BASELINE_OUT` and requires 32 repetitions per seed group at every compute budget. Implement never produces evaluation records; it runs the method once at the representative scale. The case was unsatisfiable by construction, the repair feedback (`missing_output: 1`) told the method author nothing true, and the contract never said which outputs implement provides or how the sealed rule applies to them.
- Method outputs (operator reading of public records, scoring only): the method ran four worker processes under MPS with `CUDA_MPS_ACTIVE_THREAD_PERCENTAGE=50`, aggregate 47 to 49 s against 62.9 s (1.29 to 1.33 at representative scale). Its per-seed energies differ from the baseline's by up to 1,350 kJ/mol (final) and 264 kJ/mol (mean), about one between-seed SD; its two attempts agree within 0.05 kJ/mol, and baseline runs agree within 0.03. Seeding is unchanged in the patch. The likely cause is the thread cap changing OpenMM's launch configuration, so trajectories decorrelate without being wrong. Per seed, the method fails the sealed margins; as a paired distribution over 8 seeds, the order-statistic interval at the sealed confidence (ranks 1 and 8, [-1,182, 1,350] kJ/mol for final potential) straddles the margin and decides nothing.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.45, H100 PCIe 0.3, A100 SXM4 0.2, A100 PCIe or A10 0.05 | A10 | no (0.05) |
| intake PASS 0.92 | PASS | yes |
| reproduce PASS 0.88; times for H100/A100 only | PASS; 62.0 s on A10 (no interval given) | yes; n/a |
| profile PASS 0.92; MPS verified 0.92; headroom intervals for H100/A100 only | PASS; verified; 1.30 on A10 | yes; yes; n/a |
| seal PASS 0.8; SD/sqrt(n) cited from reproduce 0.65 | PASS; one SD cited from reproduce | yes; no |
| propose approved 0.8; data-parallel over inputs 0.7 | approved 5/5; ensembles | yes; no |
| implement reached 0.5 | reached | yes |
| implement PASS 0.55 given reached | FAIL | no |
| a method repair used 0.45 | used | yes |
| `run_evaluation.sh` iterates only `EVAL_INPUTS.ids` 0.85 | yes | yes |
| evaluate reached 0.27; all evaluate predictions | not reached | no; n/a |
| takeaways PASS 0.95 | PASS | yes |
| run_box_usd 1.5 to 6 if stopped before evaluate | 1.74 | yes |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |

## What changed my mind
- The run8 prediction that same seed means same trajectory under MPS was wrong for this method: a per-process SM cap decorrelates trajectories while each configuration stays self-consistent. Per-seed identity is not a safe implement-time criterion for a stochastic seal; the seal already treats outputs as stochastic and decides equivalence on paired distributions.
- The box list fell through to the A10, where headroom is 1.30 and the expected gain 1.125. The positive control is weaker there but still above the 1.05 minimum.

## Fix
U30 (contract statement for the implement equivalence case, one gate): implement provides exactly one baseline output (`BASELINE_OUT`) and one method output (`METHOD_OUT`) at the representative scale, inputs and seeds; evaluation records, held-out seeds, repetitions and compute budgets exist only in evaluate, and no test may require them. The `equivalence` case applies the sealed metrics, margins and confidence rule to those representative pairs and fails only when the evidence rejects equivalence: the sealed interval lies entirely outside the margin, or a deterministic seal sees any difference beyond its tolerance. An interval that straddles the margin is not a rejection; evaluate decides. Regression: run8's frozen tests are unsatisfiable on any pair of implement outputs, and run8's method outputs are not an implement-time rejection under the sealed rule. Then run9 from the same brief.

## Later unit candidates
- Run the frozen tests once with the baseline as the method (identity) before the method author is called; tests that fail the identity are invalid tests, an abstention, not a method failure.
- Check that the seal's repetitions by seeds by budgets fit the evaluate budget at the measured ensemble cost (run8's seal: 32 repetitions of four 63 s ensembles is about 8,000 s per arm per mode on the A10, against a 2,400 s script budget).
- Implement signature reports `exit_kind: infra` alongside `error_class: numeric` for a test failure.
