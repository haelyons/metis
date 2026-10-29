# Sealed operator predictions: positive-openmm run14

Written and committed before launch. Run14 starts from the same brief as runs 1 to 13 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from earlier runs: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`, chain safety limits 5.8 h (pipeline) and 6 h (box). Pipeline code is at 99f9ae0: U35 (when reproduce passes, a `reproduce-freeze` box command copies the anchor run's `out/` to `reproduce-out/`; implement's `baseline-out/` is a copy of `reproduce-out/`, so the frozen tests run against the baseline outputs their author saw). Probabilities are mine; intervals are 80%.

Evidence used: run13 reached implement on an A100 SXM4. The U34 smoke failed `cost` on the per-seed ensemble adapter (491 s), and the repair's adapter (one ensemble, replica seeds 1000 to 1007) passed at 60.9 s. The method ran in 58 s. The frozen tests failed all nine cases `invalid_output` because `BASELINE_OUT` held a second baseline run made during profiling; U35 removes that cause. Run12 passed implement, validity and equivalence (paired differences within ±0.01 kJ/mol) and gave raw pairs at ratio 1.59 before its scorer timed out. Runs 11 to 13 all got an A100 SXM4.

## Box
- A100 SXM4 0.45, A10 0.25, H100 SXM5 0.12, H100 PCIe 0.13, A100 PCIe 0.05.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.95 |
| reproduce | PASS 0.92 given intake PASS (the freeze adds one box command); `reproduce-freeze` receipt rc 0 and fetched 0.97 given the anchors pass. Sequential ensemble 40 to 55 s on H100, 55 to 65 s on A100, 58 to 68 s on A10 |
| profile | PASS 0.95 given reproduce PASS; every receipt fetched 0.95; concurrency measured and MPS verified 0.92; headroom median 1.95 [1.7, 2.3] on H100, 1.78 [1.6, 2.0] on A100, 1.3 [1.15, 1.45] on A10 |
| seal | PASS 0.9 given profile PASS; margins cite reproduce outputs 0.9; seeds are the replica seeds of one ensemble 0.75; outcome curve not applicable 0.85 |
| propose | approved 0.88 given seal PASS; ensembles 0.55, data-parallel over inputs 0.4 |
| implement | reached 0.65 overall. Given reached: `baseline-out/` holds exactly one baseline run 0.95; first adapter smoke fails 0.6; given it fails, category `cost` 0.7, `metrics` 0.2, `records` 0.1; repair makes the second smoke pass 0.75; implement VOID at the smoke 0.15; a passing smoke's process_wall_s 55 to 80 s on A100, 60 to 85 s on A10, 40 to 65 s on H100; a smoke receipt timed out by the whole-`out/` fetch 0.1; implement PASS 0.6; method repair used 0.25 |
| evaluate | reached 0.39 overall. Given reached: the performance scorer finishes within its budget 0.85; validity_pass 0.9; equivalence_pass 0.8 (paired differences within readout noise 0.7); performance_pass 0.75; speedup_published 1.5 to 2.1 on H100, 1.4 to 1.8 on A100, 1.1 to 1.35 on A10; evaluate PASS 0.6 |
| takeaways | PASS 0.95; run_box_usd 1.3 to 6 if the run stops before evaluate, 3.5 to 9 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.65; reaches evaluate 0.39; end-to-end PASS 0.23.

## What would change my mind
- Frozen tests fail `invalid_output` again with one baseline run in `baseline-out/`: the tests reject something else in the frozen outputs, and an identity smoke (frozen tests with the baseline as method) becomes the next unit.
- Reproduce FAIL `infra` at `reproduce-freeze`: the freeze command or its fetch fails on a real box, which the fake-box tests did not reproduce.
- A smoke or method receipt that times out while its command finished: the whole-`out/` fetch (1.3 GB profile report) becomes the next unit.
- Evaluate performance timeout with the smoke passed: the method arm costs far more than the baseline, or the scorer has overhead the projection misses.
- Evaluate performance FAIL with median ratio above 1.05 but the lower bound below it: repetitions too few for the margin.
