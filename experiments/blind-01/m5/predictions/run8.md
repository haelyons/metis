# Sealed operator predictions: blind-01 m5 run8

Written and committed before launch, blind as for run7 (`predictions/run7.md`). Same brief (`intake_mirror/BRIEF_run5.md`, the unverified mirror addendum), args from run1's template (tag b01m5r8), chain retry38, reads only through `~/.cache/blind01/blind_read.py` under the read guard hook.

## Variables changed since run7
- U46: setup permits up to four repairs (was two); anchors keep two. Each repair prompt states `repair attempt <n> of <limit>` (U46 73c1f572, merged 58edbf9b). Run7's setup failed three times (56 s, 376 s, 35 s) on successive script errors after U45 had fixed run6's missing library; each repair saw and targeted its error, none regressed, the box reached the mirror and every hash check passed, a static check would have caught none, and reruns reuse the fetched and verified materials (diagnoses 5a3898f3, c39dfa61).
- Nothing else: same brief, same scientific checks, U43 to U45 unchanged.

Why: run7 stopped on the repair budget, not on the science. This draw measures whether more repairs converge on a working setup and whether anchors run.

## Box
- A100 SXM4 0.3, A10 0.25, H100 PCIe 0.2, H100 SXM5 0.15, A100 PCIe 0.05; all three launch attempts fail 0.05.

## Intake
| Quantity | Prediction |
|---|---|
| intake PASS | 0.85 (runs 5, 6 and 7 passed on this brief) |

## Reproduce, given intake PASS
| Quantity | Prediction |
|---|---|
| harness upload succeeds | 0.95 |
| setup needs at least one repair | 0.75 |
| setup needs three or more repairs | 0.4 |
| at least one setup attempt times out | 0.15 |
| setup passes within its four repairs | 0.6 |
| anchors run at least once | 0.55 |
| anchors need at least one repair, given they run | 0.5 |
| reproduce PASS | 0.25 |
| FAIL `install` | 0.3 |
| FAIL `anchor` | 0.25 |
| FAIL `timeout` | 0.15 |
| FAIL `infra` | 0.05 |

## Run level
- Stopping stage: intake 0.15, reproduce 0.65, profile 0.04, seal 0.05, propose 0.06, implement 0.03, evaluate 0.02.
- Pipeline exit 0, box torn down, push verified by the chain: 0.88.
- run_box_usd: 0.05 to 0.5 at an intake stop; 0.5 to 15 at a reproduce stop; 5 to 40 beyond.

## What would change my mind
- Setup failing all five attempts on successive different errors: repairs fix one error at a time without converging; diagnose whether repairs need the earlier attempts' errors or a different repair input, rather than raising the limit again.
- The same error recurring across repairs: repairs oscillate; diagnose before another draw.
- Reproduce FAIL `anchor`: the copy runs but does not reproduce the published values, or the harness measures the wrong thing. Anchors check only what they measure; a FAIL does not prove the copy differs, and a PASS would not prove it matches the original (provenance stays unverified).
