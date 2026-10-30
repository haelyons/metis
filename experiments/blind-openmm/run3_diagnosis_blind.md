# blind-openmm run3: metadata-only diagnosis (sealed before reading content)

Read so far: chain status lines, `operator/signatures.jsonl` (numeric, boolean and enum fields), the Blockers section of `operator/OPERATOR_TAKEAWAY.md`, the `control/` listing, the box type and the raid ledger. Nothing under agent/ or pipeline.log.

## Facts
- Run committed 2ae5235 by the chain, push verified. Box gpu_1x_h100_sxm5, up and torn down; pipeline exit 0. Raid: whisper.
- Intake FAIL in 181 s, 380,336 tokens in (run2: 177 s, 581,100).
- Intake facts: `found` true, `anchors_count` 1, `anchored` false (one reference), `data` "available", `licence` "unknown", `stock_environment` null, `size` "unknown".
- Signature `blockers` ["licence"] (U38). Every later stage SKIPPED; takeaways PASS; run_box_usd 0.22.

## What the metadata says
- The licence fact alone fails the gate. Whether the files were also incomplete is not visible: U38 names fact conditions only, and the signature carries no file condition.
- Same hint, same code path for licence evidence: run2 recorded "permitted", run3 "unknown". The licence judgement is not stable run to run on a public benchmark.
- `anchors_count` moved from 3 to 1, and tokens in fell by a third. Either the agent chose a different study, or it read the same study differently.

## Hypotheses (sum to 1)
- H1 0.45: a different study or source was chosen (anchors 1 against 3), for example OpenMM's `benchmark.py` or a third-party DHFR benchmark. Its code or data carries no licence statement the agent could cite.
- H2 0.3: the same energy-drift study, but the agent judged the paper's supplementary scripts unlicensed: an article licence that does not plainly cover code. Run2's agent judged the same evidence permitted.
- H3 0.15: the licence evidence was unreachable (a fetch failed for the licence page or repository) while the data was reached.
- H4 0.1: other.

## Bearing on blind-01
Blind-01 run1 stopped on the same fact, `licence` "unknown". If H2 or H3 holds here, an "unknown" licence comes from the intake agent's reading, not from the benchmark. Blind-01's H1 (licence genuinely absent or restrictive, 0.5) should then fall. The content review settles which.

## Scoring of sealed predictions (predictions/run3.md, 884274a)
| Prediction | Outcome | Hit |
|---|---|---|
| H100 PCIe 0.4, A100 SXM4 0.25, H100 SXM5 0.2, A10 0.1, A100 PCIe 0.05 | H100 SXM5 | no (0.2 on the outcome) |
| intake PASS 0.6 | FAIL | no |
| given FAIL: `env_irreproducible` 0.35; `["none"]` 0.35; `found` false 0.2; `licence` or `data_unavailable` 0.1 | `licence` | no (0.1 on the outcome) |
| stopping stage: intake 0.4, reproduce 0.45 (the mode) | intake | no (0.4 on the outcome) |
| chain cut 0.12 | no cut | yes |
| exit 0, teardown, chain push 0.8 | yes | yes |
| run_box_usd 0.05 to 0.5 at an intake stop | 0.22 | yes |
| takeaways written 0.88 | yes | yes |

My priors leaned on run2's content: I treated licence as settled because run2 found it permitted. That was the error. One run's judgement of a fact is a single draw, not a property of the benchmark.

None of the "what would change my mind" items fired as written. Run2's item did: "Intake FAIL with only a `licence` blocker: OpenMM's licence (MIT/LGPL) is public, so this would mean licence evidence is unreachable to the agent. That would also bear on blind-01 run1's H2."
