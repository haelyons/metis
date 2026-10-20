# reshape-test · measure · 20261020-0145

Kind: measure. The first phase (`gpu_bench`) of a PASS card, run as a latent_skeptic run, so that the card's own
prediction is resolved by a measurement and the result lands beside the card it came from.

## Source card

- Run: `../20261019-2345-tree` (arm O, open root), pick R1 · physical · "Large-sample multi-catchment calibration (CAMELS)".
- Record: `../20261019-2345-tree/out/result.json` sha256 `3bda9fd89ac81cd09fa50ab298fa851160d0a9a2894489276adfa4dbd42c3cdb`;
  rendered card `../20261019-2345-tree/out/RESULT.md` sha256 `93ed866bc76faa28e8b95af8b32b137f4102bd29b4217dbad3bda329f507ee04`.
- Producer reply (the PLAN): `../20261019-2345-tree/out/agents/0008-R1_physical_top_producer/reply.txt`.
- The card's prediction under test: `expected: if_not`, by its own decision rule: "if_lever iff GPU wall-clock for
  671 catchments < 1 hour AND the GPU beats the vectorized CPU baseline by >= 20x; otherwise if_not."
- The card's two load-bearing guesses, both `measured_by: gpu_bench`: `batched_forward_ms = 2` and `cpu_671_hours = 3`.
- The card's own gate at this phase: `main_run_hours <= 6`, else "Stop and replan".

## Pipeline

- latent_skeptic at ff9a63c (`../../../dut/latent_skeptic`): `pipeline.js`, `triage_workflow.js`, `gates/`, `.claude/agents/`,
  copied here read-only. Design mode is NOT run: the card is the design. `out/design.json` is the card's PLAN compiled by
  hand into the design-record schema (mapping in QUESTION.md). Triage, gate, build and post run as in design mode.
- `frozen/` copied from `latent_skeptic_meta/experiments/latent_verify_b/frozen` (lambda_run.sh, remote_run.sh,
  provenance.py), read-only; adapted only at header-declared points, per launch, as copies.
- metis at e7acf90 (before this folder).
- Hashes of every input: `out/INPUT_HASHES.txt`.

## Budget (owner, 2026-10-20)

- Project cap, Lambda, all runs from now: USD 500.
- Calibration and smoke measurements (this kind): fuzzy limit, about USD 10 per run, no re-approval needed.
- Full runs: hard limit, owner approves each spend above USD 20 before launch.
- This run: hard cap USD 5, one launch, cheapest single-GPU instance with capacity.

## Sequence

1. `SEALED_PREDICTIONS.md` written and hashed before any agent runs (`out/SEALS.txt`).
2. Triage: Workflow `triage_workflow.js` on the design-as-claim, exactly as pipeline.js design mode frames it.
3. `out/design_record.json` = {seed, design, diff, triage, gate}; `GATE_COMMIT.md` answers every queued item.
4. Build: Workflow `pipeline.js` mode build, tag m1, conventions frozen/, exec_note EXEC_NOTE.md.
5. Run: per-launch launcher copy; detached via setsid; teardown confirmed through the API.
6. Post: Workflow `pipeline.js` mode post; TAKEAWAYS_m1.md is the answer.
7. Ledger: `../../_meta/LEDGER.jsonl` gets one row: card, prediction, outcome, cost.

Models: every agent pinned in the scripts (sonnet, opus, haiku). None on Fable. The operating session is Fable; nothing
unpinned may run.

## Log

