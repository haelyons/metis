# blind-01 m5 run4: metadata-only diagnosis

Read through `~/.cache/blind01/blind_read.py` only, under the read guard hook, plus the chain status lines. No content review follows.

## Facts
- Raid `shadow2`, record committed and pushed by the chain (PUSH_OK 4556d9c3). Box gpu_1x_a100_sxm4, asia-south-1, USD 1.99/h, up on the first attempt at 20:03:27Z, torn down; pipeline exit 0; run_box_usd 0.12. Code 4a40052 (U43 and the Opus understudy).
- **Intake FAIL** in 220 s (Codex, 542,735 tokens in), blocker `data_unavailable`: `found` true, `anchors_count` 1, `anchored` true, `data` "partial", `licence` "unknown", `licence_basis` "unreachable", `size` "unknown". Every later stage SKIPPED; no box receipts.
- No Opus handover: intake ran on Codex. U43 was not exercised.

## What the metadata says
- Four intake draws on this brief:

| Run | data | licence_basis | anchors_count | intake |
|---|---|---|---|---|
| run1 | available | (no field before U40) | 3 | FAIL (licence unknown, before U41) |
| run2 | partial | unreachable | 3 | FAIL (`data_unavailable`) |
| run3 | available | none | 3 | PASS |
| run4 | partial | unreachable | 1 | FAIL (`data_unavailable`) |

- "partial" has come with "unreachable" both times it occurred (run2, run4): in those draws the intake agent failed to reach a source. Run4 also anchored 1 item where every other draw anchored 3; run2 was "partial" with 3, so the drop is not tied to "partial" alone. `found` and `anchored` stayed true throughout.
- Intake runs locally, so the box region (run2 us-west-3, run4 asia-south-1) does not bear on reachability.
- The intake agent runs locally with network access (Codex `workspace-write`, `network_access=true`, set in `idea/codex_cli.js`), so a sandbox block is unlikely to be the cause.

## Hypotheses (not resolvable from metadata)
- H1 0.45: a source host for the data is intermittently unreachable or rate-limited from this machine. A draw that reaches it reports "available".
- H2 0.35: the agent's choice of source or path decides the outcome. Some draws go to a mirror or page that works; others go to one that does not.
- H3 0.2: the data is genuinely partly gated. "Available" draws over-read what they found, which reproduce would then expose.

## Scoring of sealed predictions (predictions/run4.md, 0226644)
| Prediction | Outcome | Hit |
|---|---|---|
| Box: A100 SXM4 0.3 | A100 SXM4, first attempt | no (0.3 on the outcome) |
| intake PASS 0.6 | FAIL | no |
| `data` "available" 0.6, "partial" 0.35 | partial | no |
| Opus handover 0.15 | none | yes, correctly below 0.5 |
| stopping stage intake 0.4 | intake | yes (0.4 on the outcome) |
| exit 0, teardown, push 0.88 | yes | yes |
| run_box_usd 0.05 to 0.5 at an intake stop | 0.12 | yes |
| reproduce, U43 and later stages | not reached | — |

Run3's "what would change my mind" item fired: "partial" again with basis "unreachable". On this brief, fetch failures look systematic rather than chance, at about half the draws.

## Next
- The owner can read the run2 and run4 intake records to see which source was unreachable. That settles H1 against H3 directly.
- Without that reading, each redraw costs about USD 0.12 to an intake stop and passes intake about half the time. U43 still needs a run that reaches reproduce.
