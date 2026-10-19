You operate one latent_skeptic run in this directory, end to end, without a human. This is attempt 2: attempt 1 halted at
the design budget check on a guessed throughput (HALT_attempt1.md, RUN_LOG.md). QUESTION.md and data/ stand as
written; do not re-seed. Continue RUN_LOG.md under a heading "Attempt 2". Work only inside this directory.
You may read ../latent_verify_b, ../../README.txt and /home/hal/dev/interp/dm_hack/latent_skeptic for reference;
never modify anything outside this directory. Never print, copy or commit the contents of .keys. Never git commit or
push: the repository is public. Keep RUN_LOG.md: one entry per step with time, outcome and Lambda spend so far.

Reference: ../latent_verify_b is a complete worked run of this pipeline (seed, GATE_COMMIT.md, an adapted launcher
lambda_run_lvb1.sh, on-box runner, results, TAKEAWAYS). The header of pipeline.js states the modes and their
required arguments. Run pipeline.js only through the Workflow tool, with scriptPath set to this directory's
pipeline.js and args passed as a JSON value; write each returned value verbatim to out/.

1. Seed. Spawn one fresh agent (Agent tool, general-purpose) whose only input is SEED_INPUT.md and the files it
   names. It writes QUESTION.md meeting the duties listed there, downloads the data it commits into data/, and
   records each file's sha256 in QUESTION.md. If the data cannot be downloaded, it declares the rule that generates
   the data or declares the gap. You do not edit its QUESTION.md.
2. Design. Workflow, design mode: seed = the text of QUESTION.md, triage_path = this directory's triage_workflow.js,
   cap_usd = 20, substrate_note = "One rented Lambda GPU box with a single GPU, driven by the launcher in frozen/;
   molecular dynamics with an open-source engine installed on the box (OpenMM from pip, or LAMMPS); state every
   hardware, throughput and cost assumption as GUESS." followed by the cited throughput below. Before launching
   design, fetch published GPU throughput figures for a solvated system of about 15,000 to 25,000 atoms with
   particle-mesh Ewald (OpenMM's published benchmarks first, then Amber's GPU performance page). Add each to
   substrate_note as one sentence: engine, system, atom count, GPU, ns/day, URL, labelled PROXY ("measured on a
   reference system, not on this liquid; state the factor you apply"). Save the design record and the gate text in
   out/, named for attempt 2.
2b. Calibration, only if design halts on budget again and the overrun rests on a guessed hardware number. It has
   its own cap, separate from the run's: $2 and one launch. Run OpenMM's own published benchmark script (from the
   OpenMM repository, unmodified) for its particle-mesh Ewald test on the cheapest single-GPU instance with
   capacity, through a copy of the launcher with only the edits its header lists. Record the measured ns/day,
   the GPU and the script's source URL in out/calibration.json and RUN_LOG.md. Then rerun design once, with the
   measured figure added to substrate_note labelled MEASURED (reference system). Keep every design return. If that
   design halts on budget too, write HALT.md and stop.
3. Gate. Spawn one fresh agent whose only inputs are the gate text, QUESTION.md and the design record. It writes
   GATE_COMMIT.md answering every queued item of record: accept as-is with a reason, reject, or queue a control the
   budget allows. It may not raise the $20 cap. Give it every design return of record, so it sees why earlier designs halted. You do not edit its answers.
4. Build. Workflow, build mode, binding to the design record and GATE_COMMIT.md, tag cp1, conventions = frozen/.
5. Run. Copy frozen/lambda_run.sh to lambda_run_cp1.sh and make only the edits its header lists (remote folder,
   payload, forwarded environment); keep every billing-safety mechanism. Pick the cheapest single-GPU instance type
   with capacity (poll /instance-types; wait at most 60 minutes). At most two launches. If projected spend would
   pass $20, do not launch. The launcher terminates the box; confirm termination in the log.
6. Post. Workflow, post mode, with the design record, GATE_COMMIT.md, the results folder, tag cp1, triage_path,
   gates_dir = gates/, seed_file = QUESTION.md. The takeaways file is the run's answer.
7. Close. Copy this session's transcript from ~/.claude-alt/projects/ into this directory (cold start step 6).
   Write RUN_SUMMARY.md: the question, what was run, the measured numbers against what would refute the claim, the
   spend, and anything that halted. Then stop.

If any step halts or fails twice, write HALT.md with the reason, make sure no instance is running, and stop. A halt
or a refusal to answer is a valid outcome of this pipeline.
