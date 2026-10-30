# Sealed operator predictions: blind-openmm run5

Written and committed before launch. Run5 uses the exact one-line hint from runs 1 to 4 (`run5/args.json`, no brief file; intake searches). It runs blind to the operator; OpenMM is public, so the content is read after the run. Code at a9d643d (unchanged since run4). Chain `~/.cache/blind01/retry36.sh`: retry32.sh plus up to 3 launch attempts, and no pipeline without a box. Probabilities are mine; intervals are 80%.

Why rerun: run4's box never came up, so nothing past intake was measured. The licence criterion is unchanged, pending the owner. On a distribution basis, the verdict has so far been permitted 3 times and unknown once.

## Box
- H100 SXM5 0.35, H100 PCIe 0.3, A100 SXM4 0.25, A10 0.05, A100 PCIe 0.05. All three launch attempts fail: 0.05.

## Intake
| Quantity | Prediction |
|---|---|
| Study | `benchmark.py` (OpenMM's own or the NVIDIA MPS study) 0.6, the energy-drift study 0.3, other 0.1 |
| `licence_basis` | distribution 0.65, explicit 0.15, none 0.15, other 0.05 |
| `licence` "permitted", given distribution | 0.65 |
| intake PASS | 0.55 |

## Later stages, given intake PASS
- On `benchmark.py` (OpenMM 8.x; 0.7 of intake passes): reproduce PASS 0.7, profile PASS 0.9, seal PASS 0.8, propose approved 0.6, implement PASS 0.55, evaluate PASS 0.6.
- On the drift study (0.25 of intake passes): reproduce stops at setup 0.75 (an OpenMM 7.0.1 source build).
- `speedup_published` given evaluate PASS: 1.1 to 1.8. The method is most likely concurrent processes or MPS-style overlap of independent simulations.

## Run level
- Stopping stage: intake 0.45, reproduce 0.23, profile 0.03, seal 0.06, propose 0.09, implement 0.06, evaluate 0.03; end-to-end PASS 0.05.
- The chain cuts the pipeline: 0.05.
- Pipeline exit 0, box torn down, push verified by the chain: 0.85.
- run_box_usd: 0.05 to 0.5 at an intake stop; 0.5 to 5 at a reproduce to propose stop; 3 to 15 beyond.

## What would change my mind
- Intake PASS on `benchmark.py` but reproduce fails on setup: installing a released OpenMM 8.x on the stock image is harder than the positive control suggested.
- An end-to-end PASS: the blind same-hint path reaches the positive control's result without operator content, which is the goal of this experiment.
