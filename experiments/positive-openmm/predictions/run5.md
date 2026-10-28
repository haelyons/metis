# Sealed operator predictions: positive-openmm run5

Written and committed before launch. Run5 starts from the same brief as runs 1 to 4 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from run4: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`. Pipeline code is unchanged since 8e47e0f (U22 to U26); later commits add only run records, the raid ledger and an ignore rule. Probabilities are mine; intervals are 80%.

Evidence used: run4 (A100 SXM4), which stopped in implement only because the operator machine's disk filled. Through propose it gave: MPS verified, factor 1.37 at two copies and 1.78 at four; seal PASS with stochastic margins SD/sqrt(8) from reproduce's per-seed energies (38.6 kJ/mol mean potential, 103.5 kJ/mol final potential); propose approved 5 of 5 for data-parallel over inputs, expected speedup 1.475 (interval 1.30 to 1.65). Run3 gave the same factor on the same box type.

Equivalence reasoning: with DeterministicForces, the same seed on the same GPU and software should reproduce a replica's trajectory exactly, whether replicas run one after another or concurrently under MPS. If trajectories are identical, paired differences are zero and pass any positive margin. If anything perturbs a trajectory (different platform properties, precision, or initial state), 25,000 steps of chaotic dynamics decorrelate it, and paired differences become comparable to the between-seed spread (SD 109 and 293 kJ/mol), which exceeds the run4-style margins.

## Box
- A100 0.6 (the last three runs), H100 SXM5 0.15, H100 PCIe 0.15, A10 0.1.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.9 |
| reproduce | PASS 0.85 given intake PASS; sequential ensemble 55 to 65 s on A100 |
| profile | PASS 0.9 given reproduce PASS; MPS verified 0.9; A100 headroom median 1.78 [1.6, 2.0], H100 median 1.9 [1.3, 2.6] |
| seal | PASS 0.7 given profile PASS. Given PASS: margins cite reproduce outputs 0.85; margins of the form SD/sqrt(n) 0.5, SD or a multiple of it 0.35 |
| propose | approved 0.65 given seal PASS; method data-parallel over inputs 0.5, ensembles 0.4, batching 0.1 |
| implement | reached 0.3 overall. Given reached: PASS 0.45; the method starts its own MPS daemon 0.7; it runs replicas as concurrent processes rather than threads in one process 0.75 |
| evaluate | reached 0.14 overall. Given reached: validity_pass 0.85; equivalence_pass 0.7 (paired differences exactly zero 0.65); performance_pass 0.65 (the lower bound is the smallest of five paired ratios and must exceed minimum_worthwhile_gain); speedup_published 1.4 to 1.9 on A100 |
| takeaways | PASS 0.95; run_box_usd 1 to 3 if the run stops at or before propose, 3 to 8 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.3; reaches evaluate 0.14; end-to-end PASS 0.06.

## What would change my mind
- Implement FAIL with tests showing different per-seed energies: the method changed the simulation, or determinism does not hold across concurrent contexts.
- Evaluate equivalence FAIL with nonzero but small paired differences (below 1 kJ/mol): determinism holds only approximately, and margins of SD/sqrt(n) are still scientifically reasonable; the failure would be in the method, not the protocol.
- Evaluate performance FAIL with median ratio above 1.3 but minimum below the minimum worthwhile gain: five repetitions are too few for a stable one-sided bound, and the protocol, not the method, limits the claim.
