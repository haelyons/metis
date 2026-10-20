# reshape-test · measure · 20261020-0855

Kind: measure. The decides-by phase (`p2_sweep`, with its anchor `p1_anchor`) of the P arm's physical card, run as a
latent_skeptic run, so the card's own prediction is resolved by a measurement and lands beside the card it came from.
Second measure run in this experiment (first: `../20261020-0145-measure`, m1). Tag: m2.

## Source card

- Run: `../20261019-2344-tree` (arm P, planted root), pick R1 · physical · "Cyclic reduction (PCR) · Parallel cyclic
  reduction". Dramaturg verdict on the card: **REJECT (3 blocking)**, all on citations (the plan's own predictions and
  one literature-gap claim cited to no source); critic reshape 4, baseline 5, lever 5, stakes 3.
- Record: `../20261019-2344-tree/out/result.json` sha256 `48ac464c98a73069aab7af8efbd53021ca5439a193af666a2e1ac6d0d32ac6ae`;
  rendered `../20261019-2344-tree/out/RESULT.md` sha256 `ac1ccd211ff8ebdff09116f2aaaf52063942463b1a0bda6e838bd8fd3ccc1a07`.
- Producer reply (the PLAN): `../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt`
  sha256 `5edcb633490ee446d7a77a8f32cf246efae31aab79919fe6b21ac4f6aa411b33`.
- Prediction under test: `expected: if_lever`, by its own decision rule: "Lever if median PCR time < median Thomas time
  at n_max=2^24 by at least gate_speedup=2x, and the PCR/Thomas speedup grows with N; otherwise not."
- Card numbers measured here: `res_measured` GUESS 1e-13 (`p1_anchor`); `crossover_n` GUESS 1,024 (`p2_sweep`);
  `speedup_at_nmax` PROXY 28 (`p2_sweep`); cost line `l_anchor_sweep` hours 6, need 2 on A100 SXM 40 GB at USD 1.99/h.
- Card gate at `p1_anchor`: `res_measured <= 1e-10`, else "Fix the kernels and re-run the anchor before starting the sweep".

## Adjustments decided by the operator before any agent ran (each is a departure of record; see out/diff.json)

1. **No producer resample before measuring.** The dramaturg's REJECT is about citations for the plan's own predictions
   and a literature-gap sentence. A resample rewrites the PLAN (new numbers, new rule), so the measurement would then
   resolve a card that is not the committed record. The measurement binds to the committed record and carries the label
   "card dramaturg: REJECT (citations)". The if_lever / if_not sentences the dramaturg called unsupported are what this run
   measures.
