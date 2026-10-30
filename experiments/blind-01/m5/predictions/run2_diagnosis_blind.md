# blind-01 m5 run2: metadata-only diagnosis

Read through `~/.cache/blind01/blind_read.py` only (signature numbers, booleans and pipeline enums; OPERATOR_TAKEAWAY.md; receipts; box record; raid name; launcher log tail), plus the chain status lines. The read guard hook was active for the whole read. No content review will follow: blind-01 content is never read.

## Facts
- Raid `rappel`, run committed e40bc56 by the chain, push verified. Box gpu_1x_h100_pcie, us-west-3, USD 3.29/h, up on the first attempt at 16:09:11Z and torn down; pipeline exit 0; no large files left out; run_box_usd 0.14.
- Intake FAIL in 154 s, Codex, 455,813 tokens in and 5,268 out. `blockers` ["data_unavailable"].
- Intake facts: `found` true, `anchors_count` 3, `anchored` true, `data` "partial", `licence` "unknown", `licence_basis` "unreachable", `stock_environment` null, `size` "unknown".
- Every later stage SKIPPED; no receipts; takeaways PASS.

## What the metadata says
- **U41 took effect.** `licence` "unknown" no longer appears among the blockers; the only failed condition is `data`.
- **The intake's judgement moved between draws on the same brief.** Run1: `data` "available", `licence` "unknown". Run2: `data` "partial", `licence` "unknown" with basis "unreachable" (the licence evidence for some item could not be fetched). `found` true, 3 anchors and `anchored` true in both, which suggests the same study.
- **"unreachable" and "partial" together point to fetch failures in this draw** rather than a change in the subject. That cannot be confirmed from metadata.
- **The pipeline handled it as specified.** A partial-data intake blocks ("missing executable inputs block"); the signature named the blocker; the takeaway listed it. No pipeline defect is visible.

## Hypotheses (not resolvable from metadata; no content review)
- H1 0.5: the intake agent could not reach some sources this time (licence page and a data host), so it recorded "partial" and "unreachable" honestly. A redraw would likely see them.
- H2 0.3: part of the required data is genuinely gated (behind a login, request form or embargo). Run1's "available" was the lenient draw. Only the owner can check this against the brief.
- H3 0.2: other (a different study chosen, or a stricter reading of the same evidence).

## Scoring of sealed predictions (predictions/run2.md, 3625dc1)
| Prediction | Outcome | Hit |
|---|---|---|
| Box: H100 PCIe 0.15 | H100 PCIe, first attempt | no (0.15 on the outcome) |
| intake PASS 0.75 | FAIL | no |
| `licence` "unknown" 0.55 | unknown | yes |
| `anchored` true given PASS 0.7 | true (intake failed) | n/a |
| very long budgets (W1) 0.25 | no receipts | n/a |
| stopping stage intake 0.25 | intake | yes (0.25 on the outcome) |
| exit 0, teardown, push 0.85 | yes | yes |
| run_box_usd 0.05 to 0.5 at an intake stop | 0.14 | yes |
| end-to-end PASS 0.03 | no | yes (against 0.03) |

"What would change my mind": none fired. Intake did not fail on licence alone, and the authority line was not applicable (no PASS).

## Next
- Intake reliability on this brief is itself a measurement: two draws, two different fact sets. A third draw estimates whether "partial" is stable (H2) or a fetch failure (H1). It costs about USD 0.15 and three minutes at an intake stop, and a lenient draw cannot pass science it should not: reproduce fetches and runs the data for real, so missing data fails there.
- Owner: if the brief's data needs an access step (login, request form), only the owner can see or supply it.
