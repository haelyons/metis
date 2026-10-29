# Sealed operator predictions: positive-openmm run15

Written and committed before launch. Run15 starts from the same brief as runs 1 to 14 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from earlier runs: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`, chain safety limits 5.8 h (pipeline) and 6 h (box). Pipeline code is at aa4405e: U36 (the seal declares `baseline_invocation_s` {seconds, source} from the reproduce measurements; the seal check fails `protocol_cost` when (warmup + repetitions) × 2 × seconds, plus curve bounds, exceeds 0.9 × the evaluate budget; the seal and repair prompts state the budget). Probabilities are mine; intervals are 80%.

Evidence used: run14 passed intake through propose on an A100 SXM4 (ensemble 58.6 s, factor 1.77) and its U35 freeze worked on the box. Its seal sealed 16 seeds in two blocks of eight, warmup 0, repetitions 12, without knowing the evaluate budget; the faithful adapter measured 118.6 s and the U34 smoke failed `cost` (2,846 s against 2,160 s), so implement went VOID. In runs 13 and 14 the pre-seal adapter ran one ensemble per sealed seed and failed `cost` at the first smoke; both repairs wrote the sealed meaning. Run12 passed implement, validity and equivalence (±0.01 kJ/mol) and gave raw pairs at ratio 1.59.

## Box
- A100 SXM4 0.5, A10 0.2, H100 SXM5 0.12, H100 PCIe 0.13, A100 PCIe 0.05.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.95 |
| reproduce | PASS 0.93 given intake PASS. Sequential ensemble 40 to 55 s on H100, 55 to 65 s on A100, 58 to 68 s on A10 |
| profile | PASS 0.95 given reproduce PASS; every receipt fetched 0.95; concurrency measured and MPS verified 0.92; headroom median 1.95 [1.7, 2.3] on H100, 1.78 [1.6, 2.0] on A100, 1.3 [1.15, 1.45] on A10 |
| seal | PASS 0.85 given profile PASS; first attempt fails `protocol_cost` 0.2, and given that the repair fits 0.8; seeds are the replica seeds of one ensemble 0.6, two blocks of eight 0.3; sealed projection at most 2,160 s 0.85 given PASS; `baseline_invocation_s.seconds` within ±30% of the passing smoke's process_wall_s 0.7; margins cite reproduce outputs 0.9; outcome curve not applicable 0.85 |
| propose | approved 0.88 given seal PASS; ensembles 0.5, data-parallel over inputs 0.45 |
| implement | reached 0.62 overall. Given reached: first adapter smoke fails 0.6; given it fails, category `cost` 0.75, `metrics` 0.15, `records` 0.1; repair makes the second smoke pass 0.8; implement VOID at the smoke 0.12; a passing smoke's process_wall_s 55 to 80 s on A100 for one ensemble per invocation (110 to 150 s for two); implement PASS 0.55; method repair used 0.3 |
| evaluate | reached 0.34 overall. Given reached: the performance scorer finishes within its budget 0.85; validity_pass 0.9; equivalence_pass 0.8 (paired differences within readout noise 0.7); performance_pass 0.7; speedup_published 1.5 to 2.1 on H100, 1.4 to 1.8 on A100, 1.1 to 1.35 on A10; evaluate PASS 0.55 |
| takeaways | PASS 0.95; run_box_usd 1.3 to 6 if the run stops before evaluate, 3.5 to 9 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.62; reaches evaluate 0.34; end-to-end PASS 0.19.

## What would change my mind
- Seal FAIL `protocol_cost` after the repair: the seal author cannot fit the protocol even when told the budget; the budget or the minimum repetitions are the binding constraint, not the seal's knowledge.
- A sealed `seconds` far below the smoke's measured faithful wall (smoke fails `cost` with a seal that passed `protocol_cost`): the seal understates its cost, and the smoke should compare its measurement with the sealed estimate.
- Frozen tests fail `invalid_output` with `baseline-out/` from `reproduce-out/`: the tests reject something else in the frozen outputs; an identity smoke becomes the next unit.
- A smoke or method receipt that times out while its command finished: the whole-`out/` fetch becomes the next unit.
- Evaluate performance FAIL with median ratio above 1.05 but the lower bound below it: repetitions too few for the margin, now possibly because the seal cut repetitions to fit the budget.
