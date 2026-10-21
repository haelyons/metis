# Execution directive for build (tag m4), regenerated on 2026-10-21 as the current truth after the report on launch 6 (addendum 16; ruled in GATE_COMMIT.md Addendum 17) (revised, addendum 17)

This is the measure run m4 of card seed:idea:1: one rented single-GPU box in us-east-1 with the filesystem `metis-env-us-east-1` attached, a
timer check, an anchor redocking of AAVR-PKD2 onto AAV2 against PDB 6IHB, then four inputs (AlphaFold-Multimer hours per run, MD ns/day,
auxiliary hours per pair, storage GiB) each read against the card's own band. Binding order: this note first, `frozen/ONBOX_CONTRACT.md`
second (item 21 says where this note wins), `out/design_record.json` third; where silent the design record binds as written, GUESS values
included. The build does not read GATE_COMMIT.md. Three standing changes of record (owner, 2026-10-21): (i) the Python environment is an
artifact built once on the Lambda filesystem and recorded by its lock hash; the on-box script activates it and verifies the hash, and installs
nothing; pins live in the environment record, not in the runner; (ii) implementer selftests are not required and not credited: a separate
claim-blind author writes `tests/tests_m4.py` from this note, hidden from the builder, and the runner executes it on the box before the physics as
a record; (iii) a stage failure on the box holds the box open (HOLD) once for a bounded fixer whose every change is committed to git on the box;
the fixer may touch environment and glue, never the measurement protocol or the record fields. Launches 1 and 2 ended in install failures; launch 6
reached the anchor's docking stage, where the runner's rank-table parser dropped every row of a table the tool had written correctly (a runner defect,
now item 26), and the box was held. Nothing from earlier launches is carried over except that diagnosis. The cap is USD 10 of box time for the whole
run (the environment build counts). **Read the closing section "Build 20: exactly these changes" first; it binds the edit, and the items below are
the requirements the files must meet.**

## Where to write

The run directory is `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure`. The build writes exactly `run_m4.py` and
`onbox_m4.sh` there, by absolute path, as in-place edits of the files now present, and writes nothing anywhere else. It reads the design record
at `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/design_record.json`, the conventions in `frozen/`
(provenance.py is the record writer; lambda_run.sh and remote_run.sh show what the box does; `ONBOX_CONTRACT.md` is the binding execution
contract) and this note. It does not read `tests/`, `out/`, `results_env/` or `.keys`. `lambda_run_m4.sh` and `remote_run_m4.sh` are the
operator's files. It uses no network. Its only local checks are `python3 -m py_compile run_m4.py` and `bash -n onbox_m4.sh`.

## Checklist of gate changes the build must carry (31 entries) (revised, addendum 16)

**REQUIRED FOR LAUNCH**

1. **REQUIRED FOR LAUNCH. Order on the box.** Activate the environment and verify its lock (item 3); capability check
   (item 4); tests stage (item 5); downloads and parameter extraction (item 9); R1 controls (60 s sleep, empty run, unit-and-scale record); anchor
   (serial, then parallel); per-pair docking and analysis (aux timing); AlphaFold timings (seed-major); MD timings; storage; endpoints. A guard
   before every stage and unit (item 24). (GATE_COMMIT answers 7, 14, Q5, Q8.)
2. **REQUIRED FOR LAUNCH. Files and payload (rule 5).** The build writes exactly `run_m4.py` and `onbox_m4.sh` in
   `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure` (absolute path) and reads the design record and `frozen/` only.
   Payload shipped to the box: `run_m4.py onbox_m4.sh remote_run_m4.sh frozen/provenance.py`, `tests/tests_m4.py` (the author's file, shipped by the
   operator) and `data/` recursively if it exists, all under `~/m4_run/`; the environment is the attached filesystem, not payload. Results under
   `~/m4_run/results_m4/out/`, which the launcher fetches. Nothing else is on the box.
3. **REQUIRED FOR LAUNCH. Environment of record.** `onbox_m4.sh` sets `VENV="${ENV_DIR:-/lambda/nfs/metis-env-us-east-1/m4}/venv"`,
   exits 2 if it is not an activatable CPython 3.10 venv, activates it and puts `${VENV}/bin` first on PATH before any stage. It computes the lock
   hash as sha256 of the stdout bytes of `"${VENV}/bin/python" -m pip freeze` (no flags) and compares it with `ENV_LOCK_SHA256` (forwarded by the launcher, 64 hex
   characters, no default; unset or malformed is exit 2). Mismatch is exit 2 with a void record. The check is one provenance.py record
   `env_check_tag-m4.json` (values: `expected_lock_sha256`, `observed_lock_sha256`, `venv_path`, `python_version`, `equal`). The runner pins nothing and
   reads no `pins.txt`. After a fixer restart (item 6) the lock is recomputed and the records carry the label "environment changed by the fixer on
   the box; lock <hash>" when it differs, except that a second mismatch at this very check is final.
4. **REQUIRED FOR LAUNCH. Capability check; no installs.** The script and the runner run no `pip`, `apt-get` or `sudo` and
   build no venv. After the lock check, one capability check inside the setup ceiling (item 8), reporting every problem in one pass: import of the
   AlphaFold-Multimer stack and JAX with a GPU device listed; `colabfold_batch --help`; the docking code's entry point `--help` and its
   conformation-generating script's `--help`; OpenMM imported with `Platform.getPlatformByName("CUDA")` succeeding; each tool resolved by
   `shutil.which` against the venv PATH with its absolute path recorded. Any problem is exit 2 with a void record before any GPU stage (item 7), and
   is eligible for the hold (item 6). No trial docking.
