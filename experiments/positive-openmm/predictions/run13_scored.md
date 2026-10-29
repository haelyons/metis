# positive-openmm run13: outcome against sealed predictions (predictions/run13.md, 54cdf7a)

Run committed 859eab2. Box gpu_1x_a100_sxm4, USD 1.99/h; run_box_usd 3.93; 1.88M tokens in; wall 7,103 s; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Implement FAIL (`tests_pass` false after the method repair), evaluate skipped. U34 worked as intended. The failure is a pipeline defect, not a method failure: the frozen tests could never pass, because they ran against baseline outputs different from the ones their author was shown.

- Intake through propose passed on the A100 SXM4. Sequential ensemble 59.1 s; concurrency factor 1.81, MPS verified. Seal: the eight replica seeds of one ensemble; margins 38.6 (mean) and 103.5 (final) kJ/mol; repetitions 10, warmup 1; outcome curve not applicable. Propose approved `ensembles` 5 of 5, expected 1.475.
- U34 smoke: the pre-seal adapter again ran one whole ensemble per sealed seed. Smoke 1 measured `process_wall_s` 491 s, projected (1 + 10) × 2 × 491 ≈ 10,800 s against 2,160 s, and failed `cost`. The repair rewrote `run_evaluation.sh` to run one ensemble whose eight replicas carry seeds 1000 to 1007 ("The eight seeds identify the eight replicas, not eight shifted ensembles"), kept 8 replicas × 25,000 steps, and smoke 2 passed at 60.9 s.
- Method (four MPS workers) ran in 58 s with exit 0 on both attempts. The frozen tests failed all nine cases with `invalid_output` on both attempts, before comparing anything.
- Root cause: the frozen tests load "the" baseline `ensemble.json` and reject the outputs when there is more than one. The test author's view of `baseline-out/` is `A/results/reproduce/out/`, which holds one baseline run. But on the box, `BASELINE_OUT` is a copy of remote `out/` made at the start of implement, after profiling. By then `out/` also holds a second run of the baseline command made during profiling, in its own `baseline.*` directory (this harness makes a fresh directory per run), plus profiler and concurrency outputs; the harness's pointer file now names that second run. So the box held two candidate `ensemble.json` files. The method repair could not help, since the failure is in the baseline outputs.
- The same gap was latent in run12: that harness reused one directory, so the profiling-stage run silently overwrote the reproduce run in `BASELINE_OUT`. The two runs' energies differ slightly (−299938.104 against −299938.093 kJ/mol in run13), so tests compared against outputs other than the ones the seal cites.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| A100 SXM4 0.35, A10 0.3, H100 SXM5 0.15, H100 PCIe 0.15, A100 PCIe 0.05 | A100 SXM4 | yes (0.35, the mode) |
| intake PASS 0.95 | PASS | yes |
| reproduce PASS 0.93; 55 to 65 s on A100 | PASS; 59.1 s | yes; yes |
| profile PASS 0.95; every receipt fetched 0.95; MPS verified 0.92; A100 headroom 1.78 [1.6, 2.0] | PASS; yes; yes; 1.81 | yes; yes; yes; yes |
| seal PASS 0.9; margins cite reproduce 0.9; replica seeds of one ensemble 0.75; curve not applicable 0.85 | PASS; cited; yes; yes | yes; yes; yes; yes |
| propose approved 0.88; ensembles 0.55 | approved 5/5; ensembles | yes; yes |
| implement reached 0.7 | reached | yes |
| first adapter smoke fails 0.65; category `cost` 0.5 | fails; `cost` | yes; yes |
| repair makes the second smoke pass 0.7; VOID at smoke 0.2 | passes; no | yes; yes (against 0.2) |
| passing smoke's process_wall_s 55 to 80 s on A100 | 60.9 s | yes |
| test author reads only representative outputs 0.9 | the loader reads BASELINE_OUT and METHOD_OUT only | yes |
| implement PASS 0.55; method repair used 0.3 | FAIL; repair used | no; no (0.3) |
| evaluate reached 0.4, and all given-evaluate predictions | not reached | yes (against 0.4); n/a |
| takeaways PASS 0.95; run_box_usd 1.3 to 6 if the run stops before evaluate | PASS; 3.93 | yes; yes |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |
| end-to-end PASS 0.24 | no | yes (against 0.24) |

## What changed my mind
- The risk I named, a repair that saves cost by cutting work, did not happen: the repair recovered the sealed meaning from the cost numbers and the seal.
- I gave implement PASS 0.55 thinking only of test-content risk. I never checked that the test author's view and the test run hold the same baseline outputs. They have differed since implement first ran; run13 is the first harness whose layout made that visible.

## Fix
U35 (one gate: frozen tests run against the baseline outputs their author saw). When reproduce passes, the pipeline freezes the anchor run's remote `out/` on the box as `reproduce-out/`. Its fetch is the local `A/results/reproduce/out/` that the seal and test author read. Implement's snapshot copies `reproduce-out/`, not the post-profile `out/`, to `baseline-out/`; profiler outputs and later runs of the baseline command never enter the baseline outputs. Regression: run13's frozen `check_outputs.py`, with run13's reproduce outputs and a second `baseline.*` run added to `out/` during profiling, passes against a matching method output; under the old snapshot it fails every case `invalid_output`. Then run14 from the same brief.

## Later unit candidates (carried)
- Implement box operations fetch the whole `out/` tree (1.3 GB profile report) every time. Smoke 1's receipt took 1,102 s of its 1,200 s budget for a 491 s adapter run.
- Record meaning: an executable check that adapter records mean the sealed executions. U34 catches the run12/run13 case only through its cost.
- An evaluator command that timed out gets one identical retry, which cannot succeed (workspace reused); the stage is labelled VOID `parse` instead of `timeout`.
- Implement signature `exit_kind: infra` with `error_class: numeric` for a test failure (seen again here).
- Propose with an empty menu built on missing measurements is FAIL `numeric`; VOID `infra` would separate it from a failed method.
- boxrun keeps no fetch error text.
- Identity smoke: frozen tests against the baseline as method, before the method author. It would have caught run13 before the method author call.
- `test_m5_reproduce.js` `concurrency-real-mps-cleared` intermittent failure; one unexplained `test_m5_budgets.js` failure before the U34 pin.
