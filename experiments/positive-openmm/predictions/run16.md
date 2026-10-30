# Sealed operator predictions: positive-openmm run16

Written and committed before launch. Run16 starts from the same brief as runs 1 to 15 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from earlier runs: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`, chain safety limits 5.8 h (pipeline) and 6 h (box). Pipeline code is at a6a3ec4: U37 (the test author declares `tests/outputs.json` `method_outputs`, the paths its tests read under `METHOD_OUT`; the method author and repair prompts list them; after `run_method.sh` exits 0 a missing path fails the attempt as `layout`, before tests, and the repair gets `missing_paths`). Probabilities are mine; intervals are 80%.

Evidence used: run15 passed intake through propose on an A100 SXM4. U36's seal fit the budget on its first attempt (eight replica seeds of one ensemble, warmup 1, repetitions 5, `baseline_invocation_s` 116.8 s, projected 1,402 s). The pre-seal adapter again ran one ensemble per seed and failed the first smoke; the repaired adapter passed at 59.2 s. Method attempt 1 (ensembles) ran in 37.0 s against the baseline's 58.4 s, but wrote `run/method.log` where the frozen tests read `run/baseline.log`. With the log renamed, the frozen tests pass 8 of 8. Run12 passed validity and equivalence (±0.01 kJ/mol) and gave raw pairs at 1.59.

## Box
- A100 SXM4 0.55, A10 0.18, H100 SXM5 0.1, H100 PCIe 0.12, A100 PCIe 0.05.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.95 |
| reproduce | PASS 0.93 given intake PASS. Sequential ensemble 40 to 55 s on H100, 55 to 65 s on A100, 58 to 68 s on A10 |
| profile | PASS 0.95 given reproduce PASS; every receipt fetched 0.95; concurrency measured and MPS verified 0.92; headroom median 1.95 [1.7, 2.3] on H100, 1.77 [1.6, 2.0] on A100, 1.3 [1.15, 1.45] on A10 |
| seal | PASS 0.88 given profile PASS; first attempt fails `protocol_cost` 0.15; seeds are the replica seeds of one ensemble 0.7; margins cite reproduce outputs 0.9; outcome curve not applicable 0.85 |
| propose | approved 0.88 given seal PASS; ensembles 0.55, data-parallel over inputs 0.4 |
| implement | reached 0.65 overall. Given reached: first adapter smoke fails 0.65, and the repair makes the second pass 0.8; implement VOID at the smoke 0.12; a passing smoke's process_wall_s 55 to 80 s on A100 for one ensemble; test author writes a valid `outputs.json` 0.9; the method writes every `method_outputs` path on attempt 1 0.75; a `layout` failure on some attempt 0.2; implement PASS 0.6; method repair used 0.3 |
| evaluate | reached 0.39 overall. Given reached: the performance scorer finishes within its budget 0.9; validity_pass 0.9; equivalence_pass 0.8 (paired differences within readout noise 0.7); performance_pass 0.7; speedup_published 1.5 to 2.1 on H100, 1.4 to 1.8 on A100, 1.1 to 1.35 on A10; evaluate PASS 0.6 |
| takeaways | PASS 0.95; run_box_usd 1.3 to 6 if the run stops before evaluate, 3 to 8 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.65; reaches evaluate 0.39; end-to-end PASS 0.23.

## What would change my mind
- Implement FAIL at the test author on an invalid `outputs.json`: the declaration rules are harder for the test author than the contract assumes.
- Tests fail `missing_output` after the layout check passed: the tests read a path they did not declare; the declaration needs to be checked against what the tests read.
- A `layout` failure that the repair does not fix even with `missing_paths`: the repair cannot act on path feedback without box access.
- Equivalence FAIL with tests passing: the representative pairs and the evaluation seeds disagree, or the method changes the science.
- Evaluate performance FAIL with median ratio above 1.05 but the lower bound below it: 5 repetitions too few for the margin.
