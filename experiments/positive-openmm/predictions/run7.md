# Sealed operator predictions: positive-openmm run7

Written and committed before launch. Run7 starts from the same brief as runs 1 to 6 (`experiments/positive-openmm/BRIEF.md`, e91489b), with workload seeds 1000 to 1007 fixed by that brief. Nothing is reused from earlier runs: a fresh harness, a fresh seal and a fresh proposal. Single-GPU dev box, `m5/wf_config.json`. Pipeline code is at 3aa0622 (U28): isolated roles run with Codex's own sandbox off inside the pipeline's bubblewrap namespace, which is now the only sandbox. The operator chain's safety limits are raised from 3.9 h to 5.8 h (pipeline) and from 4 h to 6 h (box), so a run reaching evaluate is not cut by the chain. Probabilities are mine; intervals are 80%.

Evidence used: run6 (H100 SXM5) passed intake to propose cleanly (MPS factor 2.00, seal margins SD/sqrt(8) cited from reproduce, propose 5 of 5 for data-parallel over inputs, expected 1.575), then stopped in implement because the isolated Codex test author could not run any command. Run4 (A100 SXM4) also passed through propose. Implement, evaluate and the isolated roles have never run for real, so I expect implement to surface at least one new gap.

## Box
- H100 SXM5 0.55, A100 SXM4 0.3, H100 PCIe 0.08, A100 PCIe 0.04, A10 0.03.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.9 |
| reproduce | PASS 0.85 given intake PASS. Sequential ensemble 35 to 55 s on H100, 55 to 65 s on A100 |
| profile | PASS 0.9 given reproduce PASS; MPS verified 0.9; H100 headroom median 2.0 [1.6, 2.4], A100 median 1.78 [1.6, 2.0] |
| seal | PASS 0.75 given profile PASS; margins of the form SD/sqrt(n) cited from reproduce 0.6 |
| propose | approved 0.75 given seal PASS; data-parallel over inputs 0.6, ensembles 0.35 |
| implement | reached 0.4 overall. Given reached: the isolated test author runs commands and writes `run_tests.sh` 0.85; the method author writes all three method files 0.8; patch applies 0.75; PASS 0.35. Given PASS: the method starts its own MPS daemon 0.6; replicas run as concurrent processes rather than threads 0.75; a method repair was used 0.4 |
| evaluate | reached 0.14 overall. Given reached: an evaluation script hits its 2400 s budget 0.3; validity_pass 0.8; equivalence_pass 0.65 (paired differences exactly zero 0.6); performance_pass 0.6; speedup_published 1.4 to 2.5 on H100, 1.3 to 1.9 on A100 |
| takeaways | PASS 0.95; run_box_usd 1.5 to 5 if the run stops in or before implement, 5 to 20 if it reaches evaluate |

## Run level
- Pipeline exit 0, box torn down, push verified by the chain: 0.9.
- Reaches implement 0.4; reaches evaluate 0.14; end-to-end PASS 0.06.

## What would change my mind
- Implement FAIL with the isolated test author still unable to run commands: U28's real-host behaviour differs from its fake-codex tests.
- Implement FAIL because the method author cannot reach the box from inside isolation (SSH key or wrapper not visible): box access under isolation needs its own check.
- Implement FAIL with tests showing different per-seed energies: the method changed the simulation, or determinism does not hold across concurrent contexts.
- Evaluate timeouts at fixed work: the seal's 32 seeds by 7 repetitions by 3 caps does not fit the default evaluate budget, and the seal must be told the measured cost of one ensemble.
- Evaluate performance FAIL with median ratio above 1.3 but the one-sided bound below 1.05: the protocol, not the method, limits the claim.
