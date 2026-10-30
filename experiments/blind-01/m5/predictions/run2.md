# Sealed operator predictions: blind-01 m5 run2

Written and committed before launch. The operator has not read the brief (`experiments/blind-01/m5/BRIEF.md`, owner-written, untracked, unchanged since 2026-10-25). These predictions use only pipeline history and metadata, never the subject. During and after the run the operator reads only chain status lines, `devbox_up.log`, `operator/signatures.jsonl` (numbers, booleans, enums), `operator/OPERATOR_TAKEAWAY.md`, `control/receipts` (rc, timed_out, wall_s, budget_s, overrun, fetched), `control/box.json` (type, price, region, start) and the raid ledger. No content review follows.

Setup: same brief and args as run1 (tag b01m5r2). Code at 2c2e846: run1's c1998af plus U38 (intake blockers), U39 (exact intake keys), U40 (`licence_basis`) and U41 ("unknown" licence no longer blocks; the takeaway names the owner's standing instruction as execution authority). Chain `~/.cache/blind01/retry38.sh`: retry36 with a 12 h pipeline timeout and a 13 h box lifetime, in place of 21000 s and 6 h. Pipeline stage timeouts are unchanged (defaults 1200/2400 s unless intake sets `stage_budgets_s`). Probabilities are mine; intervals are 80%.

Evidence used: run1 intake found a benchmark (`found` true, 3 anchors, `anchored` true, data available) and failed only on `licence` "unknown". Positive-openmm passed end to end once (run16) after units U20 to U37. In the blind-openmm series, one run in five reached reproduce with a box, and its first workload ran past 5.7 h.

## Box
- A10 0.4, A100 SXM4 0.25, H100 SXM5 0.15, H100 PCIe 0.15, A100 PCIe 0.05. All three launch attempts fail: 0.05.

## Intake
| Quantity | Prediction |
|---|---|
| intake PASS | 0.75 |
| `licence` "unknown" | 0.55; "permitted" 0.4; "restricted" 0.05 |
| the authority line in the takeaway, given intake PASS | 0.55 (it appears exactly when `licence` is not "permitted") |
| `anchored` true, given PASS | 0.7 |
| any receipt with `budget_s` of at least 86400 (intake set very long budgets) | 0.25 |

## Later stages, conditional on reaching them
| Stage | Prediction |
|---|---|
| reproduce PASS | 0.55 |
| profile PASS | 0.85 |
| seal PASS | 0.75; first attempt fails `protocol_cost` 0.2 |
| propose | approved 0.45; measured no-feasible-method negative finding 0.15; FAIL or VOID 0.4; a Claude refusal halts the run 0.15 |
| implement PASS | 0.45 |
| evaluate PASS | 0.5; a scorer timeout (rc 124) 0.3 |

## Lessons to watch (each fires or not; a firing is the evidence for a unit)
- W1, very long budgets: any receipt `budget_s` at least 86400: 0.25.
- W2, long first workload: a reproduce box command over 3600 s: 0.15.
- W3, evaluate scorer timeout at the 2400 s default, given evaluate starts: 0.3.
- W4, adapter workload above the sealed one: not observable from the blind allowlist unless a signature number carries it; unscored.
- W5, the chain cuts the pipeline (exit 124 at 43200 s): 0.04.

## Run level
- Stopping stage: intake 0.25, reproduce 0.3, profile 0.04, seal 0.1, propose 0.15, implement 0.08, evaluate 0.05; end-to-end PASS 0.03.
- Pipeline exit 0, box torn down, push verified by the chain: 0.85.
- run_box_usd: 0.05 to 0.5 at an intake stop; 0.5 to 8 at a reproduce to propose stop; 5 to 40 beyond.

## What would change my mind
- Intake FAIL with `licence` "unknown" as its only failed condition: U41 did not take effect.
- Intake PASS without the authority line while `licence` is not "permitted": the takeaway rule is wrong.
- A Claude refusal at propose or review: the Claude routes cannot serve this brief, and routing needs an owner decision.
