# Sealed operator predictions: positive-openmm run8

Written and committed before launch. Run8 starts from the same brief as runs 1 to 7 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from earlier runs: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`, chain safety limits 5.8 h (pipeline) and 6 h (box). Pipeline code is at ef99cc3 (U29): the harness and method author prompts state that `EVAL_INPUTS.ids` is the ordered input list (other keys never inputs) and the two `EVAL_SEEDS` shapes. Probabilities are mine; intervals are 80%.

Evidence used: run7 (H100 PCIe) passed intake through implement (one method repair after an independent equivalence test failed; review passed), then evaluate was VOID because the harness's `run_evaluation.sh`, written before the seal, iterated every key of `evaluation_inputs` and crashed. Runs 6 and 7 both passed intake to propose cleanly (MPS factor 1.94 to 2.00 on H100, margins SD/sqrt(8) cited from reproduce, 5 of 5 approvals for data-parallel over inputs). No run has yet measured equivalence or performance, so evaluate is new territory beyond its first adapter call.

Equivalence reasoning: with DeterministicForces, the same seed on the same GPU and software should reproduce a replica exactly whether it runs alone or concurrently under MPS. Run7's first method attempt failed an independent equivalence test, so a method can perturb trajectories; after any perturbation, paired differences over 25,000 steps are comparable to the between-seed spread and exceed SD/sqrt(8). Evaluation repeats timing 7 to 15 times at three compute caps, at about 45 to 55 s of fixed work per eight-replica ensemble.

## Box
- H100 SXM5 0.45, H100 PCIe 0.3, A100 SXM4 0.2, A100 PCIe or A10 0.05.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.92 |
| reproduce | PASS 0.88 given intake PASS. Sequential ensemble 40 to 55 s on H100, 55 to 65 s on A100 |
| profile | PASS 0.92 given reproduce PASS; MPS verified 0.92; H100 headroom median 1.95 [1.7, 2.3], A100 median 1.78 [1.6, 2.0] |
| seal | PASS 0.8 given profile PASS; margins SD/sqrt(n) cited from reproduce 0.65 |
| propose | approved 0.8 given seal PASS; data-parallel over inputs 0.7 |
| implement | reached 0.5 overall. Given reached: PASS 0.55; a method repair used 0.45; `run_evaluation.sh` iterates only `EVAL_INPUTS.ids` 0.85 |
| evaluate | reached 0.27 overall. Given reached: every adapter run writes valid measurements 0.7; an evaluation script hits its 2400 s budget 0.25; validity_pass 0.85; equivalence_pass 0.6 (paired differences exactly zero 0.5); performance_pass 0.55; speedup_published 1.4 to 2.2 on H100, 1.3 to 1.8 on A100; evaluate PASS 0.4 |
| takeaways | PASS 0.95; run_box_usd 1.5 to 6 if the run stops before evaluate, 6 to 25 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.5; reaches evaluate 0.27; end-to-end PASS 0.11.

## What would change my mind
- Evaluate VOID again on an adapter shape error: stating the shapes in the prompt is not enough; the adapter needs a smoke run before evaluate (the queued candidate).
- Evaluate equivalence FAIL with nonzero but small paired differences (below 1 kJ/mol): determinism holds only approximately; the method, not the protocol, fails.
- Evaluate equivalence FAIL with differences near the between-seed spread: the method changed the trajectories (initial state, platform properties or precision), which the independent tests should have caught.
- Evaluate performance FAIL with median ratio above 1.3 but the one-sided bound below the minimum worthwhile gain: repetitions are too few for a stable bound.
- An evaluation script timeout at fixed work: the seal's repetitions by caps do not fit the default evaluate budget.
