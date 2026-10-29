# positive-openmm run12: outcome against sealed predictions (predictions/run12.md, 4396900)

Run committed 8b75850. Box gpu_1x_a100_sxm4, USD 1.99/h; run_box_usd 6.35; 2.15M tokens in; wall 11,485 s; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Evaluate VOID: the performance scorer timed out at 2,449 s against its 2,400 s budget, after validity and equivalence passed. This is the first run to pass implement and to measure the method in evaluate. The VOID is the correct abstention: the timing pairs were incomplete, so no performance verdict was given.

- Intake through propose passed on the A100 SXM4. Sequential ensemble 59.0 s; concurrency measured, MPS verified, factor 1.81. The seal's seeds are the eight replica seeds of one ensemble; margins SD/sqrt(8) from reproduce (103.5 kJ/mol final, 38.6 mean); repetitions 8, warmup 1, outcome curve not applicable. Propose approved `ensembles` 5 of 5, expected 1.42.
- Implement PASS with no repair anywhere. The U32 smoke passed on its first attempt (pre-seal adapter, full sealed seeds, eight records keyed by the sealed metric names). Method: four MPS worker processes; method run 70 s; frozen tests passed; review passed.
- Evaluate validity PASS (the method's measured throughput reference 1.82 against the published 5, reference only). Equivalence PASS: the paired differences are within ±0.01 kJ/mol on both metrics, against margins of 103 and 39.
- Performance: warmup and two of eight timing pairs completed (baseline 488 s and method 306 s per invocation, ratio 1.59) before the 2,400 s budget ran out. The scorer's one identical retry exited 2 in 38 s, and performance.json is VOID `missing_or_invalid_measurements`.
- Root cause: the baseline adapter runs one whole eight-replica ensemble per sealed seed (seed0 = that seed) and reports the average over replicas. One invocation is therefore eight ensembles (about 488 s), not the one ensemble the seal describes ("each replica uses its seed"; about 60 s). Records for neighbouring seeds share seven of eight replicas, and seeds up to 1014 run, outside the brief's 1000 to 1007. The method adapter copies the same meaning, so equivalence is consistent, but every invocation costs eight times the sealed workload. (Warmup + 8) × 2 arms × 488 s is about 8,800 s; with the sealed meaning it is about 1,000 s.
- The U32 smoke checks the shape of the records, not their cost or meaning, so this adapter passed it and the overrun appeared only after about 2.5 h of implement and evaluate.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.2, H100 PCIe 0.2, A100 SXM4 0.2, A100 PCIe 0.05, A10 0.35 | A100 SXM4 | no (0.2) |
| intake PASS 0.95 | PASS | yes |
| reproduce PASS 0.93; 55 to 65 s on A100 | PASS; 59.0 s | yes; yes |
| profile PASS 0.95; every receipt fetched 0.95; MPS verified 0.92; A100 headroom 1.78 [1.6, 2.0] | PASS; yes; yes; 1.81 | yes; yes; yes; yes |
| seal PASS 0.9; margins cite reproduce 0.9; seeds are one ensemble's replica seeds 0.65 | PASS; cited; yes | yes; yes; yes |
| propose approved 0.88; ensembles 0.5 | approved 5/5; ensembles | yes; yes |
| implement reached 0.66 | reached | yes |
| first adapter smoke fails 0.7 | passed first time | no |
| category / repair / VOID-at-smoke predictions | no smoke failure | n/a; VOID at smoke 0.15: no, yes against |
| test author reads only representative outputs 0.9 | tests read BASELINE_OUT and METHOD_OUT only | yes |
| implement PASS 0.55; method repair 0.35 | PASS; no repair | yes; yes (against 0.35) |
| evaluate reached 0.36 | reached | yes |
| every adapter run writes valid measurements 0.8 | every completed run valid; one killed by the scorer timeout | yes |
| an evaluation script hits its per-run budget 0.2 | no invocation near 1,200 s; the scorer budget was hit | no for per-run; the scorer overran |
| validity_pass 0.85; equivalence_pass 0.7; within readout noise 0.65 | PASS; PASS; ±0.01 kJ/mol | yes; yes; yes |
| performance_pass 0.6 | null (VOID) | no |
| speedup_published 1.3 to 1.8 on A100 | not scored; raw pairs 1.59 | n/a (raw within interval) |
| evaluate PASS 0.4 | VOID | no |
| takeaways PASS 0.95; run_box_usd 3 to 25 if evaluate reached | PASS; 6.35 | yes; yes |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |
| end-to-end PASS 0.14 | no | yes (against 0.14) |

## What changed my mind
- I expected the risk at the smoke: the pre-seal adapter would fail on names and need the repair. Instead it passed the shape check with a different meaning. A shape smoke cannot tell "one record per seed" from "one record per seed, each a whole ensemble".
- My "what would change my mind" item for a timeout blamed the seal's repetitions at measured ensemble cost. That is wrong for this run: at the sealed meaning the repetitions fit the budget (about 1,000 s of 2,400). The overrun comes from the adapter's invocation cost, which nothing measures before evaluate.
- The method itself behaves as a positive control should: equivalence holds to within readout noise, and the two completed pairs give 1.59, inside my A100 interval.

## Fix
U34 (one gate: the smoke checks its measured cost against the evaluate budget). The smoke script times the adapter with a monotonic clock and records `process_wall_s`. From it, implement projects one complete performance scorer: (sealed warmup + sealed repetitions) × 2 arms × process_wall_s, plus the curve's per-invocation bounds when an outcome curve applies. The smoke fails with category `cost` when the projection exceeds 0.9 × the evaluate budget, and the one adapter repair receives the measured wall, the projection and the budget. Regression: run12's seal with a 488 s smoke fails `cost`; the same seal with a 60 s smoke passes. Then run13 from the same brief.

## Later unit candidates (carried)
- Record meaning: an executable check that the adapter's records mean the sealed executions (here, one ensemble whose replicas carry the sealed seeds), beyond cost.
- An evaluator command that timed out gets one identical retry, which cannot succeed: it reuses the workspace and exits 2 at once, and the stage is labelled VOID `parse` instead of `timeout`.
- Implement box operations fetch the whole `out/` tree (1.3 GB profile report) every time: the 489 s smoke took a 1,014 s receipt.
- Propose with an empty menu built on missing measurements is FAIL `numeric`; VOID `infra` would separate it from a failed method more clearly.
- boxrun keeps no fetch error text.
- Identity smoke: frozen tests against the baseline as method, before the method author.
- Implement signature `exit_kind: infra` with `error_class: numeric` for a test failure.
- `test_m5_reproduce.js` `concurrency-real-mps-cleared` intermittent failure.
