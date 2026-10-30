# blind-openmm run2: metadata-only diagnosis (sealed before reading content)

Read so far: chain status lines, `operator/signatures.jsonl`, `operator/OPERATOR_TAKEAWAY.md`, the `control/receipts` listing (empty: no box command ran) and the raid ledger. Nothing under agent/ or pipeline.log.

## Facts
- Run committed 73a67e2 by the chain, push verified. Box gpu_1x_h100_pcie (USD 3.29/h), up and torn down; pipeline exit 0.
- Intake FAIL in 177 s, one Codex call, 581,100 tokens in.
- Intake facts: `found` true, `anchors_count` 3, `anchored` false (three references), `data` "available", `licence` "permitted", `stock_environment` null, `size` "unknown". Signature `blockers` ["none"], `error_class` none, `exit_code` -1.
- Every later stage SKIPPED; run_box_usd 0.16.

## What the metadata rules out
The intake gate is: complete files, `found` true, `data` "available", `licence` "permitted", `stock_environment` not false. All four fact conditions hold, so U38 correctly names no blocker. The FAIL therefore comes from the files:
- **Not the reply.** It was present: the facts come only from a reply.
- **Not anchors.json.** `anchored` is false rather than null, which happens only when anchors.json validates and its length equals `anchors_count`.

What remains is one of the following:
- a missing or unparseable benchmark, data, baseline or EXECUTION JSON file, or one that is not an object;
- baseline.json lacking `repo`, `build_commands`, `run_commands`, `published_configuration`, or `commit`/`pin`;
- EXECUTION.json lacking `representative_scale`, `inputs`, `outputs` or `timing_scope`.

Run1 failed on whether a benchmark existed; run2 found one and failed on describing it. The changes since run1 (the network proxy off, references accepted) moved the failure one step on.

## Hypotheses (sum to 1)
- H1 0.35: baseline.json has no `commit` or `pin`. A paper's supporting scripts, or a benchmark script cited by URL, have no immutable pin the agent could verify, and the prompt forbids inventing one.
- H2 0.3: EXECUTION.json leaves a required field empty, most likely `representative_scale` or `timing_scope`. The hint's "fixed set of independent simulations" has no published scale the agent could cite.
- H3 0.2: baseline.json lacks `build_commands`, `run_commands` or `published_configuration`, for example because the published scripts have no documented command line.
- H4 0.15: a file is missing or is not valid JSON (an exception path).

## Scoring of sealed predictions (predictions/run2.md, bf0c151)
| Prediction | Outcome | Hit |
|---|---|---|
| A100 SXM4 0.5, A10 0.18, H100 SXM5 0.15, H100 PCIe 0.12, A100 PCIe 0.05 | H100 PCIe | no (0.12 on the outcome) |
| intake PASS 0.45 | FAIL | yes (against 0.45) |
| given FAIL: `found` false 0.55; `licence` blocker 0.4; `data_unavailable` blocker 0.4 | `found` true; no; no | no; yes; yes |
| stopping stage intake 0.55 (the mode) | intake | yes |
| exit 0, teardown, chain push 0.9 | yes | yes |
| run_box_usd 0.05 to 0.5 at an intake stop | 0.16 | yes |
| end-to-end PASS 0.04 | no | yes |

None of the "what would change my mind" items fired as written. The run fell in the gap between them: the evidence was reachable and the benchmark was found, but the files were incomplete.

## Reporting gap
The signature cannot separate "incomplete files" from a PASS-shaped intake, or from one with a missing reply. U38 deliberately named only the three fact conditions. A blind operator needs the failed file condition too. That needs a fixed vocabulary that carries no content: which required file or key was missing, never its value.
