# Sealed operator predictions: positive-openmm run11

Written and committed before launch. Run11 starts from the same brief as runs 1 to 10 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from earlier runs: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`, chain safety limits 5.8 h (pipeline) and 6 h (box). Pipeline code is at 5cf2a09 (U32): the implement adapter smoke passes the sealed seeds unchanged, so it is one complete baseline equivalence invocation, and requires one record per sealed seed and input, seeds first. Probabilities are mine; intervals are 80%.

Evidence used: runs 6 to 10 all passed intake to propose. Runs 9 and 10 both had a pre-seal baseline adapter that wrote records without the sealed metric names. In run10 the repair, given the seal, wrote an adapter that matched the seal's seed meaning and metric names, and implement stopped only because U31's smoke cut the seeds to one. The A10 was the box for runs 8, 9 and 10.

Cost reasoning: the smoke now runs the full sealed seed list once. When the seeds are one ensemble's replicas, that is one ensemble (about 60 s on an A10) plus about 370 s of box-operation overhead per implement operation (whole `out/` fetch, queued candidate).

## Box
- H100 SXM5 0.25, H100 PCIe 0.25, A100 SXM4 0.1, A100 PCIe 0.05, A10 0.35.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.95 |
| reproduce | PASS 0.93 given intake PASS. Sequential ensemble 40 to 55 s on H100, 55 to 65 s on A100, 58 to 68 s on A10 |
| profile | PASS 0.95 given reproduce PASS; MPS verified 0.93; headroom median 1.95 [1.7, 2.3] on H100, 1.78 [1.6, 2.0] on A100, 1.3 [1.15, 1.45] on A10 |
| seal | PASS 0.9 given profile PASS; margins cite reproduce outputs 0.9; seeds are the replica seeds of one ensemble 0.65 |
| propose | approved 0.9 given seal PASS; ensembles 0.5, data-parallel over inputs 0.45 |
| implement | reached 0.7 overall. Given reached: first adapter smoke fails 0.7; given it fails, category `metrics` 0.65, `records` 0.25; repair makes the second smoke pass 0.8; implement VOID at the smoke 0.15; test author reads only representative outputs 0.9; implement PASS 0.55; method repair used 0.35 |
| evaluate | reached 0.38 overall. Given reached: every adapter run writes valid measurements 0.8; an evaluation script hits its per-run budget 0.2; validity_pass 0.85; equivalence_pass 0.7 (paired differences within readout noise 0.65); performance_pass 0.6; speedup_published 1.4 to 2.1 on H100, 1.3 to 1.8 on A100, 1.1 to 1.3 on A10; evaluate PASS 0.4 |
| takeaways | PASS 0.95; run_box_usd 1.5 to 6 if the run stops before evaluate, 3 to 25 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.7; reaches evaluate 0.38; end-to-end PASS 0.15.

## What would change my mind
- Second smoke fails `records` or `metrics` after a repair under the full seeds: the harness role cannot map the seal onto the workload even with the seal in hand, and the adapter needs to be authored after the seal from the start.
- Smoke passes but evaluate equivalence FAIL with differences near the between-seed spread on every seed: the two adapters still mean different executions; the record-meaning statement needs an executable check.
- Evaluate timeout at fixed work: the seal's repetitions do not fit the evaluate budget at the measured ensemble cost (queued candidate).
- Evaluate performance FAIL with median ratio above 1.05 but the lower bound below it: repetitions too few for the A10's small margin.
