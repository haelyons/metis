# Sealed operator predictions: blind-01 m5 run7

Written and committed before launch, blind as for run6 (`predictions/run6.md`). Same brief (`intake_mirror/BRIEF_run5.md`, the unverified mirror addendum), args from run1's template (tag b01m5r7), chain retry38, reads only through `~/.cache/blind01/blind_read.py` under the read guard hook.

## Variables changed since run6
- U45: the probe reports every enabled apt source (`apt_enabled_sources`), and setup may install a missing tool or system library with apt from any of them, after an `apt-cache policy` candidate check, never adding sources, keys or repositories, recording each install with `dpkg-query -W` (U45 37a9fa06, merged de05e892). Run6's setup failed three times in about 10 s on a missing runtime library packaged in Ubuntu universe; the old rule allowed apt only from CUDA/NVIDIA source lines, so neither repair could install it (diagnoses 09c97fdd, b950b99e, eb0d2c70).
- Nothing else: same brief, same scientific checks, U43's two repairs and U44's chunked uploads unchanged.

Why: run6 exercised U43 and stopped on a rule, not on the science. This draw measures whether setup gets past the library, fetches the mirror copy and checks its hashes, and whether anchors run.

## Box
- A100 SXM4 0.3, A10 0.25, H100 PCIe 0.2, H100 SXM5 0.15, A100 PCIe 0.05; all three launch attempts fail 0.05.

## Intake
| Quantity | Prediction |
|---|---|
| intake PASS | 0.8 (runs 5 and 6 passed on this brief) |

## Reproduce, given intake PASS
| Quantity | Prediction |
|---|---|
| harness upload succeeds | 0.95 |
| universe is among the box's enabled sources (the install route exists) | 0.85 |
| the first setup attempt runs longer than 60 s (gets past the early failure) | 0.6 |
| setup needs at least one repair | 0.6 |
| at least one setup attempt times out (fetch plus hash checks within 1,200 s) | 0.3 |
| setup passes within its repairs | 0.5 |
| anchors run at least once | 0.45 |
| reproduce PASS | 0.25 |
| FAIL `install` | 0.3 |
| FAIL `anchor` | 0.2 |
| FAIL `timeout` | 0.15 |
| FAIL `infra` | 0.05 |

## Run level
- Stopping stage: intake 0.2, reproduce 0.6, profile 0.03, seal 0.05, propose 0.06, implement 0.04, evaluate 0.02.
- Pipeline exit 0, box torn down, push verified by the chain: 0.88.
- run_box_usd: 0.05 to 0.5 at an intake stop; 0.5 to 15 at a reproduce stop; 5 to 40 beyond.

## What would change my mind
- Setup again failing in about 10 s on every attempt: the library is not installable from the enabled sources either, or the repair still does not install it. Diagnose before another draw; consider the box image (owner).
- Setup timing out: the setup budget cannot hold the fetch plus per-file checks; a budget question (EXECUTION.json stage budgets), not a reason to drop the checks.
- Reproduce FAIL `anchor`: the copy runs but does not reproduce the published values, or the harness measures the wrong thing. Anchors check only what they measure; a FAIL does not prove the copy differs, and a PASS would not prove it matches.
