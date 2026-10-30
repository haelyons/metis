# Sealed operator predictions: blind-01 m5 run1

Written and committed before launch. The operator has not read the brief (`experiments/blind-01/m5/BRIEF.md`, owner-written, untracked). These predictions use only pipeline history and metadata, never the subject. During and after the run the operator reads only `operator/signatures.jsonl`, `operator/OPERATOR_TAKEAWAY.md`, `control/receipts` (rc and timings) and the raid ledger.

Setup: single-GPU dev box, `m5/wf_config.json`, code at c1998af (pipeline as at a6a3ec4, U37). Chain `~/.cache/blind01/retry32.sh`: the same as retry7.sh, but it prints status lines only and leaves files over 95 MB uncommitted. Probabilities are mine.

Evidence used:
- The public positive control (positive-openmm) passed end to end at a6a3ec4 in run16, after units U20 to U37.
- Intake passed in all 16 positive-control runs, from an owner brief that embeds its scripts.
- The one earlier blind run (blind-openmm run1, a one-line hint) failed at intake: no qualifying anchor, and the network allowlist blocked evidence behind a DOI.
- Claude routes in this config: skeptic-4, skeptic-5 and review (claude/sonnet), with `on_refusal: halt`. An earlier Claude operator session (m4, Opus) hit a safeguard stop on blind-01.

## Box
- A100 SXM4 0.5, A10 0.18, H100 SXM5 0.15, H100 PCIe 0.12, A100 PCIe 0.05.

## Stages
| Stage | Prediction |
|---|---|
| intake | PASS 0.6. Given FAIL: `found` false 0.6; at least one named blocker (data, licence, inputs, permissions) 0.5 |
| reproduce | PASS 0.6 given intake PASS (a fresh harness on an unseen workload; the positive control needed U22 to U27 here) |
| profile | PASS 0.85 given reproduce PASS |
| seal | PASS 0.7 given profile PASS; first attempt fails `protocol_cost` 0.2 |
| propose | given seal PASS: approved 0.45, measured no-feasible-method negative finding (PASS) 0.15, FAIL or VOID 0.4; a Claude judge refusal halts the run 0.15 |
| implement | reached 0.1 overall; PASS 0.45 given reached; a Claude review refusal 0.15 given reached |
| evaluate | reached 0.045 overall; PASS 0.55 given reached |
| takeaways | PASS 0.95 |

## Run level
- Stopping stage: intake 0.4, reproduce 0.24, profile 0.05, seal 0.09, propose 0.09 (FAIL, VOID or halt), implement 0.05, evaluate 0.02. Passes as a negative finding at propose 0.03; end-to-end PASS 0.02.
- Pipeline exit 0, box torn down, push verified by the chain: 0.88. At least one file over 95 MB left uncommitted: 0.1.
- run_box_usd: 0.1 to 0.5 if it stops at intake, 0.5 to 2.5 if it stops at reproduce to propose, 2 to 8 beyond.

## What would change my mind
- Intake FAIL with no named blocker and `error_class: none`: the blind operator cannot tell the cause. The signature needs the gate that failed, as in blind-openmm run1.
- A refusal halt on a Claude route: the judge routes need an understudy that does not halt on blind content.
- Reproduce FAIL in setup or install: the box image, not the subject, is the bottleneck for unseen workloads.
- Propose FAIL on an empty menu: the profile measured nothing the method menu can use. This repeats run11's shape on the blind side.