- 01:45Z sealed predictions, design, diff hashed (`out/SEALS.txt`).
- 01:46Z triage wf_1afd659f-b55, 18 s: decidability RULED_OUT; coordinates/scale NEEDS_RUN (one control queued);
  7 instrument validations queued. **Deviation:** the isolated reader did not run (`triage-reader` agent type not
  found: role files copied into this session's project after the session started). Grounding null; answered of record
  in GATE_COMMIT.md G1. Return saved verbatim: `out/triage_wf_1afd659f-b55_return.json`.
- 01:5xZ GATE_COMMIT.md and EXEC_NOTE.md written and hashed; build wf_feb9c78c-9c3 launched (GateCheck sonnet, build opus).
- Launcher copies made while no box runs: `lambda_run_m1.sh` (header-declared points only; 61 changed or added lines,
  all in the scp payload, remote dir, forwarded env, bootstrap name and fetch paths; `bash -n` ok) and
  `remote_run_m1.sh` (cd line only).
- Lambda at 01:4xZ: 0 instances; A6000 no capacity; A10 $1.29/h in us-east-1 and us-west-1.
- 02:2xZ build wf_feb9c78c-9c3 returned after 39 min: GateCheck 14 of 14 answered; `run_m1.py` (2,650 lines) and
  `onbox_m1.sh` (174 lines). Selftest 110/110 under the operator's own run (`out/selftest_m1_operator.log`). The
  builder's float64 reference equations reproduce the page's three values on the committed data before launch:
  0.4948, 0.3360, 0.5699. Build return: `out/build_m1_wf_feb9c78c-9c3_return.json`. Hashes: `out/BUILT_HASHES.txt`.
  Builder readings accepted as recorded: parameter ranges from CreateCalibOptions.R mapped through
  TransfoParam_GR4J.R (X1, X3 in [4.6e-5, 21807]; X2 in [-10904, 10904]; X4 in [0.5, 20]), drawn uniformly in
  parameter units with seed 0; probe in blocks of 100 iterations; float32 on the box.
- Launcher: `INSTANCE_TYPE` added to the forwarded env (additive, declared point) so records carry the instance.
  Result dir at the run root (`results_m1/`, as lvb did), not `out/results_m1/` as EXEC_NOTE said: the launcher puts
  the result dir name into the Lambda instance name and a slash there is untested.
- Risk accepted: `remote_run_m1.sh` keeps the frozen Gemma bootstrap (only its cd line may change); an irrelevant
  import failure there would stop the run before `onbox_m1.sh`.
- 02:3xZ LAUNCH 1 (of at most 1): `PRICE_USD_PER_HOUR=1.29 BUDGET_LEFT_USD=5 REMOTE_TIMEOUT=5400
  INSTANCE_TYPE=gpu_1x_a10 setsid nohup bash lambda_run_m1.sh gpu_1x_a10 us-east-1 onbox_m1.sh results_m1`, log
  `out/launcher_m1.log`. Expected 40 to 90 min, USD 1 to 2.
- 03:01Z LAUNCH 1 HALTED at setup: `pip install -U "jax[cuda12]"` at about 450 kB/s hit its 1500 s timeout inside
  the 766 MB cuDNN wheel (exit 124); `onbox_m1.sh` stopped cleanly, rc=2, run_valid false, no stage run. Operator
  finding on the still-live box: the image already has JAX 0.6.0 with `[CudaDevice(id=0)]`. Launcher observation:
  26 min of silence in the poll loop, then "DONE marker after 60s" (counter counts its own sleeps; D3). Box
  terminated by the launcher's EXIT trap, API-confirmed: 02:31:55Z launch, 03:04:33Z terminate, 0.54 h,
  about USD 0.70. Launch 1 outputs archived under `out/launch1/`.
- 03:1xZ Gate addendum A1 to A4 (preinstalled JAX, pyreadr only; summary file; launch 2 authorised within the same
  USD 5 cap; launcher unchanged). EXEC_NOTE.md updated (checklist items 13 and 14, toolchain step 1). Build re-run
  through pipeline.js build mode; no built file edited by hand.
- 03:20Z build 2 (wf_8e148711-9bc, 14 min): GateCheck 14 of 14; `run_m1.py` 2,939 lines
  (98854eeb…), `onbox_m1.sh` 184 lines (f9067b23…), hashes in `out/BUILT_HASHES_build2.txt`. Selftest 135/135 under
  the operator's own run (`out/selftest_m1_operator_build2.log`); heavy imports blocked for the whole selftest. Changes:
  preinstalled JAX kept, `pyreadr` only, version comparison before and after the install, `m1_summary.json` on every
  exit path. Builder re-checked the day-step equations against `frun_GR4J.f90` and the R defaults (stores start 0.3
  and 0.5 full; warm-up up to one year plus a leap day).
- 03:2xZ LAUNCH 2 (of 2 authorised): same command with `BUDGET_LEFT_USD=4`; launch 1's results moved to
  `out/launch1/`. Monitor armed on `out/launcher_m1.log`.
- 03:52Z launch 2 progress read on the box: stages extract, anchor_airgr, anchor_jax, timers, timing_gpu, timing_cpu,
  probe_gpu all exit 0 by 03:32Z (8 min after start); probe_cpu running at about 1,080 ms per iteration (3 seeds x
  1,001 iterations, about 54 min). Projected spend at that point USD 0.96 of the USD 4 cap.
- **Launcher deviation, seen on both launches:** the ssh call that starts the detached on-box job does not return
  until the remote job exits (26 min and counting on launch 2; on launch 1 it returned when pip timed out), so the
  launcher never prints "[run] confirmed started" or any "[poll-run]" line while the run is live, and then reports
  the DONE marker "after 60s". Completion, fetch and teardown still happen (launch 1 showed this). Billing stays
  bounded by the on-box time guard and the backstop. Not repaired here; candidate cause for the next frozen
  launcher version: a descendant of the detached job holding the ssh session's channel open.
- 03:53Z airGR install on launch 2 failed before R was reached: `apt-get install` fetched 104 packages then hit 404s on
  three security.ubuntu.com .deb files (stale package index on the image; `apt-get update` was not run first, and the
  directive allowed one attempt). E1 and I1 are NOT_RUN; the run carries "anchor by page value". Fix for the next
  directive: `apt-get update` before `install`. The JAX anchors reproduce all three page values on both backends
  (0.4948, 0.3360, 0.5699).
- 04:27Z LAUNCH 2 DONE rc=0. Launcher: ssh start call blocked until remote exit (as on launch 1), then DONE marker,
  summary verified, full fetch, teardown accepted; API: launch 03:21:36Z, terminate 04:27:43Z, 1.10 h, USD 1.42.
  **Lambda total for the run: USD 2.12** (launch 1 0.70 + launch 2 1.42) of the USD 5 cap; project USD 2.12 of 500.
- Records (14, `results_m1/out/records/`), run_valid true, label "anchor by page value":
  E1 NOT_RUN (apt 404s); E2 PASS, JAX reproduces 0.4948 / 0.3360 / 0.5699 on GPU and CPU (page 0.495 / 0.336 / 0.57);
  E3 REFUTED: batched_forward_ms 88.36 (card guess 2; 44x); E4 REFUTED: cpu_671_hours 29.84 (card guess 3; 10x);
  E5 **if_not**: main_run_hours 2.46, speedup 12.1, overhead_gpu 1.0035, overhead_cpu 1.035; E6 card gate pass
  (2.46 <= 6); E7 linear (throughput ratio 8.76 for 10x chains). I3 to I7 PASS; I1 NOT_RUN; I2 PASS (page value only).
  GPU time per pass: 77.3 / 82.5 / 88.4 ms at 268 / 1,340 / 2,684 chains (flat: latency-bound on the 7,300-step
  recurrence). CPU: 131 / 583 / 1,037 ms (throughput-bound). Identical-chains rows within 1% of distinct-chains rows.
- Ledger row appended: `../../_meta/LEDGER.jsonl` (first row). Card write-back: `out/CARD_WRITEBACK_m1.json`.
  Sealed predictions scored: `out/PREDICTIONS_SCORED.md` (Brier 0.177 over 9; held 5, wrong 4, unresolved 1).
- 04:3xZ post mode wf_a438614d-1b5 launched (elicit, question triage, TAKEAWAYS_m1.md under the two gates).
- 05:35Z post done (39 agents, 6.4 min): GateCheck 14/14; 8 elicited questions; top 3 triaged (reader failed again,
  agent type not found; skeptic findings in the workflow journal). `TAKEAWAYS_m1.md` written: gates on the text above
  the raw-samples heading 3.9 codes/1000 words and 0 unscoped sentences (writer's run, pasted in the file); on the
  whole file 8.5 codes/1000 and 5 unscoped sentences (operator's run; the rule applies above the heading).
  Verdict as written there: the card's if_not holds by its own rule, with thin margin, resting on an overhead factor of
  about 1 from a probe that stores no samples and whose acceptance fell to 0.0015. Caveats appended to the ledger
  (row 2). Hashes of all outputs in `out/SEALS.txt`.
- Close: Lambda USD 2.12 total (two launches), 0 instances. Claude usage: triage 4 agents, build 2+2, post 39.
  Nothing committed or pushed.
