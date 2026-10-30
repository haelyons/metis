# Sealed operator predictions: blind-01 m5 run4

Written and committed before launch, blind as for run3 (`predictions/run3.md`): same brief, args from run1's template (tag b01m5r4), chain retry38 (12 h pipeline timeout, 13 h box), reads only through `~/.cache/blind01/blind_read.py` under the read guard hook.

## Variables changed since run3 (code 2c2e846 -> 4a40052)
- U43: setup and anchors each permit up to two harness repairs (was one). Run3 spent its one setup repair on a build-dependency failure; the repair worked, and setup then failed on a different import error (owner's reading of run3).
- Opus understudy (af27221): claude/opus is the first fallback for the Codex authoring roles (intake, harness, repairs, seal, propose, tests, implement). Fallback only; Codex stays primary.

Why: run3 is the first blind-01 intake PASS and stopped at reproduce on an install failure. This draw measures whether a second repair carries the harness through setup, and records whether the understudy is ever used.

## Box
- A100 SXM4 0.3, A10 0.25, H100 PCIe 0.2, H100 SXM5 0.15, A100 PCIe 0.05; all three launch attempts fail 0.05.

## Intake
| Quantity | Prediction |
|---|---|
| intake PASS | 0.6 (two of three draws had `data` "available") |
| `data` "available" | 0.6; "partial" 0.35; other 0.05 |
| the authority line, given PASS | 0.85 |

## Reproduce, given intake PASS
| Quantity | Prediction |
|---|---|
| reproduce PASS | 0.5 |
| setup needs at least one repair | 0.6 |
| the second setup or anchors repair is used | 0.35 |
| given the second repair is used, reproduce PASS | 0.45 |
| FAIL `install` after two repairs | 0.2 |
| FAIL `anchor` | 0.15 |
| FAIL `timeout` | 0.1 |
| FAIL `infra` | 0.05 |

## Understudy
- At least one stage recorded with `model_family` claude (an Opus handover): 0.15.
- Given a handover, the stage it happens in still reaches a status (no halt): 0.8.

## Later stages, conditional on reaching them
As in run3.md: profile 0.85, seal 0.75, propose approved 0.45, implement 0.45, evaluate 0.5 (scorer timeout 0.3).

## Run level
- Stopping stage: intake 0.4, reproduce 0.3, profile 0.02, seal 0.06, propose 0.1, implement 0.06, evaluate 0.04; end-to-end PASS 0.02.
- Pipeline exit 0, box torn down, push verified by the chain: 0.88.
- run_box_usd: 0.05 to 0.5 at an intake stop; 0.5 to 10 at a reproduce stop (two repairs lengthen it); 5 to 40 beyond.

## What would change my mind
- FAIL `install` after both repairs, with the second repaired setup running about as long as the first: the environment likely needs something the stock image cannot give (run3's H1). A content question for the owner, not more repairs.
- Reproduce PASS after the second repair: U43 fixed the failure it was built for. Note the cost (setup receipts' wall seconds) against run3.
- Any Opus handover: evaluate it after the run (which stage, whether the method and test authors ended up in the same family).
