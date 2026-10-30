# blind-openmm run5: metadata-only diagnosis (sealed before reading content)

Read so far: chain status lines, `devbox_up.log` (the box launcher's own output), `operator/signatures.jsonl` (numeric, boolean and enum fields), `control/receipts` (rc, timed_out, wall_s, budget_s, overrun, file times), `control/box.json` (type, price, region, start), the raid ledger, and box GPU utilisation and load average from `nvidia-smi` at 15:27Z (numbers only). No OPERATOR_TAKEAWAY.md exists: the takeaways stage never ran.

## Disclosure: one blindness slip during the run
While backtesting budgets at about 13:30Z, I read `stage_budgets_s` from run5's `agent/intake/EXECUTION.json` during the live run. As I recall it, every key was 604800 (7 days). No other agent/ content was read. The receipts below carry the same number for anchors, so the slip adds nothing the metadata does not, except the setup value (see the open question below).

## Facts
- Run committed 4bea66b by the chain, push verified. Raid: skeletonkey.
- Box: gpu_1x_a10, us-east-1, USD 1.29/h, up at 10:01:24Z on the first launch attempt. Torn down by the chain at about 15:56Z: 5.91 h, about USD 7.62.
- Intake PASS in 237 s, 758,721 tokens in, Codex. Facts: `found` true, `anchors_count` 3, `anchored` false, `data` "available", `licence` "permitted", `licence_basis` "distribution", `stock_environment` null, `size` "unknown".
- Reproduce receipts: upload 8 s, probe 7 s, upload 8 s, setup 29 s (each rc 0, budget 1200 s), then anchors: started 10:13:42Z, budget 604800 s, still running at the chain cut, wall 20510 s, rc null.
- At 15:27Z the box GPU was at 100% utilisation, 614 MiB used, load average 1.0: the workload was computing, not idle.
- The chain's `timeout 21000` ended the pipeline at 15:55Z (pipeline exit 124). No reproduce signature was written; every later stage has no record.

## What the metadata says
- **One anchors invocation ran over 5.7 h on an A10 and had not finished.** In the 15 public positive-openmm runs, the anchors run took 17 to 178 s, and the sealed per-invocation baseline (run15, run16) was about 117 to 119 s, so one anchors run is about one baseline invocation. If that holds here, one invocation is at least 20,510 s. The smallest protocol the seal allows is 5 repetitions per arm, at least 10 scored invocations, so evaluate alone would need at least 57 h. No ceiling under discussion (6 h soft, 12 h hard) could fit this workload at this scale on this box.
- **Intake's 604800 s budgets let the first workload run unbounded.** The fixed 1200 s defaults would have timed it out after 20 min with an error class of `timeout` and one bounded repair. Neither outcome yields a verdict, but the default would have spent 20 min, not 5.7 h.
- **The chain cut leaves no stage record.** A timeout outside the pipeline kills it before it can write a reproduce signature or a takeaway. The pipeline's own limits must fire before the chain's.
- **Open question for the content review:** the setup receipt shows budget 1200 s, while I recall the setup key in EXECUTION.json as 604800 s. Either my recollection is wrong or setup resolves from another source.

## Hypotheses: why the anchors run took over 5.7 h (sums to 1)
- H1 0.55: the study's representative scale is a long simulation (published as hours on faster hardware), run in full as one fixed scale; slower on an A10.
- H2 0.25: the harness runs the anchors workload several times or at several sizes within one invocation (e.g. all three references in sequence), each long.
- H3 0.15: a script fault that keeps the GPU busy without progress (e.g. a loop that never meets its stop condition).
- H4 0.05: other.

## Scoring of sealed predictions (predictions/run5.md, 8c3cfce)
| Prediction | Outcome | Hit |
|---|---|---|
| Box: A10 0.05 | A10, first attempt | no (0.05 on the outcome) |
| `licence_basis` distribution 0.65 | distribution | yes |
| `licence` "permitted" given distribution 0.65 | permitted | yes |
| intake PASS 0.55 | PASS | yes |
| stopping stage reproduce 0.23 | reproduce, by chain cut | yes on stage (0.23); the mechanism was the cut |
| chain cuts the pipeline 0.05 | cut at 21000 s | no (0.05 on the outcome) |
| exit 0, teardown, push 0.85 | exit 124; teardown and push yes | no |
| run_box_usd 0.5 to 5 at a reproduce to propose stop | about 7.62 (box record; no signature carries it) | no |

"What would change my mind": neither item fired; reproduce did not fail on setup (setup took 29 s, rc 0).

## Next
1. U42b, revised by this run: the first workload run in reproduce is bounded by the lower-bound fit rule, not by half the time left. If one invocation exceeds the ceiling divided by the smallest protocol's invocation count, the full protocol cannot fit, and reproduce stops with `compute_cap` and the measured lower bound. Half the time left would have spent about 5.9 h here, as the chain did, to reach the same conclusion.
2. The chain timeout must exceed the pipeline ceiling, so the pipeline's own stop rules fire and write records.
3. Content review (OpenMM is public): which study, why 604800 s, what the anchors run was doing, and the setup budget question.