5. **REQUIRED FOR LAUNCH. Tests stage.** The runner runs `${VENV}/bin/python tests/tests_m4.py --results results_m4/out` through its
   tool runner (own process group, ceiling 300 s, output under `tool_logs/`) after items 3 and 4 and before item 9's downloads. Exit 0 passes; non-zero,
   timeout or a missing file is exit 2, `void_by_failure:tests`, eligible for the hold; there is no skip and no retry inside the stage. The record is
   `tests_tag-m4.json` (values: `exit_code`, `seconds`, `tests_file_sha256`, `stdout_tail` as the last 20 lines, `tests_passed` and `tests_total` from a
   line `tests: N of M passed` in the output, else null with a `null_reasons` entry). The runner neither imports nor interprets the tests. The tests are
   written by the claim-blind author from this note, `ONBOX_CONTRACT.md`, the design record and QUESTION.md; implementer selftests are neither required nor credited.
6. **REQUIRED FOR LAUNCH. Hold-open, the fixer's scope and the restart (revised, addendum 17).** Eligible: any exit-2 stage failure of the table of item 7 except the 60 s
   sleep check. After the failed attempt's void records and `RUN_DONE` are written, the shell writes `results_m4/out/HOLD` (stage, kind, exit code, UTC
   time, `hold_seconds`) and waits as item 27 says, at most `HOLD_SECONDS` (forwarded; value of record 2400 (revised, addendum 17); any value above 2,400 is treated as 2,400 with the label
   "HOLD_SECONDS capped at 2400"; unset means 0, no hold, label "HOLD_SECONDS not forwarded; no hold") for `results_m4/out/RESUME`;
   hold time counts in elapsed time and never in a stage ceiling. At start the shell records the sha256 of `run_m4.py` and
   `tests/tests_m4.py`. The fixer may change environment and glue, each change committed to git on the box and fetched as `results_m4/out/changes.log`;
   it may not change the measurement protocol or the record fields, so `run_m4.py` and `tests/tests_m4.py` stay byte-identical: before a restart the shell
   compares the hashes, and a change (or a verifier finding of out of scope) is a halt to the gate: no restart, exit 2, label `fixer_out_of_scope`. On RESUME
   with at least 1,500 s of REMOTE_TIMEOUT left the shell moves `results_m4/out` to `results_m4/held_attempt_1/` and restarts the runner once, with the files as they are on the box at RESUME time, from its first
   stage (item 1's order, every stage, never from a mid-run state, and a RESUME never ends the run in place of the restart) under the same T0 and caps; a download whose
   file exists with the recorded sha256 may be reused, recorded as `reused: true` with the hash; the restarted attempt's stage allowances follow item 8 from the elapsed
   time then, so later stages may be guard-stopped (exit 3), stated in `m4_summary.json`; its records are the run's records and `m4_summary.json` carries
   `held_attempts: 1` and the change log's sha256. One hold per launch: a second eligible failure is exit 2, final. Expiry or less than 1,500 s left ends the launch with
   the first attempt's records and `RUN_DONE` extended with `hold: expired` or `hold: no time to resume`.
7. **REQUIRED FOR LAUNCH. Broken infrastructure (rule 4).** Ubuntu 22.04, CUDA 12.8, driver 570, python 3.10 and torch 2.7 are preinstalled;
   everything else is in the environment of record. Every outcome maps to exactly one row, and the table is the only source of exit code, `run_valid` and
   the `RUN_DONE` per-input status:

   | Event | Exit | run_valid | per-input status |
   |---|---|---|---|
   | environment missing or lock mismatch, capability check problem, tests stage failure, download failure, setup total over its ceiling, tool start failure, real tool failure (non-zero exit, crash, missing output), no parsable ranked pose, unparsable rank table, sleep check failed, shell abort before the runner starts | 2 | false | `void_by_failure:<kind>` for every input not decided before it |
   | anchor compared and tolerance missed | 4 | false | `void_by_anchor_miss` for C1 to C4 |
   | guard refusal, stage ceiling, tool-call timeout, outer timeout (124, or 137 at the deadline) left at least one input unmeasured | 3 | as it was | `unmeasured_by_stop:<kind>` for those inputs, `decided` or `void_by_rule:<reason>` for the others |
   | every input decided, or void by rule with no stop (not an A100, zero spread, marginal) | 0 | true | `decided` or `void_by_rule:<reason>` |

   Never patch around and never substitute a tool or source: after a failing tool call no second tool or source is tried (a fixer's change under item 6 is not
   the build's patching). Each failure row writes a void record, the summary and `RUN_DONE` before exit. The shell sets its exit trap before the venv step.
   Only the `|| RC=$?` form runs `run_m4.py`, its `--finalize` form and the outer `timeout` under `set -e`; the trap acts only while `FINISHED=0`.
8. **REQUIRED FOR LAUNCH. Caps, time and ceilings (rules 1, 2).** `onbox_m4.sh` reads `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD` and
   `REMOTE_TIMEOUT` from its environment, with no default above `BUDGET_LEFT_USD=5` or `REMOTE_TIMEOUT=7200`, and stops cleanly, writing a void record for
   unfinished work, before projected spend reaches `BUDGET_LEFT_USD` or elapsed time reaches `REMOTE_TIMEOUT`. Hard cap USD 10 for the run;
   `BUDGET_LEFT_USD` per launch is the lesser of 5 and what remains; every launch uses `REMOTE_TIMEOUT=7200` exactly. It records the `REMOTE_TIMEOUT` seen in
   `env.txt` and `m4_summary.json` (unset: 7200 and the label "REMOTE_TIMEOUT not forwarded; default 7200 used"). T0 is the start of the parent
   `remote_run_m4.sh` (`ps -o etimes= -p $PPID`) plus 30 s; unreadable takes 300 s and the label "bootstrap time assumed 300 s". Ceilings in seconds:
   setup (item 3, 4 and 9 work, a running total) 1,500; tests 300; controls and anchor 700; per-pair docking and analysis 600 (at most 250 per pair);
   AlphaFold 2,000; MD 1,600 (at most 600 per complex); endpoints 100; margin 400; sum 1,500 + 300 + 700 + 600 + 2,000 + 1,600 + 100 + 400 = 7,200.
   `allowance(stage) = max(0, min(ceiling(stage), REMOTE_TIMEOUT - elapsed_since_T0 - 400 - 100))`; a stage whose allowance is below its first unit's estimate
   (item 24) is not started. Setup over 1,500 or any call over its limit is exit 2. Spend: `estimated_spend_usd` = seconds since T0 x `PRICE_USD_PER_HOUR` / 3,600
   (pre-T0 seconds reported beside it, not added).
9. **REQUIRED FOR LAUNCH. Downloads, nothing interactive, command (rule 10).** No prompts anywhere. No `sudo`. Downloads only from
   the sources the design names: the PDB entry 6IHB from RCSB and the AlphaFold parameter archive from the AlphaFold project's own storage address; URL and
   sha256 recorded for each; no pip or apt download exists. The archive's sha256 is verified and recorded, it is extracted into `<data>/params` (the `--data`
   directory colabfold is given), the completion marker(s) are the names read from the installed colabfold's own download module (none hard-coded; "no marker
   named" recorded if none), and the multimer parameter files for the 5 models are verified present: missing is exit 2. No network access in any timed call;
   a timed call whose log shows a download or extraction gets `download_in_timed_call: true`, is not counted and C1 is VOID "download inside timed call". A failed
   download stops the run (item 7) with no second source. The `onbox_command` the build returns is one line: `bash remote_run_m4.sh bash onbox_m4.sh`.
10. **REQUIRED FOR LAUNCH. Secrets (rule 8).** Nothing reads `.keys`; nothing prints its environment (no `env`, `printenv` or `set` dump; `env.txt` lists only
    named non-secret variables); `HF_TOKEN` is used by downloads only: `onbox_m4.sh` unsets `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` after the downloads and
    every tool child gets a copied environment with both removed.
11. **REQUIRED FOR LAUNCH. Scope and gate scope (rule 3; answer 1).** Measure the inputs on the card's own protocol; no production phase, no 54-run pilot, no
    216-run grid; anchor first; a missed anchor voids the inputs (`run_valid` false propagates to every later record). The card's gate (`af2_h_per_run <= 1`) is
    applied to C1 only: C1 values carry `gate_value` 1, `gate_pass` and the card's fallback text in `gate_else` ("take the docking-plus-MD fallback line with one
    AlphaFold-Multimer seed per pair, or move the grid to 12 pairs"); C2 and C3 carry `gate: "not applicable: the card's gate is on af2_h_per_run"`. The C1 decision
    is the band alone; the run does not branch on the gate. `gate_pass` is computed only when C1 holds a valid measurement (PASS, FAIL or marginal VOID); for any other
    VOID it is null with `gate: "not evaluated: C1 VOID (<reason>)"`.
12. **REQUIRED FOR LAUNCH. Pairs, seeds, AlphaFold (answers 2, 3).** 3 stand-in pairs built from chains of the 6IHB entry, one per capsid slot, each a hetero-multimer of
    750 to 1,000 residues (more than one copy of a capsid chain allowed to reach the range); assert each length in range, the three sequences pairwise different,
    the lengths pairwise at least 20 residues apart, one capsid-role and one receptor-role chain set per pair; a failure is exit 2 naming the assertion, no clamp.
    Evidence `results_m4/out/pairs_tag-m4.json` (chain ids and roles, sequences, lengths, sha256 of each FASTA and PDB) and the three FASTA copies, cited in each C
    record's `inputs`. AlphaFold: one GPU; seeds 0, 1, 2 seed-major; 5 models; exactly 20 recycles, early stopping off; single-sequence input only, no sequence database, no
    remote alignment service. Measured = mean wall-clock hours of the whole prediction call per run, first-model compile included (the decision value); rows also carry the
    compile-excluded figure when the log gives per-model times. Minimums: C1 at least 3 completed runs covering all 3 pairs; C2 at least 2 complexes (n recorded); C3 at least 2
    pairs; C4 at least one run of each artifact type; below a minimum the record is VOID and the raw rows stay.
13. **REQUIRED FOR LAUNCH. Docking and auxiliary hours (answers 4, 5) (revised, addendum 16).** One pip-installed docking code from the environment (name and version read from installed
    metadata, never a constant), same swarm count and parameters for the anchor and every pair, not restrained toward the 6IHB interface, recorded in the anchor record
    (`values.docking_parameters`, `values.docking_order`); order simulate, conformation generation, `lgd_rank.py` unless `frozen/ONBOX_CONTRACT.md` states another, then that
    order. The top pose is the first row of the tool's own rank list by its score, read under item 26; a missing named pose file or an unparsable rank table is exit 2 with the raw table kept;
    never `sorted(glob)[0]`. aux_h_per_pair = wall-clock hours per pair of docking, interface analysis (contacts at 4.5 A, interface residues, distance to the nearest
    threefold axis, site class) and writing the call-table row; setup, downloads and the tests stage excluded; mean over the finished pairs; a pair reaching 250 s keeps a row
    with `truncated: true`, is not counted, and the loop continues with the next pair; C3 decided if at least 2 pairs finished, else VOID.
14. **REQUIRED FOR LAUNCH. MD protocol (answers 5, 10).** One docked complex per pair: the pair's capsid-role chains merged with the top-ranked docking pose of the receptor, one
    structure, chain roles preserved (assert both roles present and a nonzero capsid heavy-atom count before solvation, else exit 2); explicit solvent with water padding
    chosen so the built system has 120,000 to 180,000 atoms (one rebuild inside the complex's 600 s; else C2 VOID with the atom count kept, the range never widened);
    minimise, short equilibration, then a 0.5 ns production segment; one velocity seed (0). The worker writes a DCD trajectory with `DCDReporter` every 5,000 steps
    (`frame_interval_ps` 10 recorded) and a StateDataReporter file, copied to `results_m4/out/` and parsed for the engine ns/day (a file with no rate line gives
    `engine_ns_per_day: null` and the label "engine rate line missing"). The decision value is the median over complexes of production steps x timestep over the production
    wall-clock; if it and the engine rate differ by more than 5 percent every ns/day carries "engine rate and wall-clock disagree" and both are reported.
15. **REQUIRED FOR LAUNCH. Storage (answer 4).** n_storage_gib = apparent bytes written for one grid run (AlphaFold outputs of one run; the whole per-pair docking output tree with
    setup files, swarm directories, rank tables and every pose; the MD trajectory plus every log of the segment: reporter file, stdout and stderr logs, the worker's JSON
    files), intermediates kept, x 216, / 2^30, the decision value. `system.xml`, `solvated.pdb` and checkpoints are `md_setup_bytes`, not in the value. The record also
    carries the 432-run figure, the intermediates-deleted figure and MD bytes per ns (MD bytes over 0.5) as information.
16. **REQUIRED FOR LAUNCH. Controls first (answer 7).** After items 3 to 5 and 9: the planted 60 s sleep through the same timer (error at most 5 percent, else `run_valid` false, exit 2,
    nothing else runs); the empty-input run, which times the harness itself (the same timer, work-directory creation and record path as a real call, around a no-op command, no
    AlphaFold, JAX, TensorFlow or docking import) and measures the bytes in the directory it created (under 2 s and under 1 MiB, else the excess, only that harness overhead, is
    subtracted from later values and labelled "setup overhead subtracted"); one unit-and-scale record, written before any band comparison, `values.kind` "worked_examples", whose
    `values.raw_values_in` names the rows files holding the raw AlphaFold seconds, the MD engine rate lines beside the wall-clock ns/day, and the raw bytes per artifact.
17. **REQUIRED FOR LAUNCH. Anchor (answer 8).** Contact overlap = fraction of 6IHB interface residue-residue contacts (heavy-atom pair at most 4.5 A) the pose also makes, keyed by chain
    role through one chain-mapping function for reference and pose (the receptor chain id "A", "B" or "C" in the file gives the same overlap). Interface backbone RMSD is over N, CA, C, O
    of the receptor residues forming the reference interface (any heavy atom within 4.5 A of the capsid in 6IHB), in the capsid frame, no superposition; the serial-versus-parallel
    top-pose RMSD is over the whole receptor chain and labelled so. Pass if overlap >= 0.50 or interface RMSD <= 5.0 A, and serial-versus-parallel RMSD <= 2.0 A with identical bind/no-bind
    calls. Serial, then parallel on the same box, seed 0. Three routes, no overlap: a docking call over its allowance is a ceiling stop (exit 3, anchor undecided, C1 to C4 VOID
    "unmeasured, not holding"); a docking tool that fails or leaves no parsable ranked pose is exit 2; exit 4 only when a pose was obtained and compared and the tolerance missed (C1 to
    C4 VOID, `run_valid` false). The anchor record carries `independent_code: "not run: single docking code"`; the second independent code is not run.
18. **REQUIRED FOR LAUNCH. Marginal rule, non-A100, variance labels (answers 5, 13).** A value within 10 percent of a band edge (`edge x 0.9` to `edge x 1.1`) is decision VOID with
    `marginal: true`, the raw value kept in `measured`. If the GPU is not an A100, C1 and C2 are VOID with the raw number kept and the label "not an A100"; C3 and C4 are still
    decided. Zero spread across the seeds of a pair makes C1 VOID "zero spread across seeds: wrong variance source" while other inputs stand; relative SD over 50 percent on any
    pair adds the label "seed spread high; mean is uncertain" and nothing else; nothing is relaunched for spread.
19. **REQUIRED FOR LAUNCH. Records (rule 6).** For each input C1 to C4 one provenance.py record `results_m4/out/endpoint-C<i>_tag-m4.json`; its `values` carries
    `measured` (a number in the card's unit: C1 h per run, C2 ns/day, C3 h per pair, C4 GiB), `unit`, `card_value` (0.5, 129, 1, 200) and `band` ([0.2, 1.25], [51.6, 322.5],
    [0.3333, 3], [66.67, 600]); its `decision` is PASS, FAIL or VOID against that band; `run_valid` in every record. An anchor record `endpoint-anchor_tag-m4.json` (values `measured`,
    `published`, `tolerance`). `RUN_VALID.json`; `m4_summary.json`; raw rows as JSON lines (`rows_<arm>_tag-m4.jsonl`: one line per AlphaFold run with pair, seed, wall-clock,
    per-model times, `incomplete`, `download_in_timed_call`; per docking; per MD segment with complex, atoms, steps, wall-clock, engine rate, `frame_interval_ps`; per storage
    measurement). Also `env_check_tag-m4.json` and `tests_tag-m4.json` (items 3, 5) and one record each for the sleep control, the empty-run control and the unit-and-scale record.
    Records written before the failing decision carry `run_valid` true; the run is marked invalid before the failing record is written, so `RUN_VALID.json`, the summary and every
    later record agree. Every record's `inputs` lists its rows file, the pair evidence file where it applies, the download record with sha256s, and the lock hash. A value that cannot be had is
    null with a non-empty `null_reasons` entry.
20. **REQUIRED FOR LAUNCH. Labels (rule 9).** A constant `REQUIRED_LABEL_KEYS` maps each record kind (anchor, C1 to C4, sleep, empty-run, unit-and-scale, env_check,
    tests) to the keys its `values.machine` (and, for the anchor and C kinds, `values.engine`) must hold; no key is omitted. Together they cover: instance type, GPU name, driver, CUDA
    runtime version (the driver's "CUDA Version" from the nvidia-smi header, parsed, plus the JAX CUDA plugin version), engine versions and build flags (AlphaFold implementation and its
    parameter archive sha256, JAX, jaxlib and plugin versions with wheel tags, docking code and version, MD engine, version, precision and platform), start and end wall-clock (UTC, of
    the stage that produced the value), price per hour, and the observed and expected lock sha256, the venv path, `environment_changed_by_fixer` and `held_attempts`.
    Every version comes from the installed distributions' metadata read on the box, never from a constant default. Control kinds need only the machine-level keys. Every C record also
    carries "stand-in pairs built from 6IHB chains, not the card's pairs", "one GPU; one box; 3 pairs; no multi-GPU scaling" and `n`; C1 "no-MSA: alignment search time excluded;
    understates the card's setting"; C2 the atom count of each complex, engine precision, platform and version, `timestep_fs`, `production_ns`, per-complex wall-clock and engine rates; C3
    "producer's reading of aux hours"; C4 "linear in runs; intermediates kept; MD length 0.5 ns". Every record written after a guard, ceiling or timeout stop carries "incomplete
    run: unmeasured inputs are VOID, not holding".
21. **REQUIRED FOR LAUNCH. Contract precedence.** Where `frozen/ONBOX_CONTRACT.md` differs from items 7, 16, 24 and 23, this note wins by a ruling of
    record: exit codes are 0, 2, 3 and 4 (no exit 5); the runner and the shell write `RUN_DONE`; the guard uses the estimate floors of item 24 and no timed dry run on the real input; the
    per-run environment file is `env.txt` and no `env_<tag>.json` is required; the contract's install stage is replaced by items 3, 4, 5 and 9, and its selftest contract is withdrawn
    (item 5). Every other contract item (stage order, guards, record fields, failure checks) stays binding.
22. **REQUIRED FOR LAUNCH. Stops and guard paths (answers B1 to B3, E8).** A stop is exactly one of: guard refusal to start a stage or unit, a stage ceiling, a tool call exceeding its allowance, the
    outer timeout; a failure (exit 2) and an anchor miss (exit 4) are not stops. On a stop: the stopped stage is not in `stages_done` even if it returned normally; its unfinished inputs are
    `unmeasured_by_stop:<kind>` with VOID records carrying the full incomplete-run label while every decided input keeps its decision; `run_valid` is not changed; a timed-out tool's row is kept
    with `incomplete: true` and is not counted; later stages whose guard allows still start and endpoints always run; the exit is 3 if any input is `unmeasured_by_stop` at the end, else 0.
    `run_valid` is set false only for exit 2 and 4. An outer timeout (124, or 137 with elapsed at least the outer deadline minus 5 s) kills the recorded process groups, runs
    `run_m4.py --finalize` and exits 3; 137 earlier is exit 2.
23. **REQUIRED FOR LAUNCH. Summary, `RUN_DONE`, shell voids, finalize (answers E9, F2, G4, H5).** `m4_summary.json` is written without `sort_keys`, first key `what_this_run_decides` (the
    stand-in protocol only), then the run_valid and exit fields, every record, the gate result and fallback text (item 11), `unmeasured_inputs`, `held_attempts`, the seed-spread and
    incomplete-run labels; it carries no decision of its own. `RUN_DONE` carries the exit code and per input C1 to C4 exactly one status of item 7. The shell's minimal void (runner never
    started or died) writes `env.txt`, the summary, `endpoint-anchor_tag-m4.json` (VOID, `measured` null, `null_reasons.measured` "anchor stage not reached" if not run), C1 to C4 VOID
    records with the provenance.py keys, `RUN_VALID.json` and `RUN_DONE`; it never rewrites a record already decided on disk (PASS, FAIL, or VOID with `marginal` or a rule reason) and
    shows it `decided` or `void_by_rule`. `--finalize` rebuilds status from `results_m4/out/` (a missing record or one carrying "unmeasured, not holding" is
    `unmeasured_by_stop:outer_timeout`; a FAIL anchor gives exit 4; `run_valid` false elsewhere without FAIL gives exit 2; otherwise 3 if any unmeasured, else 0) and writes only missing records.
24. **REQUIRED FOR LAUNCH. Tools, process groups, caches, guard estimates (answers E1, E16, E20, F1).** Tools resolve through the venv: `child_env` puts the venv bin first (from
    `sys.executable`'s directory) and tools are called by absolute venv path where possible. Every tool call (colabfold, the docking code, the OpenMM worker, the tests) runs in its own process
    group, killed on timeout; each pgid is recorded with its leader's start time and command and signalled only if both still match; the inner tool timeout is at least 100 s shorter than the
    outer kill. `PIP_CACHE_DIR`-style cache variables, `XDG_CACHE_HOME`, `MPLCONFIGDIR`, `TMPDIR` and any JAX or colabfold cache variable the build sets point under `~/m4_run/`. Every
    `guard_before_stage` call and every unit passes `estimated_s`: the mean of finished units of that kind, else the floor (anchor serial or parallel 60 s, docking pair 60 s, AlphaFold run
    120 s, MD complex 150 s, storage 20 s, endpoints 30 s, tests 60 s); a unit whose estimate exceeds its allowance is not started and is a guard stop.
25. **REQUIRED FOR LAUNCH. Worked values for the test author (testable without a model) (revised, addendum 16).** Anchor: (overlap 0.50, RMSD 9.0) passes; (0.49, 5.0) passes; (0.49, 5.01)
    fails; serial-versus-parallel 2.0 with equal calls passes, 2.01 fails, 0.0 with different calls fails; 3 of 6 reference contacts gives 0.5; a pose shifted 5.0 A along x on the interface atoms
    gives RMSD 5.0000; a pose moving only non-interface receptor atoms by 20 A gives interface RMSD 0.0000 and a whole-chain RMSD above 0. C1: 1,800 s per run gives 0.5 h; means 0.5 PASS, 1.5 FAIL,
    0.1 FAIL, 1.2 VOID (marginal, `gate_pass` false), 0.21 VOID, 1.1 PASS with `gate_pass` false and the fallback text, 0.9 PASS with `gate_pass` true; 2 runs VOID with `gate_pass` null; 3 runs
    missing one pair VOID. C2: 250,000 steps x 2 fs in 335 s gives 128.96 ns/day; median of (100, 129, 500) is 129 PASS; 40 FAIL; 400 FAIL; 56 VOID; 60 PASS; 330 VOID; atom counts 119,999 and 180,001
    VOID, 150,000 passes; a GPU name other than A100 makes C1 and C2 VOID. C3: three pair wall-clocks of 3,600 s give 1.0 h PASS; 0.2 FAIL; 4.0 FAIL; 0.3333 VOID; 3.2 VOID; 0.5 PASS; 2.5 PASS; 7,200 s of
    setup plus 1,800 s of docking gives 0.5 h. C4: 1,073,741,824 bytes per run gives 216.0 GiB PASS (432-run figure 432.0); 0.1 gives 21.6 FAIL; 4.0 gives 864.0 FAIL; 2.9 gives 626.4 VOID; 0.35 gives 75.6
    PASS; files of 1,000 and 24 bytes sum to 1,024; an `md_` directory with a 1,000-byte trajectory, a 100-byte reporter file, a 24-byte log, a 5,000-byte `system.xml` and a 7,000-byte `solvated.pdb`
    gives MD bytes 1,124 and `md_setup_bytes` 12,000. Harness: 62.9 s for the 60 s sleep passes, 63.1 s fails (`run_valid` false, exit 2); timings (1,800, 1,830, 1,790) pass the spread check, (1,800,
    1,800, 1,800) fails; relative SD 0.6 gives the spread label only; empty run 0.5 s and 100 KiB pass, 5 s or 2 MiB trigger the subtraction label. Cost: 3,600 s at 1.99 gives 1.99, 7,200 s gives 3.98;
    with price 1.99, budget 5, timeout 7,200 the guard stops at the time cap (5 / 1.99 h = 9,045 s); with price 2.50 both caps coincide at 7,200 s; with 3.00 the dollar cap stops at 6,000 s; 3,600 s since
    T0 with 300 s pre-T0 reports 1.99. Allowance with REMOTE_TIMEOUT 7,200: setup 1,500 at elapsed 0, AlphaFold 700 at elapsed 6,000, 0 at elapsed 6,800 (clamped, stage not started). Lock: equal
    hashes pass, any differing character fails, an unset expected hash fails. Hold: a planted failing stage writes `HOLD` after its void records; `RESUME` with 1,500 s left restarts once from the first
    stage; a changed `run_m4.py` hash gives `fixer_out_of_scope` and no restart; a planted hold of 30 s with a `HUP` at 10 s writes `HOLD_END` naming the signal and 10 s. Rank table (planted shapes, not the
    tool's format of record): a header of 9 tokens `#Coordinates RecID LigID Luciferin Neighbor's number Vision Range Scoring` over two rows of 7 fields gives 2 rows, mapping `positional`, the last
    column as score, top row the first row written (score column monotone), and zero rows dropped; a header `Swarm Glowworm Scoring` over rows of 3 fields gives mapping `by_name` and the pose path
    `swarm_<Swarm>/lightdock_<Glowworm>.pdb`; a header with no data line is a parse error whose text carries the count of lines after the header; data rows of 6 and 7 fields mixed are a parse error naming both
    counts; a score column that rises then falls is a parse error; a table whose top row names no swarm, conformation or file is exit 2, never a glob; every parse error text contains the first five raw lines.
26. **REQUIRED FOR LAUNCH. Rank table: read as written, never drop a row, keep the evidence (new, addendum 16).** The cause of launch 6's failure: the parser skipped every data row whose field count differed
    from its header's, so a table with rows read "a header but no rows". The rule: (a) the first non-empty line is the header; one leading `#` and surrounding blanks are removed from it; later lines starting `#` are comments;
    blank lines are ignored. (b) A data row is a line of at least two fields whose last field parses as a float; a row is never dropped for its field count. If every data row has the header's token count, fields are
    named by the header (`by_name`); if all data rows share one count k different from the header's m, fields are named `col0` to `col{k-1}`, the last column is the score and the header's last token must be
    `scoring`, `score` or `energy` (any case), else a parse error (`positional`); if data row counts differ, a parse error naming the counts. (c) A header with no data line is a parse error that states the number of lines
    after the header. (d) The top row is the lowest `rank` when a rank column is named, else the first row as the tool wrote it, provided the score column is monotone (non-increasing or non-decreasing) down the file, else a
    parse error. (e) The pose comes from the top row through its named pose, swarm and conformation fields as now; a top row that names none is exit 2, never `sorted(glob)[0]`. (f) Every parse error and every pose failure of
    `run_docking` carries the field counts and the first five raw lines (each as `repr`), and before raising the runner writes `results_m4/out/rank_table_diagnostic_<name>_tag-m4.txt`: the first 8 raw lines (each as `repr`), the
    number of data lines and their field counts, and the names (not contents) of the entries of `work` and of its first `swarm_*` directory, depth 1. The kept copy of the raw table stays. (g) The anchor record's
    `values.docking_parameters` carries `rank_table_columns` (the header tokens, the row field count, the mapping used).
27. **REQUIRED FOR LAUNCH. The hold wait is measured, robust and explained (new, addendum 16).** In `onbox_m4.sh` the wait for `RESUME` is measured with `date +%s` against the hold's start (not by a count of sleeps),
    polls every 10 s, writes a heartbeat line to the log every 60 s (seconds waited of the forwarded `HOLD_SECONDS`), and ends only on `RESUME`, on the elapsed time reaching `HOLD_SECONDS`, or on a signal: while holding the shell traps
    `HUP`, `TERM` and `INT`, writes `results_m4/out/HOLD_END` (cause `resume`, `expired` or the signal name; seconds waited) and the log line, then ends as an expiry does (`hold: expired` on `RUN_DONE`, with the cause named). Launch 6's
    hold ended after about 13 minutes of 2,400 s with no record of why; after this item a hold that ends early says why. No other exit path from the wait exists.

**REPORTING ONLY**

28. **REPORTING ONLY. Change log and hold cost.** The fetched `changes.log`, the hold's wall-clock and its cost at `PRICE_USD_PER_HOUR` are reported in `m4_summary.json` and RUN.md; the gate reads them before any
    later launch. Not blocking in review.
29. **REPORTING ONLY. The verifier's six advisory findings, and the CUDA compiler wheel against the runtime libraries.** Advisory and not ruled one by one; the compiler-wheel question is decided by the capability
    check of item 4 on the box. A review may list further such findings; none is blocking.
30. **REPORTING ONLY. Operator's frozen bootstrap.** Whatever `frozen/remote_run.sh` installs or upgrades before `onbox_m4.sh` starts is the operator's and is not recorded by the build; the gap between the box's
    preinstalled packages and the venv is not tested. Advisory only.
31. **REPORTING ONLY. Spend record.** `m4_summary.json` carries `estimated_spend_usd`, the pre-T0 seconds and the instance type and price; the operator's figure (provisioning to termination, hold included) governs the
    cap.

## Box

- Instance: `gpu_1x_a100_sxm4` (A100 SXM4 40 GB, USD 1.99/h) in us-east-1 with the filesystem `metis-env-us-east-1` attached; else the cheapest single GPU with capacity in us-east-1 at no more than USD 2.50/h; the
  operator records which. Launches 1, 2 and 6 ran on `gpu_1x_a100_sxm4` (A100-SXM4-40GB, driver 570.148.08, CUDA 12.8, python 3.10.12).
- Launcher: the operator's `lambda_run_m4.sh` (from `frozen/lambda_run.sh` at the header's declared points only): remote dir `m4_run/`; payload as item 2; forwarded env `PRICE_USD_PER_HOUR BUDGET_LEFT_USD REMOTE_TIMEOUT
  INSTANCE_TYPE ENV_LOCK_SHA256 HOLD_SECONDS` and optionally `ENV_DIR`; fetch all of `m4_run/results_m4/out/` (rank tables, poses, diagnostics, `HOLD_END`, `tool_logs/`), `held_attempt_1/` if present and `changes.log`. `remote_run_m4.sh` is
  `frozen/remote_run.sh` with only its `cd` line changed to `~/m4_run`.
- Caps (revised, addendum 16): `REMOTE_TIMEOUT=7200` exactly; spend of record USD 4.18 (3.48 before launch 6, about 0.70 for it), remaining 5.82; `BUDGET_LEFT_USD` = the lesser of 5 and the remaining cap = 5; `HOLD_SECONDS=2400` (revised, addendum 17); no launch starts
  with less than 7,800 s x price / 3,600 remaining (USD 4.311 at 1.99, 5.417 at 2.50). A launch at its caps is 4.311; after the next launch at its caps 1.51 remains, so no launch follows it.
- Payload layout on the box: `~/m4_run/run_m4.py`, `~/m4_run/onbox_m4.sh`, `~/m4_run/frozen/provenance.py`, `~/m4_run/tests/tests_m4.py`, `~/m4_run/data/...` if shipped. Results under `~/m4_run/results_m4/out/`.

## Local selftest

None. `python3 run_m4.py --selftest` is removed; implementer selftests are neither required nor credited and no launch condition counts them. The build's only local checks are `python3 -m py_compile run_m4.py` and
`bash -n onbox_m4.sh`. The measurement logic is tested by `tests/tests_m4.py`, written by the claim-blind author from this note and run on the box by the runner (item 5); item 25's rank-table cases are added to it by the author.

## What the runner writes (`results_m4/out/`) (revised, addendum 16)

- `endpoint-anchor_tag-m4.json` and `endpoint-C1_tag-m4.json` to `endpoint-C4_tag-m4.json`, `env_check_tag-m4.json`, `tests_tag-m4.json`, and one provenance.py record for each control (60 s sleep, empty run, unit-and-scale), each with
  `cell`, `inputs` with hashes, `metric`, `values`, `threshold`, `decision_rule` written before values, `decision`, `run_valid`; the labels of item 20; the anchor's `docking_parameters` (with `rank_table_columns`) and `docking_order`. On an exit-2 or
  exit-3 end the anchor record is written even when the anchor was not reached.
- Raw rows `rows_<arm>_tag-m4.jsonl` (item 19); `pairs_tag-m4.json` and the three FASTA files; the MD reporter files and the DCD size record; the raw docking rank tables (`rank_table_<name>_tag-m4.list`), the kept poses, and
  `rank_table_diagnostic_<name>_tag-m4.txt` on a rank-table or pose failure (item 26).
- `RUN_VALID.json`; `env.txt` (named non-secret variables only, including the `REMOTE_TIMEOUT` seen and the pre-T0 seconds); `m4_summary.json`; download, capability-check and tool logs (including the tests' output); the download record
  with URLs and sha256; the colabfold marker record; `RUN_DONE` with the exit code and the per-input status of item 7; `HOLD` while held and `HOLD_END` when a hold ends (item 27); `changes.log` and `results_m4/held_attempt_1/` after a hold.

## Build 20: exactly these changes (new, addendum 16; ruled addendum 17; binds first; replaces the closing section "Build 17: exactly these changes", which is satisfied and removed)

The files edited are the ones now in the run directory. Every other line stays as it is; nothing is refactored, renamed or reordered. A changed line outside V1 to V4 is a blocking finding in review.

**V1. Rank table parse (items 13, 26 a to e).** In `run_m4.py`, `parse_rank_table` and `top_ranked_row` (and the lines of `run_docking` that call them) read the table under item 26 a to d: no row is dropped for its field count; header-with-rows
mismatch is read positionally or is a named parse error; the empty-table error states the lines after the header; the top row of a score-only table is the first row written and the score column must be monotone. `pose_path_from_row` keeps its named keys
and never falls back to a glob.

**V2. Evidence on failure (item 26 f, g).** Every parse error and pose failure of `run_docking` carries the field counts and the first five raw lines; the runner writes `rank_table_diagnostic_<name>_tag-m4.txt` before raising; the anchor record's
`values.docking_parameters` carries `rank_table_columns`.

**V3. The hold wait (item 27).** In `onbox_m4.sh`, the wait loop of `hold_open` is measured with `date +%s`, prints the 60 s heartbeat, traps `HUP`, `TERM` and `INT` while holding, writes `HOLD_END`, and applies the 2,400 s cap with its label
(item 6). No other exit path leaves the wait.

**V4. The restart (item 6).** In `onbox_m4.sh`, after `RESUME` and the hash and time checks, the runner restarts once from its first stage under the same T0 and caps; a download file with the recorded sha256 may be reused and is recorded
`reused: true` with its hash. A RESUME never ends the launch in place of the restart.

**The return** states the real line counts of both files, their sha256 values, that `py_compile` and `bash -n` pass, the exact lines changed by V1 to V4 (before and after, as line ranges), and `onbox_command` equal to
`bash remote_run_m4.sh bash onbox_m4.sh`. It never says "STOPPED", "NOT BUILT" or "NOT ISSUED".
