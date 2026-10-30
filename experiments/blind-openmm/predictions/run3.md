# Sealed operator predictions: blind-openmm run3

Written and committed before launch. Run3 uses the exact one-line hint from run1 and run2 (`run3/args.json`, no brief file; intake searches). It runs blind to the operator; OpenMM is public, so the content is read after the run. Code at 7502edf. Single-GPU dev box, chain `~/.cache/blind01/retry32.sh` (status lines only). Probabilities are mine; intervals are 80%.

What changed since run2 (73f03dd):
- U39 (7502edf): the intake prompt names every key the completeness check reads as a JSON key, defines `pin`, and states that other key names do not count. The check is unchanged.

What run2's content review told me (I have read it, so these are informed priors, not blind ones):
- The hint selected the OpenMM 7 paper's energy-drift study twice out of two: 30 VerletIntegrator simulations of 500,000 steps on DHFR, in single, mixed and double precision.
- Evidence access works: licence permitted, data available, three published references (no tolerances), so `anchored` false.
- The baseline is OpenMM 7.0.1 built from source (a CUDA 7.5-era toolchain). `stock_environment` was null.
- The agent set stage budgets up to 604,800 s. The chain bounds the pipeline at 21,000 s and the box at 6 h.

## Box
The chain lists types in preference order; run2 got H100 PCIe.
- H100 PCIe 0.4, A100 SXM4 0.25, H100 SXM5 0.2, A10 0.1, A100 PCIe 0.05.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.6, in 120 to 600 s. Benchmark chosen: the energy-drift study 0.7, OpenMM's `benchmark.py` 0.2, other 0.1. Given FAIL: `env_irreproducible` blocker (the agent judges a CUDA 7.5-era build infeasible on a stock image) 0.35; blockers `["none"]` (files still incomplete) 0.35; `found` false 0.2; `licence` or `data_unavailable` 0.1 |
| reproduce | PASS 0.25 given intake PASS (0.2 on the drift study, 0.5 on `benchmark.py`). If it fails: setup (the OpenMM 7.0.1 build) 0.6, the chain cuts it before a verdict 0.25, harness or anchors 0.15 |
| profile | PASS 0.7 given reproduce PASS; a long workload makes a chain cut here the main risk |
| seal | PASS 0.6 given profile PASS; `protocol_cost` is the likely reason if not (a 30 ns workload repeated is unaffordable) |
| propose, implement, evaluate | reached 0.05, 0.03, 0.02 overall |
| takeaways | written 0.88 (not written when the chain cuts the pipeline) |

## Run level
- Stopping stage: intake 0.4, reproduce 0.45, profile 0.05, seal 0.04, propose 0.02, implement 0.02, evaluate 0.01; end-to-end PASS 0.01.
- The chain cuts the pipeline (exit 124): 0.12.
- Pipeline exit 0, box torn down, push verified by the chain: 0.8.
- run_box_usd: 0.05 to 0.5 at an intake stop; 0.5 to 5 at a reproduce stop without a cut; 7 to 21 if the chain cuts the run.

## What would change my mind
- Intake FAIL with blockers `["none"]` again: another prompt/check mismatch survives U39, and the intake missing-keys fact (a closed list of contract key names) becomes the next unit.
- Intake PASS on `benchmark.py`: the hint does not pin the study; run-to-run selection varies, which matters for the blind protocol.
- Reproduce PASS on an OpenMM 7.0.1 source build on a modern image: the toolchain risk I assumed is smaller than I think.
- A chain cut: intake accepts budgets a run cannot spend. An intake budget ceiling becomes the next unit, and the ceiling value is the owner's decision.
