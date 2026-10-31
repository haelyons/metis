# Sealed operator predictions: blind-01 m5 run5

Written and committed before launch, blind as for run4 (`predictions/run4.md`). Args from run1's template (tag b01m5r5), chain retry38 (12 h pipeline timeout, 13 h box), reads only through `~/.cache/blind01/blind_read.py` under the read guard hook. Launched only if the mirror reader's status says the materials are usable, the hashes are recorded, the re-fetch matched and the addendum exists.

## Variables changed since run4
- Brief: `intake_mirror/BRIEF_run5.md`, the original BRIEF.md bytes plus a materials section by the Codex mirror reader (owner decision 2026-10-31, option 2). It names the unverified mirror's URLs with sizes and SHA-256, and states that the copy's identity with the original is unverified. The operator has not read it; the post check reports only enums, the prefix match, the heading, the `unverified_mirror` label and a count of SHA-256 values.
- Mirror reader status (87d632d5): materials_usable true, alternative `unverified_mirror`, hashes_recorded true, refetch match, owner_action none. The addendum holds 3603 distinct SHA-256 values, so the brief is far longer than run4's; a stage that reads it whole may spend more context or time (P 0.15 that a stage times out or truncates on it).
- Pipeline code: unchanged since run4 (4a40052, U43). Every scientific check is unchanged.

Why: run2 and run4 stopped at intake with `data` "partial" (source moved). This draw measures whether a recorded, box-fetchable copy gets intake past `data` and reproduce into U43's two repairs.

## Box
- A100 SXM4 0.3, A10 0.25, H100 PCIe 0.2, H100 SXM5 0.15, A100 PCIe 0.05; all three launch attempts fail 0.05.

## Intake
| Quantity | Prediction |
|---|---|
| intake PASS | 0.7 |
| `data` "available" | 0.7; "partial" 0.25 (intake still weighs the unverified copy as incomplete); other 0.05 |

## Reproduce, given intake PASS
| Quantity | Prediction |
|---|---|
| reproduce PASS | 0.45 |
| setup needs at least one repair | 0.6 |
| the second setup or anchors repair is used (U43 exercised) | 0.35 |
| given the second repair is used, reproduce PASS | 0.4 |
| FAIL `install` after two repairs | 0.2 |
| FAIL `anchor` (higher than run4: the copy may differ from the original) | 0.2 |
| FAIL `timeout` | 0.08 |
| FAIL `infra` or a fetch failure on the box (mirror unreachable or hash mismatch) | 0.07 |

## Understudy
- At least one stage recorded with `model_family` claude (an Opus handover): 0.15.

## Later stages, conditional on reaching them
As in run3.md: profile 0.85, seal 0.75, propose approved 0.45, implement 0.45, evaluate 0.5 (scorer timeout 0.3).

## Run level
- Stopping stage: intake 0.3, reproduce 0.4, profile 0.02, seal 0.06, propose 0.1, implement 0.06, evaluate 0.04; end-to-end PASS 0.02.
- Pipeline exit 0, box torn down, push verified by the chain: 0.88.
- run_box_usd: 0.05 to 0.5 at an intake stop; 0.5 to 10 at a reproduce stop; 5 to 40 beyond.

## What would change my mind
- Intake FAIL with `data` "partial" again: intake does not accept a recorded unverified copy as the data. That is a pipeline question for the owner (how intake treats owner-approved provenance), not a reason to redraw.
- Reproduce FAIL `anchor`: either the copy differs from the original or the harness is wrong. Anchors measure only their own properties, so a FAIL does not prove the copy differs, and a PASS would not prove it matches.
- Reproduce reaching a second repair: U43 exercised; note its wall seconds against run3's single repair.
