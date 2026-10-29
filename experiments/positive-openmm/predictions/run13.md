# Sealed operator predictions: positive-openmm run13

Written and committed before launch. Run13 starts from the same brief as runs 1 to 12 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from earlier runs: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`, chain safety limits 5.8 h (pipeline) and 6 h (box). Pipeline code is at 414c587: U34 (the adapter smoke records `process_wall_s` and fails with category `cost` when (warmup + repetitions) × 2 × that wall, plus curve bounds, exceeds 0.9 × the evaluate budget; the one repair receives the numbers). Probabilities are mine; intervals are 80%.

Evidence used: run12 passed implement for the first time and reached evaluate; validity and equivalence passed (paired differences within ±0.01 kJ/mol), and the performance scorer timed out because the pre-seal baseline adapter ran one whole ensemble per sealed seed (488 s per invocation on the A100, against about 60 s for one ensemble). The method run timed one ensemble at 38 s and the completed pairs gave 1.59. Runs 10 to 12 sealed the eight replica seeds of one ensemble. In run10 the adapter repair, given the seal, wrote an adapter that runs one ensemble and writes one record per replica seed.

## Box
- A100 SXM4 0.35, A10 0.3, H100 SXM5 0.15, H100 PCIe 0.15, A100 PCIe 0.05.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.95 |
| reproduce | PASS 0.93 given intake PASS. Sequential ensemble 40 to 55 s on H100, 55 to 65 s on A100, 58 to 68 s on A10 |
| profile | PASS 0.95 given reproduce PASS; every receipt fetched 0.95; concurrency measured and MPS verified 0.92; headroom median 1.95 [1.7, 2.3] on H100, 1.78 [1.6, 2.0] on A100, 1.3 [1.15, 1.45] on A10 |
| seal | PASS 0.9 given profile PASS; margins cite reproduce outputs 0.9; seeds are the replica seeds of one ensemble 0.75; outcome curve not applicable 0.85 |
| propose | approved 0.88 given seal PASS; ensembles 0.55, data-parallel over inputs 0.4 |
| implement | reached 0.7 overall. Given reached: first adapter smoke fails 0.65; given it fails, category `cost` 0.5, `metrics` 0.35, `records` 0.1; repair makes the second smoke pass 0.7; implement VOID at the smoke 0.2; a passing smoke's process_wall_s 55 to 80 s on A100, 60 to 85 s on A10, 40 to 65 s on H100; test author reads only representative outputs 0.9; implement PASS 0.55; method repair used 0.3 |
| evaluate | reached 0.4 overall. Given reached: the performance scorer finishes within its budget 0.85; validity_pass 0.9; equivalence_pass 0.8 (paired differences within readout noise 0.7); performance_pass 0.75; speedup_published 1.5 to 2.1 on H100, 1.4 to 1.8 on A100, 1.1 to 1.35 on A10; evaluate PASS 0.6 |
| takeaways | PASS 0.95; run_box_usd 1.3 to 6 if the run stops before evaluate, 3 to 10 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.7; reaches evaluate 0.4; end-to-end PASS 0.24.

## What would change my mind
- A repair given `cost` that cuts work (fewer steps, replicas or seeds) instead of matching the sealed meaning: the cost gate passes but records no longer mean the sealed executions; the record-meaning check becomes the next unit.
- Second smoke fails `cost`: the harness role cannot recover the sealed meaning from a cost signal, and the evaluation adapter needs to be authored after the seal.
- First smoke passes with a process_wall_s several times the reproduce ensemble: the projection or its budget resolution is wrong.
- Evaluate performance timeout with the smoke passed: the method arm costs far more than the baseline, or the scorer has overhead the projection misses.
- Evaluate performance FAIL with median ratio above 1.05 but the lower bound below it: repetitions too few for the margin.