2. **Hardware as the card states.** `gpu_1x_a100_sxm4` has capacity in us-east-1 at USD 1.99/h (the card's rate and GPU),
   so no instance substitution this time. Rule if capacity vanishes at launch: cheapest single GPU with capacity,
   recorded as a departure.
3. **The CPU floor is measured, report-only.** The card's `baseline_sequential` names "MKL dgtsv on the instance CPU as a
   floor" but gives it no endpoint. It is timed here (scipy's LAPACK dgtsv, preinstalled scipy 1.8.0 on the image) and
   the card's rule is re-read against it as a labelled sensitivity line. The card's verdict is read against its own
   baseline only.
4. **Phases p3 (block) and p4 (multi-GPU) are not run** (optional in the card).
5. **Toolchain rule from m1:** nothing is installed on the box unless missing; preinstalled scipy and system CUDA
   libraries are used; nvcc is looked up on PATH and under /usr/local/cuda*/bin; if absent the run halts cleanly with
   RUN_VALID false (no fallback install).
6. **Two launches pre-authorised within one cap** (m1 needed a gate addendum for its second launch).

## Pipeline

- latent_skeptic at ff9a63c (`../../../dut/latent_skeptic`): `pipeline.js`, `triage_workflow.js`, `gates/` copied here
  read-only and verified byte-identical. Design mode is NOT run: the card is the design. `out/design.json` is the card's
  PLAN compiled by hand into the design-record schema (mapping in QUESTION.md). Triage, gate, build and post run as in
  design mode. `.claude/agents/` role files sit at `/home/hal/dev/interp/.claude/agents/` (present since m1; this
  session predates them, so the isolated reader is expected to fail again; see INTERVENTIONS.md).
- `frozen/` as in m1 (lambda_run.sh, remote_run.sh, provenance.py), adapted only at header-declared points, per launch.
- metis at e7acf90 (uncommitted: m1 folder, this folder, `_meta/LEDGER.jsonl`, `.gitignore`, `reshape-test/QUESTION.md`).
- Hashes of every input: `out/INPUT_HASHES.txt`. Every action by actor: `INTERVENTIONS.md`.

## Budget (owner rules of 2026-10-20)

- Project cap, Lambda: USD 500. Spent before this run: USD 2.12 (m1).
- Calibration and smoke measurements (this kind): fuzzy limit about USD 10 per run, no re-approval.
- Full runs: hard limit, owner approves each spend above USD 20 before launch.
- This run: hard cap USD 8, at most two launches, `gpu_1x_a100_sxm4` at USD 1.99/h; expected 0.3 to 0.6 h per launch.

## Sequence

1. `SEALED_PREDICTIONS.md` written and hashed before any agent runs (`out/SEALS.txt`).
2. Triage: Workflow `triage_workflow.js` on the design-as-claim, as pipeline.js design mode frames it.
3. `out/design_record.json` = {seed, design, diff, triage, gate}; `GATE_COMMIT.md` answers every queued item.
4. Build: Workflow `pipeline.js` mode build, tag m2, conventions frozen/, exec_note EXEC_NOTE.md.
5. Run: per-launch launcher copy; detached via setsid; teardown confirmed through the API.
6. Post: Workflow `pipeline.js` mode post; TAKEAWAYS_m2.md is the answer.
7. Ledger: `../../_meta/LEDGER.jsonl` gets one row: card, prediction, outcome, cost.

Models: every agent pinned in the scripts (sonnet, opus). None on Fable. The operating session is Fable; nothing
unpinned may run.

## Log

- 08:55Z run dir made; pipeline files verified identical to dut ff9a63c; inputs hashed.
- 09:00Z QUESTION.md, out/design.json (10 endpoints), out/diff.json (7 departures) written and hashed. Triage launched.
- 09:02Z triage wf_da9ff4cd-543, 23 s: decidability RULED_OUT (design structure); coordinates/scale NEEDS_RUN (one run-queue item); 10 instrument validations queued. **Deviation:** isolated reader did not run (agent type not found, as in m1). Return: out/triage_wf_da9ff4cd-543_return.json.
- 09:05Z GATE_COMMIT.md and EXEC_NOTE.md written and hashed; build launched.
- 09:45Z build wf_7bcc0b19-df0 returned after 39 min: GateCheck 19 of 19; `run_m2.py` 2,836 lines (46faee5d…), `onbox_m2.sh`
  76 lines (3cfe0f6d…), hashes in `out/BUILT_HASHES.txt`; selftest 115/115 under the operator's own run
  (`out/selftest_m2_operator.log`). Builder choices (a) to (l) in `out/build_m2_wf_7bcc0b19-df0_return.json`, all accepted:
  anchor failure labels rows but does not void the run; -arch=sm_80 on A100; batched arm = K copies of the same (N, seed)
  system laid out one after another; cuSPARSE RHS copies before the block; R from the second warm-up; planted controls
  also run on the box; a cuSPARSE run-time error stops the run (the directive covered only a missing library).
  Builder's wall-clock estimate: 8 to 15 min compute, 20 to 40 min billed, USD 0.7 to 1.3.
- 09:47Z LAUNCH 1 (of at most 2): `PRICE_USD_PER_HOUR=1.99 BUDGET_LEFT_USD=6 INSTANCE_TYPE=gpu_1x_a100_sxm4 REMOTE_TIMEOUT=3600
  setsid nohup bash lambda_run_m2.sh gpu_1x_a100_sxm4 us-east-1 onbox_m2.sh results_m2`, log `out/launcher_m2.log`.
  Known launcher deviation (m1): the start-ssh call blocks until the remote job exits; no poll lines while live.
- 09:54Z progress read on the box (ssh, operator): box 3be4cd7175024dcd8ffa23e50d300409, ip 150.136.47.224; nvcc found at
  /usr/bin/nvcc, compiled with -arch=sm_80 in 2 s; GPU check pass; anchor I1 x3 PASS, E1 PASS, E2 REFUTED (too
  pessimistic); timers pass; residual sweep 63 s; thomas_gpu one-thread: 5.14 ms at 2^14, 83.2 ms at 2^18, 1,892 ms
  at 2^22, 7,598 ms at 2^24 (about 0.45 microseconds per equation, linear). scipy warns NumPy 1.26.4 is newer than
  scipy 1.8.0 supports (image as shipped; recorded).
- 10:00Z LAUNCH 1 DONE rc=0. Launcher: start-ssh blocked until remote exit (as in m1), then DONE marker, summary verified,
  full fetch (try 1), teardown accepted; API: launch 09:46:22Z, terminate 10:00:43Z, 0.239 h, **USD 0.48**. 0 instances.
  Project Lambda total USD 2.60 of 500.
- Records (35, `results_m2/out/records/`), run_valid true, labels "card dramaturg: REJECT (3 blocking, citations)" and
  "baseline: one CUDA thread per system, this build's kernel". Compute on the box 7.1 min (E10 span 0.119 h).
  E1 PASS (max relative residual 3.1e-16; cuSPARSE and scipy agree); E2 REFUTED, too pessimistic (guess 1e-13, 320x);
  E3 **if_lever**: speedups 8.5 / 95.9 / 517.5 / 395.4 / 348.3 at 2^10..2^24, slope 0.256 > 0, lower quartile at the
  top 348; two adjacent decreases above 2^18 (strict reading would fail); E4 HOLDS, crossover 1,024, launch-bound
  (launch fraction 0.775); E5 REFUTED above (348x vs proxy 28, 12.4x); E6 linear-like (g 2.135: PCR 4.79 ms at 2^22,
  21.8 ms at 2^24); E7 if_lever under the CPU floor (dgtsv 416.7 ms at 2^24, 19.1x; CPU faster below about 2^12);
  E8 HOLDS (batched/single 1.05 to 1.81); E9 cuSPARSE 2.94 ms at 2^24, this PCR 7.4x slower; E10 REFUTED below
  (0.119 h vs need 2 h, 16.8x). I1 to I10, timers, gate propagation, dispersion, timing-rows check all PASS.
  One-thread Thomas: 0.297 / 5.14 / 83.2 / 1,892 / 7,598 ms (linear, about 0.45 microseconds per equation).
- Ledger row appended: `../../_meta/LEDGER.jsonl` (row 3). Card write-back: `out/CARD_WRITEBACK_m2.json`. Sealed
  predictions scored: `out/PREDICTIONS_SCORED.md` (Brier 0.090 over 12; held 10, did not occur 2).
- 10:08Z post mode wf_c1d43903-ecc launched (elicit, question triage, TAKEAWAYS_m2.md under the two gates).
- 10:16Z post done (wf_c1d43903-ecc, 39 agents, 7.8 min): GateCheck 19/19; 8 elicited questions; top 3 triaged (reader
  failed 3x, agent type not found; skeptics: q1 baseline artifact EXPLAINS the 12.4x proxy miss, q2 CPU faster at 2^10
  EXPLAINS, q3 host-to-device copy NEEDS_RUN). **Deviation:** the writer put `TAKEAWAYS_m2.md` in the experiment dir
  (`reshape-test/`), not the run dir; moved by the operator (mv, no edit). Gates on the text above the raw-samples
  heading: 1.3 codes/1000 words, 0 unscoped sentences (writer's run; operator's run agrees). The writer satisfied the
  scope gate with 23 `[^1]` footnote markers (its model-naming rule does not fit a solver study): a workaround, recorded.
  Hash in `out/SEALS.txt`.
- Caveats appended to the ledger (row 4). Hashes of all outputs in `out/SEALS.txt`.
- Close: Lambda USD 0.48 (one launch, 0.239 h), 0 instances; project total USD 2.60 of 500. Claude usage: triage 4 agents,
  build 2, post 39 (all sonnet/opus by pin). Operator actions vs pipeline actions: `INTERVENTIONS.md`. Nothing
  committed or pushed.
