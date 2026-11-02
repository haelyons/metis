# blind-02 run1 predictions: first full chain on the owner's refined seed (sealed before launch)

## Operator exposure (recorded before sealing)

The operator is **not blind** to this experiment's brief. The operator created the brief's template with a file tool; when the owner filled it (2026-11-02), the session's changed-file notice put the whole seed into the operator's context. The guard blocks only tool calls and could not stop it. The owner chose to continue with this operator (2026-11-02). These predictions are therefore informed by the seed's text; they are not blind predictions. The operator still reads run metadata only (`blind_read.py`, reader enums) and does not quote or summarise the seed here. Templates the owner fills are made by shell copy from now on.

## Design

- Brief: `b01_materials/BRIEF_run1.md`: the seed's exact bytes plus a labelled materials section by an authorized Codex reader (owner 2026-11-02: the seed refers to cases and materials by pointing at blind-01, which the pipeline's intake agent may not read; the 2026-10-31 unverified-mirror approval extends to blind-02). Reader status (6e7c480c, enums only): cases identified `yes`, seed matches records `yes`, prepared inputs pinned `yes`, references pinned `yes`, software pins recorded `partly` (blind-01's records do not cover everything the seed names; intake must establish the rest), weakest provenance `unverified_mirror`, hashes recorded (96 values in the section), every location reachable, owner action `none`; the section follows the seed's exact bytes and names no `experiments/` path.
- Chain: full m5 pipeline (intake, reproduce, profile, seal, propose, implement, evaluate, takeaways), fresh harness (nothing reused from blind-01's harness), `retry51.sh`: `gpu_1x_h100_pcie` first, 12 h run ceiling, box `--max-hours 14`.
- Pipeline: main tree, unchanged since run11 (merge 90e379cd: U49 host-only profile gate, U50b/U52 unit probe, which this run does not use).
- First live use of: the host-only profile gate (U49, tested on run9's saved files only) if the reproduced baseline is CPU-only; seal, propose, implement and evaluate on a blind brief (no blind run has passed profile).
- Contract fit: the seed asks for comparisons that include a better-outcome question. m5 evaluates a method's equivalence to the baseline and its speed; it has no stage that scores a quality change. The seed asks for any such limit to be reported; how the pipeline reports it is visible to the operator only through stage outcomes.

## Decision rule (fixed before launch; never changed after a result)

| Result | Next |
|---|---|
| Any stage FAIL or VOID | Diagnose with an authorized reader; a pipeline change only as a new unit with its own tests, one gate per unit; no criterion change. |
| End-to-end PASS | Report the takeaways' enums and the stage facts to the owner; scientific reading is the owner's. |
| Ceiling timeout or infrastructure failure | Diagnose; relaunch only after the cause is understood. |

## Predictions

Probabilities are the operator's, written before launch.

| # | Prediction | P |
|---|---|---|
| 1 | Intake PASS | 0.80 |
| 2 | Intake `licence_basis` is `owner` or `distribution` (given intake ran) | 0.60 |
| 3 | Setup passes within its repairs | 0.70 |
| 4 | Reproduce PASS | 0.55 |
| 5 | Profile PASS (given reproduce PASS) | 0.45 |
| 6 | Profile `host_only` true (given profile ran) | 0.45 |
| 7 | Propose outcome `approved` (given propose ran) | 0.45 |
| 8 | Implement PASS (given implement ran) | 0.45 |
| 9 | Evaluate PASS (given evaluate ran) | 0.35 |
| 10 | End-to-end PASS | 0.06 |
| 11 | Run wall under 6 h | 0.65 |
| 12 | Run box cost under USD 25 | 0.75 |
| 13 | No ceiling timeout and no infrastructure failure | 0.85 |

All predictions are read from signatures, receipts and box metadata.
