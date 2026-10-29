# positive-openmm run10: outcome against sealed predictions (predictions/run10.md, 3bd26b3)

Run committed b251b5f. Box gpu_1x_a10, USD 1.29/h; run_box_usd 1.80; 0.74M tokens in; wall 5,009 s; pipeline exit 0; box torn down; push verified by the chain.

## Verdict
Implement VOID at the U31 adapter smoke, before any test or method author call. The cause is in my U31 contract, not in the harness role: the smoke cut the sealed seeds to the first seed, an invocation evaluate never makes, and the repaired adapter correctly refused it.

- Intake to propose passed on the A10 for the third run running. Sequential ensemble 62.0 s; MPS verified, factor 1.29. Seal margins SD/sqrt(8) cited from reproduce's `ensemble.json` (192.2 kJ/mol final, 43.6 mean); the seal's seeds are the eight replica seeds of one ensemble. Propose approved `data-parallel over inputs` 5 of 5 (one input, eight seeded replicas as work items), expected 1.16.
- Smoke 1 (pre-seal adapter, `EVAL_SEEDS` cut to `[1000]`): exit 0, one record at seed 1000, but its metrics are `replica_<i>_*` fields with no sealed names: category `metrics`, as predicted. Same defect as run9.
- Repair (sees the seal): rewrote `run_evaluation.sh` to run the published ensemble once at `seed0=1000` and write one record per sealed replica seed, keyed by the sealed metric names. That matches the seal and the run9 method adapter. It also rejects any seed list other than the eight published replica seeds ("Execution seeds must preserve the published eight replica seeds").
- Smoke 2: the cut `[1000]` hit that check; exit 1 in seconds, no GPU work. Implement VOID, `error_class: parse`.
- Root cause: U31 cut `seeds` to one to save cost, and called that "exactly as an evaluate invocation". Evaluate always passes the whole sealed seed list. When the seal's seeds are the replicas of one execution, a one-seed subset is a different workload, and an adapter that refuses it is right.
- Cost note: every implement box operation took 368 to 440 s, including uploads that do no GPU work (pre-implement uploads took 7 to 11 s). Each one fetches the whole `out/` tree, including the 1.3 GB profile report. Implement's 7 box operations cost about 45 min of box time. Queued as a candidate, not a gate.

## Scores
| Prediction | Outcome | Hit |
|---|---|---|
| H100 SXM5 0.3, H100 PCIe 0.3, A100 SXM4 0.15, A100 PCIe 0.05, A10 0.2 | A10 | no (0.2) |
| intake PASS 0.93 | PASS | yes |
| reproduce PASS 0.9; 58 to 68 s on A10 | PASS; 62.0 s | yes; yes |
| profile PASS 0.93; MPS verified 0.93; A10 headroom 1.3 [1.15, 1.45] | PASS; verified; 1.29 | yes; yes; yes |
| seal PASS 0.85; margins cite reproduce 0.9; seeds are one ensemble's replica seeds 0.6 | PASS; cited; yes | yes; yes; yes |
| propose approved 0.85; ensembles 0.55, data-parallel 0.4 | approved 5/5; data-parallel | yes; no (0.4) |
| implement reached 0.72 | reached | yes |
| first adapter smoke fails 0.65; category `metrics` 0.6 | fails; `metrics` | yes; yes |
| repair makes the second smoke pass 0.8 | no (smoke's seed cut) | no |
| implement VOID at the smoke 0.15 | VOID | yes (against 0.15) |
| test author reads only representative outputs 0.9; implement PASS 0.6; method repair 0.35 | not reached | n/a |
| evaluate reached 0.43, and all given-evaluate predictions | not reached | no; n/a |
| takeaways PASS 0.95 | PASS | yes |
| run_box_usd 1.5 to 6 if the run stops before evaluate | 1.80 | yes |
| pipeline exit 0, box torn down, push verified 0.9 | yes | yes |
| end-to-end PASS 0.17 | no | yes (against 0.17) |

## What changed my mind
- My sealed reading of "VOID at the smoke after a repair" was wrong for this run. I said it would mean the harness role cannot map the seal onto the workload. Here the repair mapped it correctly and my smoke asked for a workload the seal does not define. A smoke only tests what evaluate will do if it sends exactly what evaluate sends.
- The repaired adapter is evidence that the U31 repair path works: with the seal in hand, the harness role wrote records that match the sealed seed meaning and metric names.

## Fix
U32 (one gate: the smoke passes the sealed seeds unchanged). The smoke's `EVAL_SEEDS` is the sealed `paired_seed_tests` object as is, so the smoke is one complete baseline equivalence invocation, and it passes only with one record per sealed seed and input, seeds first, in sealed order. Regression: run10's repaired `run_evaluation.sh` with run10's seal passes the smoke (stand-in driver); the same script under the old one-seed cut exits nonzero; run9's script still fails on `metrics`. Then run11 from the same brief.

## Later unit candidates (carried)
- Implement box operations fetch the whole `out/` tree (1.3 GB profile report) every time: about 6 min per operation on the A10.
- Identity smoke: frozen tests against the baseline as method, before the method author.
- Seal cost against the evaluate budget at measured ensemble cost.
- Implement signature `exit_kind: infra` with `error_class: numeric` for a test failure.
- `test_m5_reproduce.js` `concurrency-real-mps-cleared` intermittent failure (also seen through `test_m5_profile.js`).
