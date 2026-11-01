# Sealed operator predictions: blind-01 m5 run9

Written and committed before launch, blind as for run8 (`predictions/run8.md`). Same brief (`intake_mirror/BRIEF_run5.md`, the unverified mirror addendum), args from run1's template (tag b01m5r9), chain retry38 (since U47: pipeline timeout 46,800 s, box `--max-hours 14`), reads only through `~/.cache/blind01/blind_read.py` under the read guard hook.

## Variables changed since run8
- U47 (121bc806, merge f7334bdd): for setup, anchors and profile, intake's `stage_budgets_s` are recorded estimates only; each box command's budget is the args override or else the time left before a 12 h run ceiling (`run_ceiling_s` 43,200 s from pipeline start), resolved at each command's start. Run8's intake set a 1,200 s anchors budget; the published-scale workload was still running at the budget in two of three attempts, completed only partly and wrote no measurements (diagnoses 4b46236a, fc561641; the runtime could not be estimated from partial progress).
- The run chain's pipeline timeout rose from 43,200 s to 46,800 s and the box limit from 13 h to 14 h, so a command ending near the ceiling still gets its records written.
- Codex is at its usage limit at launch (probe 2026-11-01 about 01:38 GMT: "usage limit", fails in 2 s; reset stated 04:30). Routing is unchanged (Codex primary, `--family codex`): a usage-limit failure hands over at once, so intake, harness, harness/anchors repairs, seal, propose, tests and implement run on the claude/opus understudy until the reset, and the unrouted Codex calls (skeptic-1 to 3) on OpenCode. Codex returns for any call after the reset. UNDERSTUDY.md records which family answered each call.
- Nothing else: same brief, same scientific checks, U43 to U46 unchanged.

Why: run8 stopped on intake's guessed budget, not on the science. This draw measures how long the published-scale anchor workload takes and whether the copy reproduces the published values.

## Box
- A100 SXM4 0.3, A10 0.2, H100 PCIe 0.2, H100 SXM5 0.25, A100 PCIe 0.05; all three launch attempts fail 0.05.

## Intake
| Quantity | Prediction |
|---|---|
| intake PASS | 0.8 (runs 5 to 8 passed on this brief with Codex; this intake runs on the Opus understudy) |
| intake answered by the Opus understudy | 0.9 |

## Reproduce, given intake PASS
| Quantity | Prediction |
|---|---|
| setup passes within its four repairs | 0.7 |
| anchors run at least once | 0.65 |
| first anchors attempt that starts the workload runs over 1,200 s | 0.75 |
| some anchors attempt runs over 3 h | 0.3 |
| anchors produce measured values for every anchor item | 0.4 |
| reproduce PASS | 0.25 |
| FAIL `anchor` | 0.3 |
| FAIL `install` | 0.15 |
| FAIL `timeout` (ceiling reached) | 0.2 |
| FAIL `infra` | 0.1 |

## Run level
- Stopping stage: intake 0.15, reproduce 0.65, profile 0.08, seal 0.04, propose 0.04, implement 0.03, evaluate 0.01.
- The run reaches the 12 h ceiling: 0.15.
- Pipeline exit 0, box torn down, push verified by the chain: 0.88.
- run_box_usd: 0.05 to 0.5 at an intake stop; 1 to 60 at a reproduce or profile stop.

## What would change my mind
- Anchors run to the ceiling: the published-scale workload does not fit 12 h on one GPU; the brief's scale, not a budget, is the question (owner).
- Anchors finish but FAIL `anchor`: the copy runs but does not reproduce the published values, or the harness measures the wrong thing. Anchors check only what they measure; a FAIL does not prove the copy differs, and a PASS would not prove it matches the original (provenance stays unverified).
- Profile times out after anchors pass: the profiler adds more than the time left; profile's budget then needs its own evidence.
