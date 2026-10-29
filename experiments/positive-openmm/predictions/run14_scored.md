# positive-openmm run14: outcome against sealed predictions (predictions/run14.md, 53b226c)

Run committed f947c01. Box gpu_1x_a100_sxm4, USD 1.99/h; run_box_usd 1.91; 0.73M tokens in; wall 3,450 s; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Implement VOID at the adapter smoke, evaluate skipped. The VOID is the correct abstention, and U34 caught the cause, but late: the seal chose a protocol whose complete performance scorer cannot fit the evaluate budget. No adapter faithful to the seal could have passed.

- Intake through propose passed on the A100 SXM4. Sequential ensemble 58.6 s; concurrency factor 1.77, MPS verified. U35 worked: `reproduce-freeze` exited 0 and fetched in 17 s, and the implement snapshot from `reproduce-out/` exited 0.
- Seal: 16 seeds (2000 to 2015) in two fixed blocks of eight replicas, so one evaluation invocation is two ensembles; repetitions 12, warmup 0; outcome curve not applicable; margins 38.6 (mean) and 103.5 (final) kJ/mol from reproduce. Its timing scope cites the measured 58.56 s ensemble. Propose approved `data-parallel over inputs` 5 of 5, expected 1.36.
- Smoke 1: the pre-seal adapter ran one whole ensemble per sealed seed (16 ensembles, 944 s) and failed `cost` (projected 22,671 s). The repair ran the sealed meaning, two blocks of eight replicas (118.6 s). Smoke 2 passed records and metrics and failed `cost`: 12 × 2 × 118.6 = 2,846 s against 0.9 × 2,400 = 2,160 s. Implement stopped before any test or method author call.
- Root cause: the seal author is never told the evaluate budget, and nothing checks the sealed protocol's cost before implement. At the seal's own measured cost, 16 seeds and 12 repetitions need about 2,830 s; 8 or 9 repetitions would have fit. The smoke is the first place the cost is checked, about 35 minutes and two adapter runs later, and it cannot repair a seal.
- The signature reads `error_class: parse`, because a second smoke failure of any category except `timeout` maps to `parse`. The category (`cost`) is visible only in the repair prompt and the smoke outputs.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| A100 SXM4 0.45, A10 0.25, H100 SXM5 0.12, H100 PCIe 0.13, A100 PCIe 0.05 | A100 SXM4 | yes (0.45, the mode) |
| intake PASS 0.95 | PASS | yes |
| reproduce PASS 0.92; freeze rc 0 and fetched 0.97; 55 to 65 s on A100 | PASS; yes (17 s); 58.6 s | yes; yes; yes |
| profile PASS 0.95; every receipt fetched 0.95; MPS verified 0.92; A100 headroom 1.78 [1.6, 2.0] | PASS; yes; yes; 1.77 | yes; yes; yes; yes |
| seal PASS 0.9; margins cite reproduce 0.9; replica seeds of one ensemble 0.75; curve not applicable 0.85 | PASS; cited; two blocks of eight (16 seeds); yes | yes; yes; no; yes |
| propose approved 0.88; ensembles 0.55, data-parallel over inputs 0.4 | approved 5/5; data-parallel over inputs | yes; no (0.4 on the outcome) |
| implement reached 0.65 | reached | yes |
| baseline-out holds one baseline run 0.95 | not observed (remote `baseline-out/` is not fetched; tests never ran) | n/a |
| first smoke fails 0.6; category `cost` 0.7 | fails; `cost` | yes; yes |
| repair makes second smoke pass 0.75; VOID at smoke 0.15 | fails `cost`; VOID | no; no (0.15) |
| passing smoke's process_wall_s 55 to 80 s on A100 | no passing smoke; the faithful adapter took 118.6 s (two ensembles) | n/a |
| a smoke receipt timed out by the whole-`out/` fetch 0.1 | no (smoke 1 receipt 1,135 s for 944 s of work) | yes (against 0.1) |
| implement PASS 0.6; method repair used 0.25 | VOID; no method author | no; n/a |
| evaluate reached 0.39, and all given-evaluate predictions | not reached | yes (against 0.39); n/a |
| takeaways PASS 0.95; run_box_usd 1.3 to 6 if the run stops before evaluate | PASS; 1.91 | yes; yes |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |
| end-to-end PASS 0.23 | no | yes (against 0.23) |

## What changed my mind
- I priced the smoke risk as the adapter's meaning, which the repair has now fixed twice. I did not price the seal's own cost: runs 10 to 13 sealed eight seeds, and I assumed this seal would too. With 16 seeds the faithful invocation doubles, and the sealed repetitions no longer fit.
- The seal had every number it needed except the budget: it measured the ensemble at 58.56 s and wrote that two blocks run per arm. "Seal cost against the evaluate budget" has been a candidate since run11; it is now the binding failure.
- The adapter repair kept the sealed meaning under cost pressure instead of cutting work, as in run13.

## Fix
U36 (one gate: the seal's protocol must fit the evaluate budget at the seal's own estimate). The seal prompt states the resolved evaluate budget and the scorer projection. The seal declares `baseline_invocation_s` = {seconds, source}: the expected process wall of one complete baseline equivalence invocation over the sealed seeds and inputs, derived from the reproduce measurements, with `source` naming the measured file and arithmetic. The deterministic seal check projects (warmup + repetitions) × 2 × seconds, plus curve bounds unless the curve is not applicable, and fails `protocol_cost` above 0.9 × the evaluate budget; the existing one seal repair gets the code and field paths. The U34 smoke stays as the measured check. Regression: run14's seal (warmup 0, repetitions 12, not applicable, two ensembles ≈ 118 s) fails `protocol_cost` against 2,400 s, and the same seal with 8 repetitions passes. Then run15 from the same brief.

## Later unit candidates (carried)
- Smoke category in the signature: a second smoke failure maps every category except `timeout` to `error_class: parse`, so a `cost` VOID reads as a parse failure.
- Record meaning: compare the smoke's measured `process_wall_s` with the sealed `baseline_invocation_s` (944 s against about 118 s here would flag the per-seed ensemble adapter by meaning, not only by cost).
- Implement box operations fetch the whole `out/` tree (1.3 GB profile report) every time: implement uploads took 127 to 171 s each, and smoke 1's receipt 1,135 s for 944 s of work.
- An evaluator command that timed out gets one identical retry, which cannot succeed; the stage is labelled VOID `parse` instead of `timeout`.
- Implement signature `exit_kind: infra` with `error_class: numeric` for a test failure.
- Propose with an empty menu built on missing measurements is FAIL `numeric`; VOID `infra` would separate it from a failed method.
- boxrun keeps no fetch error text.
- Identity smoke: frozen tests against the baseline as method, before the method author.
- `test_m5_reproduce.js` intermittent failure (once more in the U35 chain; passed a full rerun).
