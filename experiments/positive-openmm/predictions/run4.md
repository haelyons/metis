# Sealed operator predictions: positive-openmm run4

Written and committed before launch. Same brief as runs 1 to 3 (`experiments/positive-openmm/BRIEF.md`, e91489b), fresh harness, single-GPU dev box, `m5/wf_config.json`. Code under test at 8e47e0f: U22 to U24 as in run3, plus U25 (the seal agent reads the baseline's reproduce outputs; a variability-derived margin cites the measured file and statistic) and U26 (the stochastic seal check reads executable fields only). Probabilities are mine; intervals are 80%.

Evidence used: run3 (predictions/run3_scored.md). On an A100 SXM4: intake, reproduce and profile PASSed; MPS was verified, with factor 1.39 at two copies and 1.79 at four; the seal agent marked outputs stochastic and, unable to see measured variability, left margins null. Reproduce's baseline output holds per-seed energies for seeds 1000 to 1007; their standard deviation is 109 kJ/mol (mean potential) and 293 kJ/mol (final potential). With DeterministicForces, the same seed on the same GPU and software should give identical energies whether runs are sequential or concurrent, so paired differences should be near zero.

## Box
- A100 0.5 (two of the last three runs), H100 SXM5 0.2, H100 PCIe 0.2, A10 0.1.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.9; anchored false 0.85 |
| reproduce | PASS 0.85 given intake PASS; sequential ensemble 55 to 65 s on A100, 45 to 70 s on H100 |
| harness respects the MPS rule | 0.9 |
| profile | PASS 0.9 given reproduce PASS |
| probe MPS state | mps true (verified) 0.85; mps_failed true 0.1 |
| headroom given verified MPS | A100 median 1.8 [1.5, 2.1]; H100 median 1.9 [1.3, 2.6]; A10 median 1.15 [0.9, 1.6] |
| seal | PASS 0.6 given profile PASS. outputs_stochastic true 0.9. Given PASS: margins cite a reproduce output file and a per-seed statistic 0.75; margins between 10 and 300 kJ/mol 0.7; prediction_count 3 (data-parallel, batching, ensembles) 0.85. Failure modes: margins still declared unavailable 0.2; another validation code after repair 0.2 |
| propose | given seal PASS with feasible methods: outcome approved 0.6, rejected 0.25, conditions_unmet 0.15. Method: ensembles 0.45, data-parallel over inputs 0.45, batching 0.1 |
| implement | reached 0.25 overall. Given reached: PASS 0.45; the method starts its own MPS daemon 0.7 |
| evaluate | reached 0.11 overall. Given reached: validity_pass 0.85, equivalence_pass 0.75 (paired differences near zero), performance_pass 0.65; speedup_published 1.4 to 2.1 on A100, 1.3 to 2.4 on H100 |
| takeaways | PASS 0.95; run_box_usd 1 to 3 if the run stops between reproduce and propose, 3 to 8 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.25; reaches evaluate 0.11; end-to-end PASS 0.05.
- Measured negative finding 0.03.

## What would change my mind
- Seal FAIL with margins still null although the reproduce outputs hold per-seed energies: the seal agent does not find or trust them, and the baseline's per-seed outcomes need a fixed location rather than a harness-chosen one.
- Seal PASS with margins far above the per-seed spread (more than 300 kJ/mol): the variability-derived margin is too loose to mean anything, and the contract needs a rule linking margin size to the measured statistic.
- Equivalence FAIL with deterministic forces: concurrent runs change per-seed energies, so either the method altered the simulation or determinism does not hold under MPS.
