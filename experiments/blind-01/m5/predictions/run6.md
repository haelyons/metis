# Sealed operator predictions: blind-01 m5 run6

Written and committed before launch, blind as for run5 (`predictions/run5.md`). Same brief as run5 (`intake_mirror/BRIEF_run5.md`, the unverified mirror addendum), args from run1's template (tag b01m5r6), chain retry38, reads only through `~/.cache/blind01/blind_read.py` under the read guard hook.

## Variables changed since run5
- U44 (fd0c5e6e, merged 16cb7b76): harness uploads use chunked base64 batches below 32,768 characters, one `upload` receipt per batch. Run5's harness exceeded the 131,072-byte single-argument limit when sent as one command; spawn failed with E2BIG and reproduce stopped with `infra` before setup (diagnosis 3a2f7d16: harness upload, over 128 KiB, embedded hashes, hash checks requested by the brief).
- Nothing else: same brief, same scientific checks, U43's two repairs unchanged.

Why: run5 got past intake for the first time with the mirror addendum and stopped on a transport limit. This draw measures whether setup and anchors run on the mirror copy, and whether U43's second repair is used.

## Box
- A100 SXM4 0.3, A10 0.25, H100 PCIe 0.2, H100 SXM5 0.15, A100 PCIe 0.05; all three launch attempts fail 0.05.

## Intake
| Quantity | Prediction |
|---|---|
| intake PASS | 0.75 (run5 passed on the same brief) |
| `data` "available" | 0.75 |

## Reproduce, given intake PASS
| Quantity | Prediction |
|---|---|
| harness upload succeeds (several `upload` receipts before the first `setup`) | 0.9 |
| reproduce PASS | 0.35 |
| setup needs at least one repair | 0.65 |
| at least one setup attempt times out (fetching the copy and checking thousands of hashes inside the setup budget) | 0.3 |
| the second setup or anchors repair is used (U43 exercised) | 0.4 |
| given the second repair is used, reproduce PASS | 0.35 |
| FAIL `install` after two repairs | 0.2 |
| FAIL `anchor` | 0.2 |
| FAIL `timeout` | 0.12 |
| FAIL `infra` | 0.08 |

## Understudy
- At least one stage recorded with `model_family` claude (an Opus handover): 0.15.

## Later stages, conditional on reaching them
As in run3.md: profile 0.85, seal 0.75, propose approved 0.45, implement 0.45, evaluate 0.5 (scorer timeout 0.3).

## Run level
- Stopping stage: intake 0.25, reproduce 0.5, profile 0.02, seal 0.06, propose 0.08, implement 0.05, evaluate 0.03; end-to-end PASS 0.01.
- Pipeline exit 0, box torn down, push verified by the chain: 0.88.
- run_box_usd: 0.05 to 0.5 at an intake stop; 0.5 to 10 at a reproduce stop; 5 to 40 beyond.

## What would change my mind
- Reproduce FAIL `anchor` with setup passing: the mirror copy runs but does not reproduce the published values, or the harness measures the wrong thing. Anchors measure only their own properties, so this does not prove the copy differs from the original, and a PASS would not prove it matches.
- Setup timing out on every attempt: the setup budget cannot hold the fetch plus per-file checks. A budget question for the owner (EXECUTION.json stage budgets), not a reason to drop the checks.
- Upload still failing `infra`: U44 did not cover the path the run used; diagnose before another draw.
