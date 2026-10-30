# positive-openmm run15: outcome against sealed predictions (predictions/run15.md, 0186ae2)

Run committed 0e9d963. Box gpu_1x_a100_sxm4, USD 1.99/h; run_box_usd 2.24; 3.34M tokens in; wall 4,051 s; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Implement FAIL (`tests_pass` false after the method repair), evaluate skipped. The method was correct; it failed on an output file name. Its frozen tests pass all eight cases, equivalence included, once its stdout log carries the baseline's name. This is a pipeline defect: no step told the method author, or its repair, which output paths the tests read.

- Intake through propose passed on the A100 SXM4. Sequential ensemble 58.4 s; concurrency factor 1.76, MPS verified. Seal (one attempt, no `protocol_cost`): the eight replica seeds 1000 to 1007 of one ensemble, warmup 1, repetitions 5, curve not applicable, margins 38.6 and 103.5 kJ/mol from reproduce, `baseline_invocation_s` 116.8 s (twice the measured ensemble, an explicit allowance for unmeasured process overhead); projected 1,402 s against 2,160 s. Propose approved `ensembles` 5 of 5, expected 1.35.
- Smoke 1: the pre-seal adapter ran one ensemble per sealed seed (470 s) and failed `metrics`. The repair's adapter (one ensemble, the sealed replica seeds) passed at 59.2 s.
- Method attempt 1 ran the ensemble in 37.0 s (baseline 58.4 s, about 1.58×) and wrote `run/ensemble.json` and `run/method.log`. The baseline's harness writes `run/ensemble.json` and `run/baseline.log`. The frozen tests read `run/baseline.log` from both `BASELINE_OUT` and `METHOD_OUT`, so all eight cases failed `missing_output` before comparing anything.
- The method repair received only `{"missing_output": 8}`. It rewrote the method (attempt 2: 72.2 s, slower than the baseline) and kept `method.log`, so it failed the same way.
- Check: with attempt 2's `method.log` renamed to `run/baseline.log`, run15's `check_outputs.py` passes 8 of 8 against the reproduce outputs.
- Root cause: the contract requires the method to write "exactly the baseline's ... relative output locations", but the baseline outputs mix harness artifacts (`probe.json`, `setup.log`) with outputs, and a stdout log named `baseline.log` reads like a harness file. Nothing checks the rule before the blind tests, and by design the repair learns only reason-code counts.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| A100 SXM4 0.5, A10 0.2, H100 SXM5 0.12, H100 PCIe 0.13, A100 PCIe 0.05 | A100 SXM4 | yes (0.5, the mode) |
| intake PASS 0.95 | PASS | yes |
| reproduce PASS 0.93; 55 to 65 s on A100 | PASS; 58.4 s | yes; yes |
| profile PASS 0.95; every receipt fetched 0.95; MPS verified 0.92; A100 headroom 1.78 [1.6, 2.0] | PASS; yes; yes; 1.76 | yes; yes; yes; yes |
| seal PASS 0.85; first attempt `protocol_cost` 0.2 | PASS; no repair | yes; yes (against 0.2) |
| replica seeds of one ensemble 0.6; projection ≤ 2,160 s 0.85; margins cite reproduce 0.9; curve not applicable 0.85 | yes; 1,402 s; cited; yes | yes; yes; yes; yes |
| `baseline_invocation_s` within ±30% of the passing smoke 0.7 | 116.8 s against 59.2 s (+97%) | no |
| propose approved 0.88; ensembles 0.5 | approved 5/5; ensembles | yes; yes |
| implement reached 0.62 | reached | yes |
| first smoke fails 0.6; `cost` 0.75, `metrics` 0.15 | fails; `metrics` | yes; no (0.15 on the outcome) |
| repair makes second smoke pass 0.8; VOID at smoke 0.12 | passes; no | yes; yes (against 0.12) |
| passing smoke's process_wall_s 55 to 80 s on A100 for one ensemble | 59.2 s | yes |
| implement PASS 0.55; method repair used 0.3 | FAIL; used | no; no (0.3) |
| evaluate reached 0.34, and all given-evaluate predictions | not reached | yes (against 0.34); n/a |
| takeaways PASS 0.95; run_box_usd 1.3 to 6 if the run stops before evaluate | PASS; 2.24 | yes; yes |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |
| end-to-end PASS 0.19 | no | yes (against 0.19) |

## What changed my mind
- U36 worked as intended on its first real seal: told the budget, the seal chose 5 repetitions and stayed within it. Its estimate was about twice the measured smoke (an explicit overhead allowance). An overstated estimate can only make `protocol_cost` stricter than needed, never let an unaffordable protocol through.
- I expected the remaining implement risk in test content or equivalence. Instead the blind tests and the method disagreed on a log file name. Since the tests are blind by design, the method's only source for the output layout is the baseline outputs, which also hold harness artifacts. The rule was never checkable.
- The repair under counts-only feedback made the method worse (37 s to 72 s) without touching the cause.

## Fix
U37 (one gate: the method writes every output the frozen tests read). The test author also writes `tests/outputs.json`, `{"method_outputs": [paths]}`: every path the tests read under `METHOD_OUT`, each a regular file in its view's `baseline-out/`. It is frozen and hashed with the tests. The method author and method repair prompts list those paths. After `run_method.sh` exits 0 and before the tests, implement checks each path exists in the method's fetched `out/`. Otherwise the attempt fails with pipeline category `layout`, and the repair feedback adds `missing_paths`: baseline output locations, not test content. Regression: run15's frozen tests with `method_outputs` [`run/ensemble.json`, `run/baseline.log`] fail attempt 2's outputs as `layout` with `missing_paths` [`run/baseline.log`] and no test command. The same outputs with the log renamed pass the check and all eight frozen cases. Then run16 from the same brief.

## Later unit candidates (carried)
- Record meaning: the smoke could compare its measured `process_wall_s` with the sealed `baseline_invocation_s`. Smoke 1's 470 s against 116.8 s would flag the per-seed adapter. The seal's 2× allowance limits how tight that comparison can be.
- Smoke category in the signature: a second smoke failure maps every category except `timeout` to `error_class: parse`.
- Implement box operations fetch the whole `out/` tree (1.3 GB profile report) every time: implement uploads took 75 to 94 s each, and smoke 1's receipt 581 s for 470 s of work.
- An evaluator command that timed out gets one identical retry, which cannot succeed; the stage is labelled VOID `parse` instead of `timeout`.
- Implement signature `exit_kind: infra` with `error_class: numeric` for a test failure (seen again here).
- Propose with an empty menu built on missing measurements is FAIL `numeric`; VOID `infra` would separate it from a failed method.
- boxrun keeps no fetch error text.
- Identity smoke: frozen tests against the baseline as method, before the method author. It would not have caught run15.
- `test_m5_reproduce.js` intermittent failure.
