# Sealed operator predictions: positive-openmm run6

Written and committed before launch. Run6 starts from the same brief as runs 1 to 5 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from earlier runs: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`. Pipeline code is at 2566965 (U27): the anchors repair may now rewrite `run_anchors.sh`, `run_command.sh` or both, and every harness prompt states that `run_command.sh` contains only the exact measured baseline command and complete environment. Probabilities are mine; intervals are 80%.

Evidence used: run5 (H100 SXM5) stopped at reproduce because its harness put an `openmm.__version__ == '8.2.0'` assertion in `run_command.sh` and the repair could not edit that file. Run4 (A100 SXM4) passed through propose: MPS verified (factor 1.37 at two copies, 1.78 at four), seal PASS with margins SD/sqrt(8) from reproduce's per-seed energies, propose approved 5 of 5 for data-parallel over inputs (expected speedup 1.475).

Equivalence reasoning is unchanged from run5: with DeterministicForces, the same seed on the same GPU and software should reproduce each replica's trajectory exactly, so paired differences are zero; any perturbation decorrelates trajectories over 25,000 steps and paired differences become comparable to the between-seed spread, which exceeds margins of the form SD/sqrt(n).

## Box
- H100 SXM5 0.45 (run5 got it, and it is first in the type order), A100 SXM4 0.35, H100 PCIe 0.1, A100 PCIe 0.05, A10 0.05.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.9 |
| reproduce | PASS 0.85 given intake PASS. `run_command.sh` holds no preflight assertion 0.7; if an anchors repair runs, it edits `run_command.sh` 0.5. Sequential ensemble 55 to 65 s on A100, 35 to 55 s on H100 |
| profile | PASS 0.9 given reproduce PASS; MPS verified 0.9; A100 headroom median 1.78 [1.6, 2.0], H100 median 2.0 [1.4, 2.8] |
| seal | PASS 0.7 given profile PASS. Given PASS: margins cite reproduce outputs 0.85; margins of the form SD/sqrt(n) 0.5, SD or a multiple of it 0.35 |
| propose | approved 0.65 given seal PASS; method data-parallel over inputs 0.5, ensembles 0.4, batching 0.1 |
| implement | reached 0.3 overall. Given reached: PASS 0.45; the method starts its own MPS daemon 0.7; it runs replicas as concurrent processes rather than threads in one process 0.75 |
| evaluate | reached 0.14 overall. Given reached: validity_pass 0.85; equivalence_pass 0.7 (paired differences exactly zero 0.65); performance_pass 0.65; speedup_published 1.4 to 1.9 on A100, 1.4 to 2.5 on H100 |
| takeaways | PASS 0.95; run_box_usd 0.5 to 4 if the run stops at or before propose, 3 to 10 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.3; reaches evaluate 0.14; end-to-end PASS 0.06.

## What would change my mind
- Reproduce FAIL again on a script the anchors repair could edit: the one-repair budget, not its scope, is the limit.
- Reproduce PASS with a preflight block still in `run_command.sh`: stating the rule in the prompt is not enough, and the contract needs a check.
- Implement FAIL with tests showing different per-seed energies: the method changed the simulation, or determinism does not hold across concurrent contexts.
- Evaluate equivalence FAIL with nonzero but small paired differences (below 1 kJ/mol): determinism holds only approximately; the failure is in the method, not the protocol.
- Evaluate performance FAIL with median ratio above 1.3 but minimum below the minimum worthwhile gain: five repetitions are too few for a stable one-sided bound.
