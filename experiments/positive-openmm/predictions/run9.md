# Sealed operator predictions: positive-openmm run9

Written and committed before launch. Run9 starts from the same brief as runs 1 to 8 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from earlier runs: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`, chain safety limits 5.8 h (pipeline) and 6 h (box). Pipeline code is at 0c5b112 (U30): the test author prompt says tests see only the baseline outputs and one method run, and the equivalence case fails only when the representative pairs reject equivalence under the sealed rule. Probabilities are mine; intervals are 80%.

Evidence used: runs 6 to 8 all passed intake to propose (H100 SXM5, H100 PCIe, A10). Run7 passed implement and was VOID in evaluate on the adapter input shape (fixed by U29, which held in run8). Run8 failed implement because its equivalence test required evaluation records that implement never produces. Run8's method capped each MPS client at 50% of the SMs, and its per-seed trajectories decorrelated from the baseline's (differences about one between-seed SD) while staying self-consistent; baseline reruns agree within 0.03 kJ/mol. Seals vary in size: run7 sealed 15 repetitions of one eight-seed ensemble per arm; run8 sealed 32 repetitions of four ensembles, about 8,000 s per arm per mode on an A10, against a 2,400 s evaluation script budget.

Equivalence reasoning: a method that keeps each replica's launch configuration (no SM cap) should reproduce baseline trajectories to readout noise, so paired differences are near zero and pass any sealed margin. A method that changes the configuration decorrelates trajectories: paired differences have SD about 1.4 between-seed SDs. Against a margin of SD/sqrt(8) that fails at any seed count; against a one-SD margin it passes with 32 seeds and cannot decide with 8. At implement, with 8 representative pairs, only a systematic shift can reject.

## Box
- H100 SXM5 0.35, H100 PCIe 0.3, A100 SXM4 0.15, A100 PCIe 0.05, A10 0.15.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.93 |
| reproduce | PASS 0.9 given intake PASS. Sequential ensemble 40 to 55 s on H100, 55 to 65 s on A100, 58 to 68 s on A10 |
| profile | PASS 0.93 given reproduce PASS; MPS verified 0.93; headroom median 1.95 [1.7, 2.3] on H100, 1.78 [1.6, 2.0] on A100, 1.3 [1.15, 1.45] on A10 |
| seal | PASS 0.85 given profile PASS; margins cite reproduce outputs 0.9; margin is one SD rather than SD/sqrt(n) 0.45; seal implies more than 2,400 s per evaluation script at the measured ensemble cost 0.45 |
| propose | approved 0.85 given seal PASS; data-parallel over inputs 0.5, ensembles 0.45 |
| implement | reached 0.65 overall. Given reached: test author's equivalence case reads only representative outputs 0.85; PASS 0.65; a method repair used 0.4; method caps MPS SMs per client 0.35 |
| evaluate | reached 0.4 overall. Given reached: every adapter run writes valid measurements 0.75; an evaluation script hits its 2400 s budget 0.4; validity_pass 0.85; equivalence_pass 0.5 (paired differences within readout noise 0.45); performance_pass 0.55; speedup_published 1.4 to 2.1 on H100, 1.3 to 1.8 on A100, 1.1 to 1.35 on A10; evaluate PASS 0.3 |
| takeaways | PASS 0.95; run_box_usd 1.5 to 6 if the run stops before evaluate, 5 to 25 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.65; reaches evaluate 0.4; end-to-end PASS 0.12.

## What would change my mind
- Implement FAIL with `equivalence` while paired intervals overlap the margin: the test author still writes per-seed or stricter-than-sealed checks; the prompt statement is not enough, and the identity smoke (tests against the baseline as method) becomes the next unit.
- Implement FAIL with `missing_output` again: the test author still reaches for evaluation records.
- Evaluate timeout at fixed work: the seal's repetitions by seeds do not fit the evaluate budget at the measured ensemble cost (queued candidate).
- Evaluate equivalence FAIL with paired differences near one SD and a margin of SD/sqrt(8): the method changed launch configuration; the seal and method are each defensible, and the result is a correct rejection under the sealed rule.
- Evaluate performance FAIL with median ratio above the minimum gain but a lower bound below it: repetitions too few for a stable bound.
