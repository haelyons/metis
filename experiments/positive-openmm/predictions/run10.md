# Sealed operator predictions: positive-openmm run10

Written and committed before launch. Run10 starts from the same brief as runs 1 to 9 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from earlier runs: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`, chain safety limits 5.8 h (pipeline) and 6 h (box). Pipeline code is at 691bc09 (U31): before any test or method author call, implement smoke-runs the baseline evaluation adapter with the seal (equivalence mode, first sealed seed), requiring the evaluator's record rules and every sealed metric name; one harness repair with the seal may rewrite only `run_evaluation.sh`; a second failure stops implement VOID. Probabilities are mine; intervals are 80%.

Evidence used: runs 6 to 9 all passed intake to propose. Run9 passed implement cleanly (U30 held; method in MPS worker waves without an SM cap; per-seed energies within 0.02 kJ/mol of the baseline's; 1.26 at representative scale on an A10), then evaluate was VOID because the pre-seal baseline adapter ran each seed as an ensemble and lacked the sealed metric names. The harness writes `run_evaluation.sh` before the seal, so it cannot know the sealed names; I expect most first smokes to fail on `metrics` or `records` and the repair, which sees the seal, to fix them.

Cost reasoning: under the seal's per-replica seed meaning, one equivalence arm is one ensemble (about 50 to 65 s). Performance repeats both arms 5 to 32 times, and curves add budgeted runs; at run9's 16 repetitions that is about 1,800 s on an A10 for performance alone, inside 2,400 s but with little margin, and well inside on an H100.

## Box
- H100 SXM5 0.3, H100 PCIe 0.3, A100 SXM4 0.15, A100 PCIe 0.05, A10 0.2.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.93 |
| reproduce | PASS 0.9 given intake PASS. Sequential ensemble 40 to 55 s on H100, 55 to 65 s on A100, 58 to 68 s on A10 |
| profile | PASS 0.93 given reproduce PASS; MPS verified 0.93; headroom median 1.95 [1.7, 2.3] on H100, 1.78 [1.6, 2.0] on A100, 1.3 [1.15, 1.45] on A10 |
| seal | PASS 0.85 given profile PASS; margins cite reproduce outputs 0.9; seeds are the replica seeds of one ensemble 0.6 |
| propose | approved 0.85 given seal PASS; ensembles 0.55, data-parallel over inputs 0.4 |
| implement | reached 0.72 overall. Given reached: first adapter smoke fails 0.65; given it fails, category `metrics` 0.6, `records` 0.3; repair makes the second smoke pass 0.8; implement VOID at the smoke 0.15; test author reads only representative outputs 0.9; implement PASS 0.6; method repair used 0.35 |
| evaluate | reached 0.43 overall. Given reached: every adapter run writes valid measurements 0.8; an evaluation script hits its 2,400 s budget 0.3; validity_pass 0.85; equivalence_pass 0.7 (paired differences within readout noise 0.65); performance_pass 0.6; speedup_published 1.4 to 2.1 on H100, 1.3 to 1.8 on A100, 1.1 to 1.35 on A10; evaluate PASS 0.4 |
| takeaways | PASS 0.95; run_box_usd 1.5 to 6 if the run stops before evaluate, 2.5 to 25 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.72; reaches evaluate 0.43; end-to-end PASS 0.17.

## What would change my mind
- Implement VOID at the smoke after a repair: the harness role cannot map the seal's seeds and metric names onto the workload even with the seal in hand; the adapter needs to be authored after the seal from the start.
- Smoke passes but evaluate equivalence FAIL with differences near the between-seed spread on every seed: the two adapters still mean different executions (for example an ensemble average against one replica); the record-meaning statement is not enough and needs an executable check.
- Evaluate timeout in performance at fixed work: the seal's repetitions do not fit the evaluate budget at the measured ensemble cost (queued candidate).
- Evaluate performance FAIL with median ratio above 1.05 but the lower bound below it: repetitions too few for the A10's small margin.
