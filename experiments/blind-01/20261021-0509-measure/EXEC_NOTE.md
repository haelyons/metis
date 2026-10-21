# Execution directive for build (tag m4), revised on 2026-10-21 after the reviews of build 2 (addendum 3) and build 6 (addendum 5)

Binding order: GATE_COMMIT.md answers first (the original answers 1 to 14, then addendum 3 answers B1 to B15, then addendum 5
answers E1 to E28), this note second, `out/design_record.json` third; `frozen/ONBOX_CONTRACT.md` binds under rule 5 and nothing
here loosens it. Where silent, the design record binds as written, GUESS values included. The build does not read GATE_COMMIT.md
itself; the checklist below carries every gate change the build must implement. This is the measure run m4 of card
seed:idea:1: one rented single-GPU box, a timer check, an anchor redocking of AAVR-PKD2 onto AAV2 against PDB 6IHB, then four
inputs (AlphaFold-Multimer hours per run, MD ns/day, auxiliary hours per pair, storage GiB) each read against the card's own
band. The cap is USD 10 for the whole run, at most two launches. Nothing here has run yet. Items marked `(revised, addendum 3)`
changed build 2's behaviour and items marked `(revised, addendum 5)` change build 6's; items 38 to 47 are new in addendum 5;
items 31 to 37 came with addendum 3; the rest stand.

## Where to write

The run directory is `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure`. Write exactly `run_m4.py` and
`onbox_m4.sh` there, by absolute path. Write nothing anywhere else. Read the design record at
`/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/design_record.json` and the conventions in `frozen/`
(provenance.py is the record writer; lambda_run.sh and remote_run.sh show what the box does; `ONBOX_CONTRACT.md` is the binding
execution contract). `lambda_run_m4.sh` and `remote_run_m4.sh` are the operator's files and are not written by the build.

## Checklist of gate changes the build must carry (47 entries)

1. **Order on the box.** install and downloads (with the smoke check, item 33); R1 controls (60 s sleep, empty run,
   unit-and-scale print); anchor (serial, then parallel); per-pair docking and analysis (aux timing); AlphaFold timings
   (seed-major); MD timings; storage; endpoints. A guard before every stage. (GATE_COMMIT answers 7, 14.)
2. **Files (rule 5).** The build writes exactly `run_m4.py` and `onbox_m4.sh` in
   `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure` (absolute path), and reads the design record and
   `frozen/`. Payload shipped to the box: `run_m4.py onbox_m4.sh remote_run_m4.sh frozen/provenance.py`, and `data/` recursively
   if it exists, all under `~/m4_run/`. Results under `~/m4_run/results_m4/out/`, which the launcher fetches. Nothing else is on
   the box.
3. **Records (rule 6) (revised, addendum 5).** For each input C1 to C4 one provenance.py record
   `results_m4/out/endpoint-C<i>_tag-m4.json`; its `values` carries `measured` (a number in the card's unit: C1 h per run, C2
   ns/day, C3 h per pair, C4 GiB), `unit`, `card_value` (0.5, 129, 1, 200) and `band` ([0.2, 1.25], [51.6, 322.5], [0.3333, 3],
   [66.67, 600]); its `decision` is PASS, FAIL or VOID against that band; `run_valid` in every record. An anchor record
   `endpoint-anchor_tag-m4.json` (values: `measured`, `published`, `tolerance`). `RUN_VALID.json`, `m4_summary.json`, and raw rows
   as JSON lines (`rows_<arm>_tag-m4.jsonl`, one line per timed run, per docking, per MD segment, per storage measurement).
   Records written before the decision that fails carry run_valid true; the run is marked invalid before the failing record is
   written, so a failing sleep record, a failing anchor record and every record after carry run_valid false, and
   `RUN_VALID.json` and the summary agree (E15). Every record's `inputs` lists its rows file, the pip report with its sha256 and
   the apt hash file (item 34), and the pair evidence file where it applies (item 40).
4. **Selftest (rule 7) (revised, addendum 3).** `python3 run_m4.py --selftest`: stdlib only, no GPU, no network, under 300 s;
   prints `selftest: N of M checks passed`, a line `selftest: files sha256 run_m4.py <hash> onbox_m4.sh <hash>` (item 36), then
   exactly `selftest: PASS` or `selftest: FAIL` as its last line; non-zero exit on FAIL. Planted cases for every parser and for
   the gate-failure (void) path (items 21 to 29, 31 and 47 list them).
