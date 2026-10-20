# Interventions log: measure run m3 (coolant V1 card, MD throughput)

Same format as `../../reshape-test/20261020-0855-measure/INTERVENTIONS.md`. Actors: `operator` (the operating Claude
session, by hand), `workflow:<name>` (one Workflow tool call sets it off; everything inside is the script's),
`script:<name>` (shell or Python with no model). `mech`: yes = the pipeline did it; no = operator only; partly = the
pipeline has the step but the operator prepared or repaired its input.

| # | UTC | actor | action | mech | note |
|---|---|---|---|---|---|
| 1 | 10:15 | operator | picked the card to measure (V1 "force-field error floor", PASS 2/2) over V3 (needs GROMACS ester topologies the repo lacks) and over molecular pose estimation (no card; two readings of the phrase; collaborator's question not in hand) | no | the choice of what to measure is the operator's; recorded in RUN.md |
| 2 | 10:20 | operator | created run dir; copied pipeline.js, triage_workflow.js, gates/, frozen/ read-only from m2; copied the pilot's committed data (builder, three decks, READMEs, environment.yml, dataset.csv) and verified every file against the pilot's QUESTION.md hashes; hashed inputs | no | |
| 3 | 10:21 | operator | installed micromamba in the session scratchpad and created an env (rdkit 2025.09.5, packmol, LAMMPS 2024.08.29 CPU) to build the box locally; the pilot's local toolchain is gone from this workstation | no | the pilot's "boxes are built on the workstation" step has no pipeline mechanism |
| 4 | 10:25 | operator | wrote this file, RUN.md, SEALED_PREDICTIONS.md; sealed the hash | no | |
| 5 | 10:26 | operator | wrote QUESTION.md (compiled from the card), out/design.json (10 endpoints), out/diff.json (7 departures); hashed | no | card2question by hand again |
| 6 | 10:27 | operator | ran the committed builder locally (first try failed: Packmol not on PATH; second try exit 0 in 12 s); hashed the box files into the input list | no | pre-launch build step has no pipeline mechanism; the pilot's runner did it inside its extract stage |
| 7 | 10:28 | operator | made launcher copies lambda_run_m3.sh and remote_run_m3.sh from m2's at the declared points | no | |
| 8 | 10:29 | operator | zero-step read_data of the box in the CPU LAMMPS env (E1 part 2, pass); built triage args as design mode frames them; set off Workflow triage_workflow.js | partly | one Workflow call |
| 9 | 10:31 | workflow:triage (wf_fb02fd5d-a4e) | FAILED: reader agent type not found (as before) and all 5 skeptic/adjudicator agents "Login expired · Please run /login"; returned an empty findings list with both confounds marked rejected (an artifact of the failures, not a verdict); return saved as out/triage_wf_fb02fd5d-a4e_FAILED_login_expired.json and not used | yes | the runtime reported the failures; it did not halt the script, which returned a misleading empty triage |
| 10 | 10:32 | owner | ran `/login` in the session ("Login successful") | no | a human action the operator cannot take |
| 11 | 10:32 | operator | relaunched triage with identical arguments | partly | |
| 12 | 10:33 | workflow:triage (wf_0cc4d978-d33) | 4 agents, 35 s: reader RAN (first time in this program; "unauditable": pre-launch artifacts confirmed, box outputs not yet exist, builder exit code in no artifact); 2 skeptics NEEDS_RUN; 1 run-queue control (timed GPU dry run, units check); 10 instrument validations queued | yes | role files now loaded (metis/.claude/agents, refreshed at /login) |
| 13 | 10:34 | operator | wrote out/prelaunch_build_mol00557.json (the artifact the reader asked for); assembled design_record.json | partly | the reader's finding was consumed by the operator writing a record; no mechanism records a pre-launch step |
| 14 | 10:40 | operator | wrote GATE_COMMIT.md (D1-D7, G1, R1 dry run, I1-I10, labels, A1) and EXEC_NOTE.md (14-item checklist); set off Workflow pipeline.js mode build | partly | gate is a human role; one Workflow call |
| 15 | 11:22 | workflow:build (wf_2975691d-aa9) | GateCheck 19/19; build (opus) wrote run_m3.py (3,072 lines) and onbox_m3.sh (172 lines), selftest 282/283, then STOPPED by design: the directive's planted I7 value (1.3021e10) contradicts the directive's formula (1.3021e7); four readings listed for ruling; 44 min | yes | the pipeline's selftest discipline caught the gate's arithmetic error; no launch happened on a wrong spec |
| 16 | 11:24 | operator | ruled by gate addendum A2 to A5 (formula binds; planted value 1.3021e7; builder readings accepted); corrected EXEC_NOTE item 9; archived build 1's files; set off build 2 with the revised directive (fresh run, not a cache resume) | partly | the ruling is the gate's; the re-run is one Workflow call |
| 17 | 11:45 | workflow:build 2 (wf_4df87803-b95) | GateCheck 19/19; build (opus) rewrote run_m3.py (3,336 lines), onbox_m3.sh (178 lines); selftest 313/313; STOPPED by design: conda-forge LAMMPS CUDA builds have PKG_GPU=OFF (KOKKOS instead), read from every feedstock recipe revision 2024-2026; two options listed; 15 min | yes | second stop before any spend; the pilot's RUN_LOG step 4d had said so and the operator missed it |
| 18 | 11:48 | operator | ruled by gate addendum A7 to A9: compile LAMMPS stable_29Aug2024 from source on the box with the GPU package (sm_80), cmake from the image or pip, FFTW3 or KISS, mixed precision labelled; REMOTE_TIMEOUT 7,200 s; rewrote EXEC_NOTE item 11; archived build 2's files; set off build 3 | partly | the engine decision is the gate's; one Workflow call |
| 19 | 11:57 | workflow:build 3 (wf_881fe8ab-bfb) | GateCheck 19/19; build (opus) wrote run_m3.py (3,772 lines), onbox_m3.sh (266 lines); selftest 365/365; ready, one ruling asked: the directive's stale "conda-forge" engine label; 21 min | yes | third catch of a gate inconsistency before any spend |
| 20 | 11:59 | operator | ruled by addendum A10 (label text), A11 (build 4); fixed EXEC_NOTE item 10; archived build 3; set off build 4 | partly | one constant; the law "no hand edit of built files" kept at the cost of one more build |
| 21 | 12:01 | workflow:build 4 (wf_5b14e871-632) | GateCheck 19/19; build (opus) changed the label constant and added two selftest checks tying it to the directive; selftest 367/367; 3.5 min; ready | yes | |
| 22 | 12:03 | operator | ran the selftest myself (367/367); hashed built files; diffed against build 3 (19 lines, label and checks); read onbox_m3.sh in full (compile stage, guards, exit paths; rm -rf scoped to engine dirs); checked the launcher's backstop against the 7,200 s window | partly | "human reviews files, then runs the launcher verbatim" |
| 23 | 12:05 | operator | LAUNCH 1: `REMOTE_TIMEOUT=7200 PRICE_USD_PER_HOUR=1.99 BUDGET_LEFT_USD=5 INSTANCE_TYPE=gpu_1x_a100_sxm4 setsid nohup bash lambda_run_m3.sh gpu_1x_a100_sxm4 us-east-1 onbox_m3.sh results_m3` (sandbox off), log out/launcher_m3.log; monitor armed | partly | the launcher is deterministic from here |
| 24 | 12:14 | script:lambda_run_m3.sh + onbox_m3.sh + run_m3.py | LAUNCH 1 on box 7fd3a46c…: compile 113 s (cmake from image, KISS FFT, GPU package mixed precision); lmp -h check pass; timed dry run RUNS_AGREE at 13.5 ns/day (78 steps/s); guard STOP before the box copy (875,000 steps at 78 steps/s need 10,558 s; 7,009 s left); exit 3; summary, fetch, terminate; 12:05:10Z to 12:14:09Z, USD 0.30 | yes | the guard did what it was built to do; no overspend |
| 25 | 12:15 | operator | read the fetched records and guard rows; archived launch 1 under out/launch1/; wrote gate addenda A12 to A14 (shorter protocol: 450,000 steps; window 9,000 s); revised EXEC_NOTE item 2 and caps; archived build 4; set off build 5 | partly | re-planning after a guard stop is the gate's; one Workflow call |
| 26 | 12:27 | workflow:build 5 (wf_4759c384-967) | GateCheck 19/19; build (opus) shortened the -var constants, density window, row counts, default window; 16 new selftest checks incl. a replay of launch 1's guard readings (now "go, cuts nothing"); selftest 383/383; 12 min | yes | |
| 27 | 12:28 | operator | ran the selftest myself (383/383); hashed; diffed onbox_m3.sh (two lines: the 9,000 s default); checked capacity and zero instances; LAUNCH 2: `REMOTE_TIMEOUT=9000 PRICE_USD_PER_HOUR=1.99 BUDGET_LEFT_USD=5 INSTANCE_TYPE=gpu_1x_a100_sxm4 setsid nohup bash lambda_run_m3.sh gpu_1x_a100_sxm4 us-east-1 onbox_m3.sh results_m3`; monitor armed | partly | |
| 28 | 12:41 | script:onbox_m3.sh + run_m3.py | launch 2: compile 2 min; dry run RUNS; equilibration attempt 1 refused by pppm/gpu + fix balance; A6 fallback (edit 3) applied automatically and attempt 2 started; guard go | yes | the gate's queued control fired as designed, no operator action |
| 29 | 12:41 | operator | read progress on the box over ssh (the launcher is silent while live) | no | |
| 30 | 13:58 | script:lambda_run_m3.sh + onbox_m3.sh + run_m3.py | LAUNCH 2 complete: compile, dry run, copy, equilibration (edit 3 applied automatically), runs a/b/c, endpoints; 36 records; DONE rc=0; fetch; terminate; 12:28:32Z to 13:57:47Z, USD 2.96 | yes | |
| 31 | 14:00 | operator | two progress reads over ssh during the run; read the records; confirmed teardown and billing via the API | no | |
| 32 | 14:05 | operator | wrote out/CARD_WRITEBACK_m3.json and out/PREDICTIONS_SCORED.md; appended ledger row 5; set off Workflow pipeline.js mode post | partly | one Workflow call; write-back and ledger have no mechanism |
| 33 | 14:16 | workflow:post (wf_890f436a-e4f) | GateCheck 19/19; elicit 8 questions; nested triage of top 3 with the reader running (reproduces x3); write TAKEAWAYS_m3.md in the run dir with both gates run; 39 agents, 10 min, 0 failures | yes | first fully clean post in the program |
| 34 | 14:18 | operator | re-ran both gates on the truncated copy; hashed TAKEAWAYS; read sections 4-5 | partly | |
| 35 | 14:20 | operator | appended ledger caveats row 6 (12 caveats from the post and the operator's checks); closed RUN.md; wrote the tally below | no | nothing writes the ledger |

## Tally

| Actor | Rows | What |
|---|---|---|
| operator (by hand) | 1, 2, 3, 5, 6, 7, 8, 13, 14, 16, 18, 20, 22, 23, 25, 27, 29, 31, 32, 34, 35 (21, of which 7 are gate rulings or re-plans) | pick; run-dir setup; local toolchain and box build; QUESTION/design/diff; launcher copies; design_record; gate commit and directive, plus five addenda (I7 arithmetic, engine, label, lengths, A6 fallback); build reviews and selftest re-runs; launches; progress reads over ssh; billing; write-back, scoring, ledger; TAKEAWAYS gate re-run |
| owner | 10 (1) | `/login` after the session's login expired |
| operator setting off a workflow (one tool call each) | 4, 11, 9*, 14, 16, 18, 20, 25, 32 (9 calls: triage x2, build x5, post x1; *row 9 is the failed triage) | |
| workflow (agents inside a script) | 9, 12, 15, 17, 19, 21, 26, 33 (8 workflow runs; 6 + 4 + 2 x 5 + 39 = 59 agents) | triage (failed on login, then clean with the reader); five builds (two stopped on the gate's errors, one on an engine fact, one label, one lengths); post |
| script (no model) | 24, 28, 30 (3) | launcher lifecycle twice; on-box driver and runner: compile, dry run, guard stop (launch 1), A6 fallback, full run (launch 2) |

Compared with m2 (16 operator rows of 25), m3 needed 21 operator rows of 35, seven of them gate rulings after a stop.
Every stop before spend was the pipeline's: the builder's selftest caught two errors in the gate's own text, read a
packaging recipe the gate had not, and refused to launch on a false label; the on-box guard stopped launch 1 before
an overrun; the queued A6 control fired on its own. The operator's hand remained in the same places as m2 (card
compile, gate, launcher, ledger) plus two new ones: the local box build (the pilot's halt) and the engine ruling.

## How the workflows are set off

As in m2's log: one `Workflow` tool call per stage with `scriptPath` on the committed script and an `args` object
(triage: claims + instruments as design mode frames them; build: design_record, gate_commit, tag, conventions,
exec_note; post: those plus results_dir, triage_path, gates_dir, seed_file). Each `agent()` inside spawns one pinned
subagent (sonnet or opus; never Fable); post nests triage. This run adds two facts: a re-run of a stopped build must be a
fresh call (a resume replays the cached stop), and the agent types for the isolated reader loaded mid-session once the
role files sat in `metis/.claude/agents/` and the session's login was refreshed.
