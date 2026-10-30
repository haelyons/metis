# Sealed operator predictions: blind-openmm run4

Written and committed before launch. Run4 uses the exact one-line hint from runs 1 to 3 (`run4/args.json`, no brief file; intake searches). It runs blind to the operator; OpenMM is public, so the content is read after the run. Code at a9d643d. Single-GPU dev box, chain `~/.cache/blind01/retry32.sh` (status lines only). Probabilities are mine; intervals are 80%.

What changed since run3 (7502edf):
- U40 (a9d643d): intake reports an optional `licence_basis` enum fact (unreachable, none, owner, distribution, explicit) for the least-covered item among the benchmark code and its required inputs. It changes no gate.

Purpose: test U40 end to end before it is used on blind-01, and take a fourth draw of the intake licence judgement under the same hint. The licence criterion is unchanged, pending the owner's decision, so a licence stop is likely and is not a pipeline defect.

Lessons from run3's scoring: one run's judgement of a fact is a single draw. Study selection varied (drift study twice, then the NVIDIA MPS `benchmark.py` study), and the licence judgement varied on the same evidence.

## Box
- H100 SXM5 0.4, H100 PCIe 0.3, A100 SXM4 0.2, A10 0.05, A100 PCIe 0.05.

## Intake
| Quantity | Prediction |
|---|---|
| Study | `benchmark.py` (NVIDIA MPS study or OpenMM's own) 0.45, the energy-drift study 0.35, other 0.2 |
| `licence_basis` reported (not null) | 0.9 |
| `licence_basis`, given `benchmark.py` | distribution 0.6, explicit 0.3, other 0.1 |
| `licence_basis`, given the drift study | none 0.4, distribution 0.3, explicit 0.2, other 0.1 |
| `licence` "permitted", given the basis | explicit 0.9, distribution 0.5, none 0.1 |
| Files complete (no blocker-free FAIL) | 0.85 |
| intake PASS | 0.4, in 120 to 600 s |
| Given FAIL: blockers | `licence` alone 0.7, `["none"]` 0.15, `env_irreproducible` 0.1, other 0.05 |

## Later stages
- Given intake PASS on `benchmark.py`: reproduce PASS 0.7. A public OpenMM 8.x workload resembles the positive control, which passed end to end (run16).
- Given intake PASS on the drift study: reproduce stops at setup 0.6 (an OpenMM 7.0.1 source build).

## Run level
- Stopping stage: intake 0.6, reproduce 0.2, profile 0.03, seal 0.04, propose 0.04, implement 0.04, evaluate 0.02; end-to-end PASS 0.03.
- The chain cuts the pipeline: 0.07.
- Pipeline exit 0, box torn down, push verified by the chain: 0.85.
- run_box_usd: 0.05 to 0.5 at an intake stop; 0.5 to 5 at a reproduce to propose stop; 3 to 15 beyond.

## What would change my mind
- `licence_basis` null: the prompt does not elicit the fact; U40 needs a required fact, not an optional one.
- `licence_basis` "explicit" with `licence` "unknown", or "none" with "permitted": the agent's two answers contradict each other, and the basis fact is not a reliable reading of the judgement.
- `licence_basis` "unreachable": evidence access has regressed since run2.
