# Interventions log: measure run m2 (P card, PCR vs Thomas)

Purpose: record every action in this run by actor, so the operator's hand can be separated from what the pipeline
did on its own. Written by the operating session as it goes; each row is appended before or right after the action.

Actors:
- `operator`: the operating Claude session (Fable), acting by hand with Bash, Write, curl, ssh.
- `workflow:<name>`: a Claude Code Workflow run (`triage_workflow.js` or `pipeline.js`), set off by one Workflow tool
  call from the operator; everything inside it (agent spawning, phases, schemas, halts) is the script's own.
- `script:<name>`: a committed shell or Python script running without a model (launcher, on-box driver, gates).

`mech` column: does a pipeline mechanism exist for this action? `yes` = the pipeline did it; `no` = operator only;
`partly` = the pipeline has the step but the operator had to prepare or repair its input.

| # | UTC | actor | action | mech | note |
|---|---|---|---|---|---|
| 1 | 08:55 | operator | created run dir; copied pipeline.js, triage_workflow.js, gates/, frozen/ read-only from m1; verified byte-identical to dut ff9a63c; hashed inputs (out/INPUT_HASHES.txt); symlinked .keys | no | a `launch.js measure` would do this |
| 2 | 08:56 | operator | wrote this file, RUN.md, SEALED_PREDICTIONS.md; sealed hashes | no | predictions are the operator's own, not a pipeline role |
| 3 | 09:00 | operator | compiled the card's PLAN into QUESTION.md, out/design.json (design-record schema), out/diff.json (7 departures); hashed | no | the `card2question.js` + design-mode step the pipeline lacks for a card input; in design mode a sonnet agent writes design and diff from a seed text |
| 4 | 09:01 | operator | built triage args exactly as pipeline.js design mode frames them (claim = design-as-claim; instruments = one per endpoint) and set off Workflow triage_workflow.js | partly | framing copied from pipeline.js lines 92-105; the Workflow call itself is the operator's one action |
| 5 | 09:02 | operator | made per-launch launcher copies lambda_run_m2.sh (from m1's copy via sed at the declared points: remote dir, payload, bootstrap name, fetch paths; data scp line removed) and remote_run_m2.sh (cd line only); `bash -n` ok | no | frozen/ header declares the points; the adaptation is always by hand |
| 6 | 09:02 | workflow:triage (wf_da9ff4cd-543) | 4 agents (reader failed: agent type not found; 2 skeptics sonnet; 1 adjudicator sonnet), 23 s: decidability RULED_OUT, scale NEEDS_RUN, 1 run-queue item, 10 instrument validations queued | yes | reader failure = known session-start limitation, deviation G1 |
| 7 | 09:03 | operator | saved the triage return verbatim; assembled out/design_record.json {seed, design, diff, triage, gate} as design mode would return it | partly | design mode returns this object; here the operator assembled it because design mode was not run |
| 8 | 09:05 | operator | wrote GATE_COMMIT.md (D1-D7, G1, R1 with launch-probe control, I1-I10, timers, propagation, labels, A1 pre-authorisation) and EXEC_NOTE.md (16-item checklist, two-files law for the CUDA source, toolchain rule) | no | the gate is a human role by design; the operator stood in |
| 9 | 09:06 | operator | set off Workflow pipeline.js mode build (GateCheck sonnet, build opus) | partly | one Workflow call; everything after is the script's |
| 10 | 09:45 | workflow:build (wf_7bcc0b19-df0) | GateCheck (sonnet) 19 of 19 answered; build (opus) wrote run_m2.py (2,836 lines, CUDA C as a string) and onbox_m2.sh (76 lines); selftest 115/115; 39 min; 12 builder choices (a)-(l) listed for veto | yes | no built file edited by hand |
| 11 | 09:46 | operator | ran the selftest myself (115/115, out/selftest_m2_operator.log); hashed built files (out/BUILT_HASHES.txt); read onbox_m2.sh in full; grepped run_m2.py for installs or deletions (none; two rmtree on temp dirs); accepted all 12 builder choices, none vetoed | partly | the pipeline says "human reviews files, then runs the launcher verbatim"; the review is the operator's |
| 12 | 09:46 | operator | decided against a local GPU smoke test (workstation has a GTX 1070 but no nvcc; the pipeline runs only the selftest locally; the box is the test) | no | recorded as a choice |
| 13 | 09:46 | operator | checked Lambda: 0 instances, A100 SXM4 capacity in us-east-1 at USD 1.99/h | no | a `launch.js` would do this |
| 14 | 09:47 | operator | LAUNCH 1: `PRICE_USD_PER_HOUR=1.99 BUDGET_LEFT_USD=6 INSTANCE_TYPE=gpu_1x_a100_sxm4 REMOTE_TIMEOUT=3600 setsid nohup bash lambda_run_m2.sh gpu_1x_a100_sxm4 us-east-1 onbox_m2.sh results_m2` (sandbox off), log out/launcher_m2.log | partly | the launcher (script:lambda_run_m2.sh) is deterministic from here: launch, poll, scp, detached run, fetch, terminate |
| 15 | 09:54 | script:lambda_run_m2.sh | boot poll (19 polls), sshd wait, scp payload, backstop armed (5,400 s), detached run started 09:51Z | yes | deterministic launcher |
| 16 | 09:54 | script:onbox_m2.sh + run_m2.py | build (nvcc, sm_80), gpucheck, anchor (E1 PASS, E2 REFUTED too pessimistic, I1 x3 PASS), timers, residual_sweep, thomas_gpu running | yes | all guards passed |
| 17 | 09:54 | operator | read progress on the box over ssh (stages.jsonl, log tails) | no | the launcher prints nothing while its start-ssh call blocks (known deviation); the only live view is a manual ssh |
| 18 | 10:00 | script:lambda_run_m2.sh | DONE marker rc=0; criticals-first fetch; full fetch (try 1); terminate accepted; EXIT trap | yes | deterministic |
| 19 | 10:01 | operator | confirmed teardown through the API (terminating, then 0 instances); read audit events for exact billing (09:46:22Z to 10:00:43Z, 0.239 h, USD 0.48) | no | the launcher does not read back billing |
| 20 | 10:05 | operator | read m2_summary.json and the 35 records; scored the sealed predictions (out/PREDICTIONS_SCORED.md); wrote out/CARD_WRITEBACK_m2.json; appended the ledger row | no | `result2card.js` and a ledger writer are the missing mechanisms |
| 21 | 10:08 | operator | set off Workflow pipeline.js mode post | partly | one call; elicit, question triage (nested triage workflow), write and gates are the script's |
| 22 | 10:16 | workflow:post (wf_c1d43903-ecc) | GateCheck 19/19; elicit (sonnet) 8 questions; nested triage of top 3 (readers failed, agent type not found; skeptics + adjudicators sonnet); write (sonnet) TAKEAWAYS_m2.md with both gates run by the writer; 39 agents, 7.8 min | yes | reader failure = G1 again |
| 23 | 10:17 | operator | moved TAKEAWAYS_m2.md from reshape-test/ into the run dir (the writer read "this repo" as the parent); no edit | no | deviation of the write prompt's "in this repo" |
| 24 | 10:17 | operator | re-ran both gates on the truncated copy (1.3 codes/1000, 0 unscoped); hashed TAKEAWAYS; noted the footnote-marker workaround of gate_scope | partly | gates are scripts; the operator's re-run is a check on the writer's pasted output |
| 25 | 10:20 | operator | appended the ledger caveats row from TAKEAWAYS sections 4-5, the post triage and two row/log checks (77 of 150 blocks under 50 ms confirmed; "installs" were the frozen bootstrap's, not the design's); closed RUN.md | no | post mode writes TAKEAWAYS; nothing writes the ledger |

## Tally

| Actor | Rows | What |
|---|---|---|
| operator (by hand) | 1, 2, 3, 5, 7, 8, 11, 12, 13, 14, 17, 19, 20, 23, 24, 25 (16) | run-dir setup; sealed predictions; card -> QUESTION/design/diff compile; launcher adaptation; design_record assembly; gate commit and build directive; review of built files and selftest re-run; capacity check; launch command; live progress read over ssh; billing read; scoring, write-back, ledger; TAKEAWAYS move; gate re-run; caveats |
| operator setting off a workflow (one tool call each) | 4, 9, 21 (3) | triage, build, post |
| workflow (agents inside a script) | 6, 10, 22 (3 workflows; 4 + 2 + 39 = 45 agents) | skeptics and adjudication; GateCheck and build; GateCheck, elicit, nested triage, write and gates |
| script (no model) | 15, 16, 18 (3) | launcher lifecycle (launch, poll, scp, backstop, detached run, fetch, terminate); on-box driver and runner (12 stages, guards, 35 records, 368 rows, summary) |

Of 25 rows, 16 are operator actions with no pipeline mechanism, 3 are the operator's single calls that set a workflow
off, and 6 are the pipeline running on its own. Measured by wall-clock, the pipeline did almost all of the work
(build 39 min, post 8 min, box 14 min, triage 23 s); measured by decisions, the operator made every decision between
stages (what to measure, the gate answers, which builder choices to accept, when to launch, what the ledger says).

Where the operator's hand was unavoidable with the pipeline as it stands:
- there is no `card2question`: a card's PLAN had to be compiled into QUESTION.md and design.json by hand (row 3);
- design mode was not run, so design_record.json was assembled by hand (row 7);
- the gate is a human role by design (row 8); here the operator stood in, on the owner's budget rules;
- the launcher is adapted per launch at declared points (row 5) and set off by hand (row 14), and it prints nothing
  while the run is live (row 17);
- nothing reads billing back (row 19), nothing writes the card write-back or the ledger (rows 20, 25);
- the writer's "in this repo" put TAKEAWAYS one directory up (row 23).

Where the pipeline failed on its own: the isolated reader, in triage and in post (agent type not loaded at session
start); the writer's footnote workaround of gate_scope.

## How the workflows are set off

Each workflow is one `Workflow` tool call from the operating session with `scriptPath` pointing at the committed
script (`triage_workflow.js` or `pipeline.js`, byte-identical copies of dut ff9a63c) and an `args` object:
- triage: `{claims: [{id, text, evidence, confounds}], instruments: [{id, version, asserts, validation_artifact: null}]}`,
  framed exactly as pipeline.js design mode frames them (the design-as-claim, one instrument per endpoint);
- build: `{mode: 'build', design_record, gate_commit, tag, conventions, exec_note}`;
- post: `{mode: 'post', design_record, gate_commit, results_dir, tag, triage_path, gates_dir, seed_file}`.
The runtime runs the script in the background; every `agent(prompt, {model, schema, agentType?})` inside it spawns one
subagent of the pinned model (sonnet or opus here; never Fable); `workflow({scriptPath})` nests a workflow (post nests
triage). The script's return value arrives as a task notification; the per-agent results sit in the run's
`journal.jsonl`. The operator then writes the next file by hand (gate commit after triage; launcher after build;
ledger after post). The launcher and the on-box driver are not workflows: they are shell scripts run once, detached
(`setsid nohup`), and they finish on their own.