5. **Secrets (rule 8) (revised, addendum 3).** Nothing reads `.keys`; nothing prints its environment (no `env`, `printenv` or
   `set` dump; `env.txt` lists only named non-secret variables); `HF_TOKEN` is used by downloads only: `onbox_m4.sh` unsets
   `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` after the downloads, and `run_tool` gives every child a copied environment with both
   removed. Selftest: a planted environment with both variables gives a child environment without them. (B7)
6. **Labels (rule 9) (revised, addendum 5).** Every measured record carries instance type (`INSTANCE_TYPE`), GPU name and driver
   (nvidia-smi), CUDA runtime version (the driver's "CUDA Version" from the nvidia-smi header, parsed, plus the JAX CUDA plugin
   package version; a value that cannot be had is null with a reason, never omitted), engine version and build flags
   (AlphaFold implementation and its parameter archive sha256, JAX, jaxlib and CUDA-plugin versions and wheel build tags, docking
   code and version, MD engine, version, precision and platform), start and end wall-clock (UTC, of the stage or run that
   produced the value, not the record's write time), price per hour. Every C record also carries "stand-in pairs built from 6IHB
   chains, not the card's pairs", "one GPU; one box; 3 pairs; no multi-GPU scaling" and `n`. C1 adds "no-MSA: alignment search
   time excluded; understates the card's setting"; C2 the atom count of each complex, the engine precision, platform and version,
   `timestep_fs`, `production_ns` and the per-complex wall-clock and engine rates; C3 "producer's reading of aux hours"; C4
   "linear in runs; intermediates kept; MD length 0.5 ns". The anchor adds `independent_code: "not run: single docking code"`.
   Every record written after a guard, ceiling or timeout stop carries "incomplete run: unmeasured inputs are VOID, not holding"
   (item 35). Selftest: every record kind the selftest flow writes carries every label key. (E10, E11)
7. **Nothing interactive; downloads; command (rule 10) (revised, addendum 5).** No prompts anywhere; `sudo` only for declared apt
   packages (the build declares them in `onbox_m4.sh`, `python3-venv` among them), called as
   `sudo -n env DEBIAN_FRONTEND=noninteractive apt-get ...`; `apt-get update` called the same way is allowed as the first step of
   those installs and no other sudo call is (B11, E20); downloads only from the sources in item 14, URL and sha256 recorded for
   each (pip and apt too, item 34); no unrecorded download, so no `pip install --upgrade pip` (E14); the on-box command the
   build returns (`onbox_command`) is one line the operator runs verbatim through `remote_run_m4.sh`.
8. **Broken infrastructure (rule 4) (revised, addendum 5).** Ubuntu 22.04, CUDA 12.8, driver 570, python 3.10, torch 2.7 are
   preinstalled; anything else is installed by `onbox_m4.sh` inside the time cap. Any failure of install, download, GPU check,
   smoke check (item 33), tool start, or install-total ceiling (item 28), and any real tool failure (non-zero exit, crash,
   missing output, no parsable ranked pose, unparsable rank table): exit non-zero with a void record (run_valid false, summary
   written, `RUN_DONE` with the exit code); never patch around, never substitute a tool or a source. `onbox_m4.sh` sets its exit
   trap before the venv step, so an abort before `run_m4.py` starts still writes a minimal void record, `RUN_VALID.json` (false)
   and `RUN_DONE` with exit 2 from the shell itself (E14). A tool call that merely exceeds its stage allowance is not broken
   infrastructure: it is a ceiling stop (item 29). Exit codes: 2 infrastructure or harness failure, 3 cost or time guard stop, 4
   anchor miss.
9. **Caps (rules 1, 2) (revised, addendum 5).** `onbox_m4.sh` reads `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD` and `REMOTE_TIMEOUT`
   from its environment, with no default that exceeds `BUDGET_LEFT_USD=5` or `REMOTE_TIMEOUT=7200`, and stops cleanly, writing a
   void record for unfinished work, before projected spend reaches `BUDGET_LEFT_USD` or elapsed time reaches `REMOTE_TIMEOUT`.
   Hard cap USD 10 for the run, at most two launches. It records the `REMOTE_TIMEOUT` it sees in `env.txt` and
   `m4_summary.json`; if unset it uses 7200 and labels "REMOTE_TIMEOUT not forwarded; default 7200 used" (item 37). Elapsed
   time counts from the start of the bootstrap (item 44). (B4, E19)
10. **Scope (rule 3).** Measure the inputs on the card's own protocol; no production phase, no 54-run pilot, no 216-run grid;
    anchor first; a missed anchor voids the inputs (run_valid false propagates to every later record).
11. **Gate scope (answer 1) (revised, addendum 5).** The card's gate (`af2_h_per_run <= 1`) is applied to C1 only: C1 values carry
    `gate_value`, `gate_pass` and the card's fallback text in `gate_else` ("take the docking-plus-MD fallback line with one
    AlphaFold-Multimer seed per pair, or move the grid to 12 pairs"); C2 and C3 carry `gate: "not applicable: the card's gate is
    on af2_h_per_run"`. The C1 decision is the band alone. The run does not branch on the gate. `gate_pass` is computed only
    when C1 holds a valid measurement (PASS, FAIL, or marginal VOID); for any other VOID (not an A100, below minimum, zero
    spread, a stop, `download_in_timed_call`) it is null with `gate: "not evaluated: C1 VOID (<reason>)"` and the summary does
    not present the fallback text as triggered. (E21)
12. **Pairs and seeds (answer 2) (revised, addendum 5).** 3 stand-in pairs built from chains of the 6IHB entry, one per capsid
    slot, each a hetero-multimer of 750 to 1,000 residues with the lengths spread over that range; chain ids, sequences, lengths
    and file hash recorded and checked as item 40 says. AlphaFold seeds 0, 1, 2. Seed-major order. Minimums: C1 at least 3
    completed runs covering all 3 pairs; C2 at least 2 complexes (n recorded); C3 at least 2 pairs; C4 at least one run of each
    artifact type; below a minimum the record is VOID and the raw rows stay.
13. **AlphaFold protocol (answer 3) (revised, addendum 5).** One GPU; 5 models; exactly 20 recycles with early stopping off;
    single-sequence input only; no sequence database download and no remote alignment service. Measured = mean wall-clock hours of
    the whole prediction call per run, first-model compile included (the decision value); rows also carry the compile-excluded
    figure when the log gives per-model times. The parameter files are in place before any timed call (item 39), so no download
    or extraction time can enter the call.
14. **Allowed download sources (answer 3).** The PDB entry 6IHB from RCSB; the AlphaFold parameter archive from the
    AlphaFold project's own storage address; Python wheels through pip and declared packages through apt. Each URL and sha256
    recorded. Any other host is not allowed; a failed download stops the run (item 8).
15. **Auxiliary hours (answer 4).** aux_h_per_pair = per pair wall-clock hours of docking, interface analysis (contacts at
    4.5 A, interface residues, distance to the nearest threefold axis, site class) and writing the call-table row; installs,
    downloads and setup excluded; mean over the finished pairs (3 if all finish). One pip-installable docking code, name and
    version recorded.
16. **Storage (answer 4) (revised, addendum 5).** n_storage_gib = apparent bytes written for one grid run (AlphaFold outputs of
    one run; the whole per-pair docking output directory tree, with setup files, copied structures, swarm directories, rank tables
    and every pose file; MD trajectory and every log of one 0.5 ns segment, the engine rate file included, frame interval
    recorded), intermediates kept, x 216, / 2^30; the decision value. The record also carries the 432-run figure, the
    intermediates-deleted figure and MD bytes per ns, as information. (E6, E25)
17. **MD protocol (answers 5, 10) (revised, addendum 5).** One docked complex per sampled pair, built as item 41 says: the pair's
    capsid-role chains merged with the top-ranked docking pose of the receptor, explicit solvent, water padding chosen so the
    atom count is inside 120,000 to 180,000; minimise, short equilibration, then a 0.5 ns production segment; one velocity seed
    (0). ns/day from the engine's rate line (the reporter file, item 41) and, separately, from production steps x timestep over
    the wall-clock of the production segment; the decision value is the median over complexes of the wall-clock figure; if the two
    disagree by more than 5 percent every ns/day is labelled "engine rate and wall-clock disagree" and both are reported. Atom
    count outside the range: C2 VOID, the range is not widened.
18. **Marginal rule (GATE_COMMIT instrument queue).** A value within 10 percent of a band edge (`edge x 0.9` to `edge x 1.1`) is
    decision VOID with `marginal: true`; the raw value is kept in `measured`.
19. **Non-A100 GPU (design, does_not_test).** If the GPU is not an A100 (instance fallback), C1 and C2 are VOID with the raw
    number kept and the label "not an A100"; C3 and C4 are still decided and labelled with the GPU.
20. **Controls first (answer 7) (revised, addendum 5).** After install: planted 60 s sleep (error at most 5 percent, else
    run_valid false, exit 2); empty-input run, which times the harness itself (the same timer, work-directory creation and
    record path as a real call, around a no-op command, with no AlphaFold, JAX, TensorFlow or docking import) and measures the
    bytes in the directory that call created (time under 2 s and bytes under 1 MiB, else the excess is subtracted from later
    values, only that harness overhead, and the label "setup overhead subtracted"); one unit-and-scale record (raw AlphaFold
    seconds, MD engine rate lines with the wall-clock ns/day beside them, raw bytes per artifact). No band is compared before
    these are written. (E7)
21. **Anchor readout (answer 8; revised, addendum 5).** Contact overlap = fraction of 6IHB interface residue-residue contacts
    (heavy-atom pair at most 4.5 A) that the pose makes; pass if overlap at least 0.50 or interface backbone RMSD at most 5.0 A,
    and serial vs parallel top-pose RMSD at most 2.0 A with identical bind/no-bind calls. Selftest, planted: (0.50, RMSD 9.0)
    pass; (0.49, 5.0) pass; (0.49, 5.01) fail; serial-parallel 2.0 with equal calls pass, 2.01 fail, 0.0 with different calls
    fail; 3 of 6 contacts gives 0.5; a 5.0 A shift along x gives RMSD 5.0. The anchor runs serially, then in parallel on the
    same box, seed 0. A miss writes C1 to C4 as VOID, run_valid false, exit 4. The second independent docking code is not run
    (answer 5). Contacts are keyed by chain role, not by the file's chain id: the reference and the pose pass through one
    chain-mapping function before keys are built, so the same planted pose gives overlap 0.5 with the receptor chain id "B",
    "C" and "A", and an overlap of 0.0 on a planted pose with non-trivial overlap fails the selftest, native-versus-pose round
    trip through `write_pdb` and `read_pdb_atoms` included (B5). The interface backbone RMSD is over the N, CA, C, O atoms of the
    receptor residues that form the reference interface (any heavy atom within 4.5 A of the capsid in 6IHB), in the capsid
    frame, no superposition; a planted pose moving only non-interface receptor atoms by 20 A gives interface RMSD 0.0000 and a
    whole-chain RMSD above 0; the serial-parallel RMSD stays over the whole receptor chain and is labelled so (B10). Three
    routes, no overlap (E8): a docking call over its allowance is a ceiling stop (exit 3, anchor undecided, C1 to C4 VOID
    "unmeasured, not holding", run_valid as it was); a docking tool that fails, or leaves no parsable ranked pose, is a harness
    failure (exit 2, run_valid false, raw output kept); exit 4 only when a pose was obtained and compared and the tolerance was
    missed. `anchor_decision` never receives a missing pose.
22. **C1 selftest (answer 9) (revised, addendum 5).** 1,800 s per run gives 0.5 h; means 0.5 PASS, 1.5 FAIL, 0.1 FAIL, 1.2 VOID
    (marginal; `gate_pass` false), 0.21 VOID, 1.1 PASS with `gate_pass` false and the fallback text, 0.9 PASS with `gate_pass`
    true; n=2 runs VOID with `gate_pass` null; 3 runs missing one pair VOID with `gate_pass` null.
23. **C2 selftest (answer 10).** A planted engine log rate line parses to its number; 250,000 steps x 2 fs in 335 s gives 128.96
    ns/day; median of (100, 129, 500) is 129 PASS; 40 FAIL; 400 FAIL; 56 VOID; 60 PASS; 330 VOID; atom counts 119,999 and
    180,001 VOID, 150,000 passes the size check; a GPU name other than A100 VOID for C1 and C2.
24. **C3 selftest (answer 11).** Three pair wall-clocks of 3,600 s give 1.0 h PASS; 0.2 FAIL; 4.0 FAIL; 0.3333 VOID; 3.2 VOID;
    0.5 PASS; 2.5 PASS; 7,200 s install plus 1,800 s docking gives 0.5 h.
25. **C4 selftest (answer 12) (revised, addendum 5).** 1,073,741,824 bytes per run = 1.0 GiB x 216 = 216.0 PASS (432-run figure
    432.0); 0.1 gives 21.6 FAIL; 4.0 gives 864.0 FAIL; 2.9 gives 626.4 VOID; 0.35 gives 75.6 PASS; files of 1,000 and 24 bytes sum
    to 1,024; a planted docking tree with a nested swarm directory and a top-level `setup.json` sums every file (E25).
26. **Harness selftest (answer 13).** 62.9 s for the 60 s sleep passes; 63.1 s fails (run_valid false, exit 2); timings (1,800,
    1,830, 1,790) pass the spread check; (1,800, 1,800, 1,800) fails and gives C1 VOID with "zero spread across seeds: wrong
    variance source" while other inputs stand; relative SD 0.6 gives the label "seed spread high; mean is uncertain" only;
    empty run 0.5 s and 100 KiB pass, 5 s or 2 MiB trigger the subtraction label.
27. **Cost and time selftest (answer 14; revised, addendum 5).** 3,600 s at 1.99 gives 1.99; 7,200 s gives 3.98; with price
    1.99, budget 5, timeout 7,200 the guard stops at the time cap (5 / 1.99 h = 9,045 s is above it); with price 2.50 both caps
    coincide at 7,200 s; with 3.00 the dollar cap stops at 6,000 s; a stage whose estimated remaining time exceeds the time left
    is not started, the guard writes VOID (unmeasured) records for unfinished inputs, keeps finished ones, exits 3, and leaves
    run_valid as it was. The guard is called with an estimate (item 43). The gate-failure (void) path is also planted for: anchor
    miss, sleep failure, install failure, download failure, smoke-check failure. The stage flow itself (not only the functions)
    is planted in items 31 and 47.
28. **Stage ceilings (GATE_COMMIT answer B8; revised, addendum 5).** In seconds: install and downloads with the smoke check
    1,800; controls and anchor 700; per-pair docking and analysis 600 in total, at most 250 per pair; AlphaFold 2,000; MD 1,600,
    at most 600 per complex; endpoints 100; margin 400; total 7,200. A stage's allowance is the lesser of its ceiling and the
    time left minus the margin and the endpoints slot. The install ceiling is a running total: every apt, pip, download,
    extraction and smoke-check call takes `min(its own limit, 1,800 minus install seconds used, the allowance above)`, and
    exhausting it ends the stage with exit 2 (broken infrastructure, void record, A2(a)), not exit 3. A later stage that hits its
    ceiling stops and its unfinished inputs are VOID ("unmeasured, not holding", with the full incomplete-run label, item 35).
    A docking pair that reaches its 250 s is kept as a row with `truncated: true`, not counted in the mean; C3 stays decided if at
    least 2 pairs finished, else VOID. Selftest: planted install calls whose per-call limits sum past 1,800 s stop at 1,800 s. (E2)
29. **Gate-failure and guard-stop paths (answers 8, 13, 14; revised, addendum 5).** run_valid false when the anchor misses (exit
    4), the sleep check fails (exit 2), or infrastructure breaks (exit 2); it propagates to every later record, `RUN_VALID.json`
    and `m4_summary.json`. A guard stop does NOT set it false: a time-guard refusal to start a stage or unit, a stage ceiling, a
    tool call exceeding its stage allowance, or the outer timeout voids the unfinished inputs, keeps finished inputs' decisions,
    leaves run_valid as it was, labels later records "incomplete run: ...", and the run ends with exit 3. `fail_stage` sets
    run_valid false only for exit 2 and 4. Each early return in `stage_af2`, `stage_aux` and `stage_md` raises `GuardStop` or
    records the stop in run state that `run_stages` reads; a stage that stopped on a ceiling, guard or timeout is not in
    `stages_done` even when it returned normally (C3 still decided on 2 finished pairs, item 28); later stages whose own guard
    allows still start; `stage_endpoints` always runs. Exit 3 is returned only when a guard, ceiling, tool-timeout or
    outer-timeout stop left an input unmeasured; a VOID by rule with no stop (not an A100, zero spread, marginal) ends with exit
    0, and `RUN_DONE` carries the exit code and the void reason per input; exit 0 otherwise only when every input was decided
    by measurement. A timed-out tool's row is kept with `incomplete: true` and is not counted in a mean. (B1, B2, B3, E17, E22)
30. **Summary and spread (answers 5, 6; revised, addendum 5).** `m4_summary.json` is written without `sort_keys` and its first
    key is `what_this_run_decides`, stating that the run decides the stand-in protocol only; it then restates every record, the
    gate result and the fallback text (item 11); carries no decision of its own; carries the label "seed spread high; mean is
    uncertain" for any pair with relative SD over 50 percent; and carries the full "incomplete run" label after an early stop. No
    relaunch is made for spread. Selftest reads the written file as text and checks the first key. (E9)
31. **Stage-flow selftest (new, addendum 3, B15).** `run_stages` takes its stage functions and tool runner by injection; the
    selftest runs the whole flow with fakes and asserts exit code, run_valid, per-input decisions and labels for: (a) all stages
    finish: exit 0, run_valid true; (b) a time-guard stop in AlphaFold after 2 of 9 runs: exit 3, run_valid true, C1 VOID with
    raw rows kept, C2 to C4 decided; (c) a tool timeout in MD on the third complex: exit 3, run_valid true, C2 decided on n=2,
    others untouched; (d) a ceiling stop in docking: exit 3, C3 decided on the finished pairs or VOID below 2; (e) a real tool
    failure: exit 2, run_valid false, all inputs VOID; (f) anchor miss: exit 4, run_valid false, C1 to C4 VOID; (g) sleep
    failure: exit 2; (h) install, smoke-check and download failure: exit 2; (i) the outer-timeout route (rc 124): exit 3,
    run_valid true. Addendum 5 adds: (j) docking timeout in the anchor: exit 3, anchor undecided; (k) docking with no parsable
    pose: exit 2, run_valid false; (l) not-an-A100 or zero spread with no stop: exit 0 with the VOIDs.
32. **Process groups and outer timeout (new, addendum 3, B12; revised, addendum 5).** Every tool call (colabfold, the docking
    code, the OpenMM worker) runs in its own process group and a timeout kills the group; when the outer `timeout` on `run_m4.py`
    returns 124, or 137 with elapsed time since T0 at least the outer deadline minus 5 s, `onbox_m4.sh` kills the recorded
    process groups before the endpoints stage and routes the outcome as a guard stop, exit 3, not as `fail`/exit 2; rc 137
    earlier than that is a failure (exit 2). Each pgid is recorded with its leader's `/proc/<pid>/stat` start time and command
    name, removed when the tool returns, and signalled only if the leader is alive and both still match (a skipped entry goes to
    the log). The inner tool timeout is at least 100 s shorter than the outer kill (outer kill = stop_at minus elapsed minus
    600; inner = stop_at minus elapsed minus 700) so the inner fires first; an outer firing is itself a recorded event.
    Selftest: a planted tool that sleeps past its allowance is killed with its child and the result is a ceiling stop; planted
    rc 137 at the deadline gives exit 3, at 100 s exit 2; a stale pgid entry with a different start time is not signalled. (E23)
33. **Smoke check in the install stage (new, addendum 3, B6; revised, addendum 5).** After every install and inside the 1,800 s
    install ceiling: import of the AlphaFold-Multimer stack and JAX with a GPU device listed; `colabfold_batch --help`; the
    docking code's entry point `--help`; OpenMM imported with `Platform.getPlatformByName("CUDA")` succeeding; and each tool
    resolved by `shutil.which` against the venv PATH with its absolute path recorded (item 38). A failure is exit 2 with a void
    record before any GPU stage. Every package is pinned by version in the install line; the build chooses the package form
    whose metadata carries the CUDA platform for OpenMM and what the smoke check imports for colabfold, and a JAX build
    compatible with the pinned `colabfold`, without substituting a tool; the smoke check decides, not recollection. No trial
    docking is run in the install stage. (E12, E13)
34. **Downloads recorded in full (new, addendum 3, B13; revised, addendum 5).** pip installs run with `--report`; the report (URL
    and archive hash of each wheel) is kept under `results_m4/out/` and its sha256 is cited in every record's `inputs` (E24); each
    apt package is recorded with version and the SHA256 from `apt-cache show`; the direct downloads keep URL and sha256.
35. **Incomplete-run label (new, addendum 3, B9).** The constant "incomplete run: unmeasured inputs are VOID, not holding" exists
    beside `LABEL_UNMEASURED = "unmeasured, not holding"`; every record and the summary written after a guard, ceiling or
    timeout stop carries the full label. Selftest: a planted early-stopped run's records all contain it.
36. **Selftest ties its log to the files (new, addendum 3, B14).** The selftest prints
    `selftest: files sha256 run_m4.py <hash> onbox_m4.sh <hash>` (the script hashes itself and `onbox_m4.sh` with the stdlib)
    before its final line; the build's return states the real line counts and those hashes. The operator re-runs the selftest
    after the build and compares before any launch.
37. **Launcher and REMOTE_TIMEOUT (new, addendum 3, B4; operator's change, listed so the build relies on it).** `lambda_run_m4.sh`
    forwards `REMOTE_TIMEOUT` with `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD` and `INSTANCE_TYPE`; the build does not write it. The
    build's two files read the variable, never default above 7200, record the value seen (item 9), and label an unset value.
38. **Tools resolve through the venv (new, addendum 5, E1, E12, E14).** `onbox_m4.sh` exports `PATH="${VENV}/bin:${PATH}"` before
    the first stage; `run_m4.py` builds `child_env` with the venv bin directory (taken from `sys.executable`'s directory) first
    and calls `colabfold_batch`, `lightdock3.py`, `lightdock3_setup.py` and `lgd_*` by absolute venv path where it can; an
    unresolved tool is exit 2 in the install stage. `python3-venv` is a declared apt package; the venv's bundled pip is used with
    no `--upgrade pip`. Selftest: a planted venv directory with an executable stub resolves through `child_env`, not through the
    bare inherited PATH.
39. **Parameter archive extracted, no download in a timed call (new, addendum 5, E3).** The install stage verifies the AlphaFold
    parameter archive's sha256 (recorded), extracts it into `<data>/params`, the same `--data` directory colabfold is given, and
    verifies the multimer parameter files for the 5 models are present before the smoke check ends; missing is exit 2.
    Extraction time is install time, never C1 time. A timed call whose log shows a download or extraction gets
    `download_in_timed_call: true` on its row, is not counted, and C1 is VOID "download inside timed call". Selftest: a planted
    archive extracts to the expected layout; a planted "Downloading" log line sets the flag.
40. **Stand-in pair checks and evidence (new, addendum 5, E4).** After building the pairs, assert: each total length in 750 to
    1,000; the three sequences pairwise different; the three lengths pairwise at least 20 residues apart; one capsid-role set and
    one receptor-role set per pair. More than one copy of a capsid chain may be used to reach the range; if the range or the
    spread still cannot be met, exit 2 with a void record naming the assertion; no silent clamp of `want_cap`. Write
    `results_m4/out/pairs_tag-m4.json` (chain ids and role mapping, sequences, lengths, sha256 of each pair's FASTA and PDB file)
    and copies of the three FASTA files into `results_m4/out/`; each C record cites that file's hash in `inputs`. Selftest: a
    planted short capsid chain fails the range; equal-length pairs fail the spread; planted good pairs pass and the evidence file
    parses.
41. **MD on the merged complex; engine rate file parsed (new, addendum 5, E5, E6).** The MD input is the pair's capsid-role chains
    from the stand-in pair file merged with the top-ranked docking pose of the receptor, one structure, chain roles preserved;
    assert both roles present and a nonzero capsid heavy-atom count before solvation, else exit 2. Water padding is estimated from
    the solute's extent so the built system has 120,000 to 180,000 atoms, verified on the built system, one rebuild allowed inside
    the complex's 600 s; if it cannot be met, C2 VOID with the atom count kept. The worker's StateDataReporter file is copied to
    `results_m4/out/` and is the file parsed for the engine's ns/day (the tool's stdout log is not); a rate file with no
    parsable rate line gives `engine_ns_per_day: null` and the label "engine rate line missing" and C2 still rests on the
    wall-clock figure. Selftest: a receptor-only pose is refused; a merged complex passes the role check; a planted reporter
    file in its real column layout parses; one without a rate line gives null and the label; 129 against 100 fires the
    disagreement label.
42. **Docking pose: top-ranked or nothing (new, addendum 5, E8, E13).** The top pose is the first row of the tool's own rank list
    by its score; a missing named pose file or an unparsable rank table is exit 2 with the raw table kept in `results_m4/out/`;
    the lexicographically first pose is never a fallback. The first use of the docking output in the anchor stage is the rank
    table parse. Selftest: planted rank tables with the assumed columns parse; a table without a rank column is refused.
43. **Guard estimates (new, addendum 5, E16).** Every `guard_before_stage` call and every unit inside a stage passes
    `estimated_s`: the mean of finished units of that kind, else the floor (anchor serial or parallel 60 s, docking pair 60 s,
    AlphaFold run 120 s, MD complex 150 s, storage 20 s, endpoints 30 s). A unit whose estimate exceeds its allowance is not
    started and is recorded as a guard stop. Selftest: 100 s left with a 150 s estimate does not start.
44. **Bootstrap time counts (new, addendum 5, E19).** `onbox_m4.sh` sets T0 to the start of its parent `remote_run_m4.sh`
    (`ps -o etimes= -p $PPID`) plus 30 s; an unreadable value takes 300 s and the label "bootstrap time assumed 300 s"; the
    pre-T0 seconds go to `env.txt` and the summary. `STOP_AT` and elapsed time use this T0. Selftest: a planted `etimes` value
    moves T0; garbage takes the default and the label.
45. **Caches under the run directory (new, addendum 5, E20).** `PIP_CACHE_DIR`, `XDG_CACHE_HOME`, `MPLCONFIGDIR`, `TMPDIR` and
    any JAX or colabfold cache variable the build sets point under `~/m4_run/`. The frozen bootstrap's `~/.local` installs are
    the operator's and are not the build's to change.
46. **Exit-code vocabulary in `RUN_DONE` (new, addendum 5, E22).** `RUN_DONE` carries the exit code and, per input C1 to C4,
    decided, void-by-rule with its reason, or unmeasured by a named stop, so A2(a) and A2(b) are readable from it alone.
47. **The selftest runs the real stage bodies (new, addendum 5, E28; binding).** Besides the injected-fake flows (item 31), the
    selftest runs the real `stage_*` bodies with the tool runner, clock and filesystem roots injected and fake tool executables
    in a planted venv bin directory (stdlib only, no GPU, no network, still under 300 s). It asserts at least: tools resolve
    through the venv PATH (item 38); the parameter directory is populated before a timed call (item 39); the pair assertions
    (item 40); the MD input holds both chain roles and the reporter file is parsed (item 41); the empty-run control times the
    harness (item 20); the three docking failure routes (item 21); the install total ceiling (item 28); and the first key of
    `m4_summary.json` (item 30).

## Box

- Instance: `gpu_1x_a100_sxm4` (A100 SXM4 40 GB, USD 1.99/h) in us-east-1 if it has capacity; else the cheapest single GPU
  with capacity at no more than USD 2.50/h; the operator records which.
- Launcher (revised, addendum 5): the operator's per-launch copy `lambda_run_m4.sh` (made from `frozen/lambda_run.sh` at the
  header's declared points only; the header declares the four added variables and any added fetch line, such as the one for
  `results_m4/out/RUN_VALID.json`): remote dir `m4_run/`; payload `run_m4.py onbox_m4.sh remote_run_m4.sh frozen/provenance.py`
  and `data/` recursively if it exists; forwarded env `PRICE_USD_PER_HOUR BUDGET_LEFT_USD REMOTE_TIMEOUT INSTANCE_TYPE`; fetch
  from `m4_run/results_m4/out/`. `remote_run_m4.sh` is `frozen/remote_run.sh` with only its `cd` line changed to `~/m4_run`; its
  bootstrap time is counted by the build (item 44).
- Caps: `REMOTE_TIMEOUT=7200`; `BUDGET_LEFT_USD=5` per launch; two launches at most within USD 10.
- Payload layout on the box: `~/m4_run/run_m4.py`, `~/m4_run/onbox_m4.sh`, `~/m4_run/frozen/provenance.py`, `~/m4_run/data/...`
  if shipped. Results under `~/m4_run/results_m4/out/`.
- The build's `onbox_command` is a single line the operator runs verbatim on the box through `remote_run_m4.sh`
  (`bash remote_run_m4.sh bash onbox_m4.sh`).

## Local selftest (revised, addendum 5)

`python3 run_m4.py --selftest` is stdlib-only and runs under `timeout 300`: no GPU, no network. It covers every parser
(engine rate line and reporter file, MD log and production wall-clock, AlphaFold timing rows, docking rank and contact tables,
byte counts, nvidia-smi labels including the CUDA version header, pip report, `etimes`), the marginal rule, the planted cases of
items 21 to 27, the stage-flow cases of item 31, the real-stage-body cases of item 47, the process-group kill of item 32, the
child-environment and venv-PATH cases of items 5 and 38, the incomplete-run label of item 35, the void path of item 29, record
writing through `frozen/provenance.py`, and the file-hash line of item 36. No local tool run (no AlphaFold, docking or MD).

## What the runner writes (`results_m4/out/`) (revised, addendum 5)

- `endpoint-anchor_tag-m4.json` and `endpoint-C1_tag-m4.json` to `endpoint-C4_tag-m4.json`, plus one provenance.py record
  for each control (60 s sleep, empty run, unit-and-scale), each with `cell`, `inputs` with hashes, `metric`, `values`,
  `threshold`, `decision_rule` written before values, `decision`, `run_valid`.
- Raw rows, one JSON line each (`rows_<arm>_tag-m4.jsonl`): every AlphaFold run (pair, seed, wall-clock, per-model times when
  available, `incomplete` when timed out, `download_in_timed_call`), every docking and analysis timing (`truncated` when it hit
  its per-pair cap), every MD segment (complex, atom count, steps, wall-clock, engine rate or null), every storage measurement
  (artifact, apparent bytes).
- `pairs_tag-m4.json` and the three pair FASTA files (item 40); the MD reporter files and the raw docking rank tables (items 41,
  42).
- `RUN_VALID.json`; `env.txt` (named non-secret variables only, including the `REMOTE_TIMEOUT` seen and the pre-T0 seconds);
  `m4_summary.json` (first key `what_this_run_decides`); download, install, smoke-check and tool logs; the pip report and the
  apt package hashes (item 34); the `RUN_DONE` marker with the exit code (3 after any guard, ceiling or timeout stop with inputs
  unmeasured) and the per-input status (item 46).
