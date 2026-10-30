# blind-01 m5 run3: metadata-only diagnosis

Read through `~/.cache/blind01/blind_read.py` only, under the read guard hook, plus the chain status lines. No content review follows.

## Facts
- Raid `lockpick2`, run committed a8fc089 by the chain (mid-run snapshot d068c12), push verified. Box gpu_1x_a100_sxm4, asia-south-1, USD 1.99/h, up on the first attempt at 16:24:10Z, torn down; pipeline exit 0; run_box_usd 0.65.
- **Intake PASS** in 192 s (Codex, 388,724 tokens in): `found` true, `anchors_count` 3, `anchored` true, `data` "available", `licence` "unknown", `licence_basis` "none". The first blind-01 m5 intake PASS.
- **The takeaway carries the authority line** ("Execution authority: owner's standing instruction (2026-10-30), not licence evidence."). U41 works end to end on the blind brief.
- **Reproduce FAIL** in 975 s, `exit_kind` infra, `error_class` install, `stock_verified` false, Codex (418,843 tokens in). Receipts: upload 12 s, probe 13 s, upload 13 s, setup rc 1 in 92 s, the one bounded repair (upload 69 s), setup rc 1 in 578 s. No anchors run; every later stage SKIPPED.

## What the metadata says
- The harness could not install the baseline on the stock image in two attempts. The repaired setup ran six times longer before failing, so the repair changed what it did (more got installed or downloaded) without reaching a working environment.
- The pipeline classified this correctly: an install failure is infrastructure, not a benchmark finding, and one bounded repair was spent as the contract allows.
- Intake on this brief has now given three different fact sets in three draws: run1 data available, licence unknown; run2 data partial, basis unreachable; run3 data available, basis none. `found`, 3 anchors and `anchored` stayed constant, which suggests the same study each time.

## Hypotheses (not resolvable from metadata)
- H1 0.45: the published environment needs versions the stock image cannot provide (an old CUDA, compiler or Python), so no harness would install it as pinned.
- H2 0.3: a harness script fault the single repair did not fix.
- H3 0.25: downloads failed from this box (asia-south-1) or a source host, consistent with run2's "unreachable".

## Scoring of sealed predictions (predictions/run3.md, 2c8ca21)
| Prediction | Outcome | Hit |
|---|---|---|
| Box: A100 SXM4 0.2 | A100 SXM4, first attempt | no (0.2 on the outcome) |
| intake PASS 0.5 | PASS | yes (at 0.5) |
| `data` "available" 0.5 | available | yes |
| `licence_basis` "unreachable" 0.35 | none | no, correctly below 0.5 |
| authority line, given PASS 0.85 | present | yes |
| reproduce PASS 0.45 | FAIL (install) | no, correctly below 0.5 |
| stopping stage reproduce 0.25 | reproduce | yes (0.25 on the outcome) |
| exit 0, teardown, push 0.88 | yes | yes |
| run_box_usd 0.5 to 8 at a reproduce to propose stop | 0.65 | yes |

"What would change my mind": neither item fired (`data` was "available").

## Next
- The owner can now read the brief (f46f066) and every run folder; whether H1 holds is a content question. Without it, a redraw tests H2 and H3 cheaply (about USD 0.65 to a reproduce stop).
- The next run will carry the Opus understudy for authoring roles (owner, 2026-10-30), a change of variable to note when comparing it with run3.
