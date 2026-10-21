# Execution directive for build (tag m4), revised on 2026-10-21 after the reviews of build 2 (addendum 3), build 6 (addendum 5), build 7 (addendum 6), build 9 (addendum 7), launch 1 (addendum 8) and builds 11 and 13 (addendum 9) (revised, addendum 9)

Binding order: GATE_COMMIT.md answers first (the original answers 1 to 14, then addendum 3 answers B1 to B15, then addendum 5
answers E1 to E28, then addendum 6 answers F1 to F22, then addendum 7 answers G1 to G8, then addendum 8 answers H1 to H10, then
addendum 9 answers J1 to J9), this note second, `out/design_record.json` third; `frozen/ONBOX_CONTRACT.md` binds under rule 5 and
nothing here loosens it except at the points item 56 names (where it states a docking command order, that order is followed, item
52). Where silent, the design record binds as written, GUESS values included. The build does not read GATE_COMMIT.md itself; the
checklist below carries every gate change the build must implement. This is the measure run m4 of card seed:idea:1: one rented
single-GPU box, a timer check, an anchor redocking of AAVR-PKD2 onto AAV2 against PDB 6IHB, then four inputs (AlphaFold-Multimer
hours per run, MD ns/day, auxiliary hours per pair, storage GiB) each read against the card's own band. The cap is USD 10 for the
whole run, at most two launches. Launch 1 has run: it ended in 9 minutes with exit 2 at the pip install step (the pins
`openmm==8.2.0` and `openmm-cuda==8.1.1.12` cannot be resolved together), USD 0.30, nothing measured, void records written as the
contract requires. Builds 11 and 13 left the pins unchanged because the evidence file they were told to read held the wrong
content (J5), and the operator's pre-launch resolve failed with the same conflict. Build 14 is the next and last build on this
matter: an in-place edit limited to what item 65 lists, started only after the operator's test of item 66 passes on the pins of
item 58. Launch 2 is the last launch allowed. Items marked `(revised, addendum 3)` changed build 2's behaviour, items marked
`(revised, addendum 5)` changed build 6's, items marked `(revised, addendum 6)` changed build 7's, items marked `(revised,
addendum 7)` changed build 9's, items marked `(revised, addendum 8)` changed build 10's, items marked `(revised, addendum 9)`
change build 11's; items 63 to 67 are new in addendum 9; items 58 to 62 came with addendum 8 (58, 61, 62 revised again);
items 55 to 57 came with addendum 7; items 48 to 54 came with addendum 6; items 38 to 47 came with addendum 5; items 31 to 37
came with addendum 3; the rest stand. Items 6, 8, 28 and 29 are restated in addendum 6 as single testable requirements; review
judges the build against those texts. (revised, addendum 9)

## Where to write

The run directory is `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure`. Write exactly `run_m4.py` and
`onbox_m4.sh` there, by absolute path. Write nothing anywhere else. Read the design record at
`/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure/out/design_record.json` and the conventions in `frozen/`
(provenance.py is the record writer; lambda_run.sh and remote_run.sh show what the box does; `ONBOX_CONTRACT.md` is the binding
execution contract). Build 14 reads no other file as an input (item 67): the operator's evidence files under `out/` are not inputs,
because the pins are written in item 58. It edits the existing `run_m4.py` and `onbox_m4.sh` of build 11 in place and uses no
network. `lambda_run_m4.sh` and `remote_run_m4.sh` are the operator's files and are not written by the build. (revised, addendum 9)

## Checklist of gate changes the build must carry (67 entries)

1. **Order on the box.** install and downloads (with the smoke check, item 33); R1 controls (60 s sleep, empty run,
   unit-and-scale print); anchor (serial, then parallel); per-pair docking and analysis (aux timing); AlphaFold timings
   (seed-major); MD timings; storage; endpoints. A guard before every stage. (GATE_COMMIT answers 7, 14.)
2. **Files (rule 5).** The build writes exactly `run_m4.py` and `onbox_m4.sh` in
   `/home/hal/dev/interp/metis/experiments/blind-01/20261021-0509-measure` (absolute path), and reads the design record and
   `frozen/` only (item 67). Payload shipped to the box: `run_m4.py onbox_m4.sh remote_run_m4.sh frozen/provenance.py`, and `data/`
   recursively if it exists, all under `~/m4_run/`. Results under `~/m4_run/results_m4/out/`, which the launcher fetches. Nothing
   else is on the box. (revised, addendum 9)
3. **Records (rule 6) (revised, addendum 5).** For each input C1 to C4 one provenance.py record
   `results_m4/out/endpoint-C<i>_tag-m4.json`; its `values` carries `measured` (a number in the card's unit: C1 h per run, C2
   ns/day, C3 h per pair, C4 GiB), `unit`, `card_value` (0.5, 129, 1, 200) and `band` ([0.2, 1.25], [51.6, 322.5], [0.3333, 3],
   [66.67, 600]); its `decision` is PASS, FAIL or VOID against that band; `run_valid` in every record. An anchor record
   `endpoint-anchor_tag-m4.json` (values: `measured`, `published`, `tolerance`). `RUN_VALID.json`, `m4_summary.json`, and raw rows
   as JSON lines (`rows_<arm>_tag-m4.jsonl`, one line per timed run, per docking, per MD segment, per storage measurement).
   Records written before the decision that fails carry run_valid true; the run is marked invalid before the failing record is
   written, so a failing sleep record, a failing anchor record and every record after carry run_valid false, and
   `RUN_VALID.json` and the summary agree (E15). Every record's `inputs` lists its rows file, the pip report with its sha256 and
   the apt hash file (item 34), and the pair evidence file where it applies (item 40). The records the shell writes on an early
   abort have the same keys (item 54).
4. **Selftest (rule 7) (revised, addendum 3).** `python3 run_m4.py --selftest`: stdlib only, no GPU, no network, under 300 s;
   prints `selftest: N of M checks passed`, a line `selftest: files sha256 run_m4.py <hash> onbox_m4.sh <hash>` (item 36), then
   exactly `selftest: PASS` or `selftest: FAIL` as its last line; non-zero exit on FAIL. Planted cases for every parser and for
   the gate-failure (void) path (items 21 to 29, 31, 47, 48, 49, 55, 58, 59, 60 and 64 list them).
5. **Secrets (rule 8) (revised, addendum 3).** Nothing reads `.keys`; nothing prints its environment (no `env`, `printenv` or
   `set` dump; `env.txt` lists only named non-secret variables); `HF_TOKEN` is used by downloads only: `onbox_m4.sh` unsets
   `HF_TOKEN` and `HUGGING_FACE_HUB_TOKEN` after the downloads, and `run_tool` gives every child a copied environment with both
   removed. Selftest: a planted environment with both variables gives a child environment without them. (B7)
6. **Labels (rule 9) (revised, addendum 6; restated as one requirement; sourcing of versions revised, addendum 8).** The runner
   keeps one constant, `REQUIRED_LABEL_KEYS`, mapping each record kind it writes through provenance.py (anchor, C1, C2, C3, C4,
   sleep control, empty-run control, unit-and-scale) to the keys that its `values.machine` (and, for C records and the anchor,
   `values.engine`) must hold. A key is never omitted: a value that cannot be had is null and `values.null_reasons[<key>]` is a
   non-empty string. Taken together the lists for every kind cover these nine labels, each by at least one key whose name contains
   the stated word: instance type (`instance`), GPU name (`gpu`), driver (`driver`), CUDA runtime version (`cuda`: the driver's
   "CUDA Version" from the nvidia-smi header, parsed, plus the JAX CUDA plugin package version), engine versions (`version`), build
   flags (`flags` or `tags`: AlphaFold implementation and its parameter archive sha256, JAX, jaxlib and CUDA-plugin versions and
   wheel build tags, docking code and version, MD engine, version, precision and platform), start and end wall-clock (`start`,
   `end`: UTC, of the stage or run that produced the value, not the record's write time), price per hour (`price`). Every engine
   and plugin version in these labels comes from the pip report of this run or from the installed distribution's metadata read
   after the install, never from a constant default; item 60. The control kinds need only the machine-level keys (instance, GPU,
   driver, CUDA, start, end, price); the anchor and C kinds need all. Every C record also carries "stand-in pairs built from 6IHB
   chains, not the card's pairs", "one GPU; one box; 3 pairs; no multi-GPU scaling" and `n`. C1 adds "no-MSA: alignment search
   time excluded; understates the card's setting"; C2 the atom count of each complex, the engine precision, platform and version,
   `timestep_fs`, `production_ns` and the per-complex wall-clock and engine rates; C3 "producer's reading of aux hours"; C4
   "linear in runs; intermediates kept; MD length 0.5 ns". The anchor adds `independent_code: "not run: single docking code"`.
   Every record written after a guard, ceiling or timeout stop carries "incomplete run: unmeasured inputs are VOID, not holding"
   (item 35). Planted selftest case: the selftest flow writes every record kind, and for each asserts that every key in
   `REQUIRED_LABEL_KEYS[kind]` is present, that every null has a reason, and that the nine-label coverage holds; a planted record
   with one key removed fails the check, and a planted null without a reason fails it. (E10, E11, F20, H3)
7. **Nothing interactive; downloads; command (rule 10) (revised, addendum 6 and addendum 8).** No prompts anywhere; `sudo` only for
   declared apt packages (the build declares them in `onbox_m4.sh`: `python3-venv`, `aria2`, `curl`, `build-essential` and
   `python3-dev`, exactly these five, item 59), called as `sudo -n env DEBIAN_FRONTEND=noninteractive apt-get ...`; `apt-get
   update` called the same way is allowed as the first step of those installs and no other sudo call is (B11, E20); downloads only
   from the sources in item 14, URL and sha256 recorded for each (pip and apt too, item 34); no unrecorded download, so `pip install
   --upgrade pip` is not used; the one pip bootstrap allowed is the recorded one of item 50 (F14); the on-box command the build
   returns (`onbox_command`) is one line the operator runs verbatim through `remote_run_m4.sh`.
8. **Broken infrastructure (rule 4) (revised, addendum 6; restated as one requirement).** Ubuntu 22.04, CUDA 12.8, python 3.10, torch
   2.7 are preinstalled; anything else is installed by `onbox_m4.sh` inside the time cap. Every outcome maps to
   exactly one row of this table, and the table is the only source of exit code, `run_valid` and `RUN_DONE` status:

   | Event | Exit | run_valid | `RUN_DONE` per-input status |
   |---|---|---|---|
   | install, download, GPU check, smoke check, tool start, install-total ceiling, apt or pip call over its limit, real tool failure (non-zero exit, crash, missing output), no parsable ranked pose, unparsable rank table, sleep check failed, shell abort before the runner starts | 2 | false | `void_by_failure:<kind>` for every input not decided before it |
   | anchor compared and tolerance missed | 4 | false | `void_by_anchor_miss` for C1 to C4 |
   | guard refusal, stage ceiling, tool-call timeout, outer timeout (124, or 137 at the deadline) left at least one input unmeasured | 3 | as it was | `unmeasured_by_stop:<kind>` for those inputs, `decided` or `void_by_rule:<reason>` for the others |
   | every input decided, or void by rule with no stop (not an A100, zero spread, marginal) | 0 | true | `decided` or `void_by_rule:<reason>` |

   Never patch around, never substitute a tool or a source: after a failing tool call no second tool and no second source is
   tried. Each failure row writes a void record (summary and `RUN_DONE` included) before exit. `onbox_m4.sh` sets its exit trap
   before the venv step, so an abort before `run_m4.py` starts still writes the shell's void record (item 54) with exit 2. A tool
   call that merely exceeds its stage allowance is a ceiling stop (item 29), not a failure. "Not decided before it" is read from
   the records on disk (item 55). Planted selftest cases: one stage-flow case per table row (items 31 and 48), each asserting
   exit code, `run_valid` and the status strings; a planted failing tool whose call count is asserted equal to 1 (no fallback
   tried). (E14, F5, F20)
9. **Caps (rules 1, 2) (revised, addendum 5).** `onbox_m4.sh` reads `PRICE_USD_PER_HOUR`, `BUDGET_LEFT_USD` and `REMOTE_TIMEOUT`
   from its environment, with no default that exceeds `BUDGET_LEFT_USD=5` or `REMOTE_TIMEOUT=7200`, and stops cleanly, writing a
   void record for unfinished work, before projected spend reaches `BUDGET_LEFT_USD` or elapsed time reaches `REMOTE_TIMEOUT`.
   Hard cap USD 10 for the run, at most two launches (launch 1 spent USD 0.30; launch 2 is the last, item 62). It records the
   `REMOTE_TIMEOUT` it sees in `env.txt` and `m4_summary.json`; if unset it uses 7200 and labels "REMOTE_TIMEOUT not forwarded;
   default 7200 used" (item 37). Elapsed time counts from the start of the bootstrap (item 44). Both launches run with
   `REMOTE_TIMEOUT=7200` exactly (G2). (B4, E19)
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
    figure when the log gives per-model times. The parameter files are in place before any timed call (items 39 and 51), so no
    download or extraction time can enter the call.
14. **Allowed download sources (answer 3).** The PDB entry 6IHB from RCSB; the AlphaFold parameter archive from the
    AlphaFold project's own storage address; Python wheels and source distributions through pip (the `lightdock` sdist and the
    build requirements pip fetches for it, item 59; the CUDA runtime wheels the `with_cuda` extra of item 58 brings, J2) and
    declared packages through apt. Each URL and sha256 recorded. Any other host is not allowed; a failed download stops the run
    (item 8). (revised, addendum 9)
15. **Auxiliary hours (answer 4).** aux_h_per_pair = per pair wall-clock hours of docking, interface analysis (contacts at
    4.5 A, interface residues, distance to the nearest threefold axis, site class) and writing the call-table row; installs,
    downloads and setup excluded; mean over the finished pairs (3 if all finish). One pip-installable docking code, name and
    version recorded.
16. **Storage (answer 4) (revised, addendum 6).** n_storage_gib = apparent bytes written for one grid run (AlphaFold outputs of
    one run; the whole per-pair docking output directory tree, with setup files, copied structures, swarm directories, rank tables
    and every pose file; the MD bytes: the trajectory file plus every log of the 0.5 ns segment, namely the engine rate
    (reporter) file, the tool's stdout and stderr logs and the worker's build and run JSON files), intermediates kept, x 216,
    / 2^30; the decision value. The MD worker writes the trajectory with OpenMM's `DCDReporter` every 5,000 steps (10 ps at 2 fs,
    50 frames), and `frame_interval_ps` is recorded on the MD row and in C4's values; the interval is not tuned toward the band.
    `system.xml`, `solvated.pdb` and any checkpoint are not in the decision value and are reported as `md_setup_bytes`. The
    record also carries the 432-run figure, the intermediates-deleted figure and MD bytes per ns (MD bytes over 0.5), as
    information. Planted: an `md_` directory with a 1,000-byte trajectory, a 100-byte reporter file, a 24-byte log, a 5,000-byte
    `system.xml` and a 7,000-byte `solvated.pdb` gives MD bytes 1,124 and `md_setup_bytes` 12,000; the worker source text names
    `DCDReporter`. (E6, E25, F3)
17. **MD protocol (answers 5, 10) (revised, addendum 5).** One docked complex per sampled pair, built as item 41 says: the pair's
    capsid-role chains merged with the top-ranked docking pose of the receptor, explicit solvent, water padding chosen so the
    atom count is inside 120,000 to 180,000; minimise, short equilibration, then a 0.5 ns production segment; one velocity seed
    (0). ns/day from the engine's rate line (the reporter file, item 41) and, separately, from production steps x timestep over
    the wall-clock of the production segment; the decision value is the median over complexes of the wall-clock figure; if the two
    disagree by more than 5 percent every ns/day is labelled "engine rate and wall-clock disagree" and both are reported. Atom
    count outside the range: C2 VOID, the range is not widened. The OpenMM release is the one of item 58, recorded as installed.
18. **Marginal rule (GATE_COMMIT instrument queue).** A value within 10 percent of a band edge (`edge x 0.9` to `edge x 1.1`) is
    decision VOID with `marginal: true`; the raw value is kept in `measured`.
19. **Non-A100 GPU (design, does_not_test).** If the GPU is not an A100 (instance fallback), C1 and C2 are VOID with the raw
    number kept and the label "not an A100"; C3 and C4 are still decided and labelled with the GPU.
20. **Controls first (answer 7) (revised, addendum 6).** After install: planted 60 s sleep (error at most 5 percent, else
    run_valid false, exit 2); empty-input run, which times the harness itself (the same timer, work-directory creation and
    record path as a real call, around a no-op command, with no AlphaFold, JAX, TensorFlow or docking import) and measures the
    bytes in the directory that call created (time under 2 s and bytes under 1 MiB, else the excess is subtracted from later
    values, only that harness overhead, and the label "setup overhead subtracted"); one unit-and-scale record, written after the
    controls and before any band comparison, which holds worked examples of the unit and scale conversions and says so: its
    `values.kind` is `"worked_examples"` and `values.raw_values_in` names the rows files that hold the raw AlphaFold seconds, the
    MD engine rate lines with the wall-clock ns/day beside them, and the raw bytes per artifact (those values cannot exist before
    the controls, so they are not copied into a second record). Planted: the record has both keys and `raw_values_in` names the
    AlphaFold, MD and storage rows files. (E7, F9)
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
    missed. `anchor_decision` never receives a missing pose. The docking steps and the recorded parameters are item 52.
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
    to 1,024; a planted docking tree with a nested swarm directory and a top-level `setup.json` sums every file (E25); the MD
    bytes case of item 16.
26. **Harness selftest (answer 13).** 62.9 s for the 60 s sleep passes; 63.1 s fails (run_valid false, exit 2); timings (1,800,
    1,830, 1,790) pass the spread check; (1,800, 1,800, 1,800) fails and gives C1 VOID with "zero spread across seeds: wrong
    variance source" while other inputs stand; relative SD 0.6 gives the label "seed spread high; mean is uncertain" only;
    empty run 0.5 s and 100 KiB pass, 5 s or 2 MiB trigger the subtraction label.
27. **Cost and time selftest (answer 14; revised, addendum 6).** 3,600 s at 1.99 gives 1.99; 7,200 s gives 3.98; with price
    1.99, budget 5, timeout 7,200 the guard stops at the time cap (5 / 1.99 h = 9,045 s is above it); with price 2.50 both caps
    coincide at 7,200 s; with 3.00 the dollar cap stops at 6,000 s; a stage whose estimated remaining time exceeds the time left
    is not started, the guard writes VOID (unmeasured) records for unfinished inputs, keeps finished ones, exits 3, and leaves
    run_valid as it was. The guard is called with an estimate (item 43). The gate-failure (void) path is also planted for: anchor
    miss, sleep failure, install failure, download failure, smoke-check failure. The stage flow itself (not only the functions)
    is planted in items 31, 47 and 48. The reported spend is item 53.
28. **Stage ceilings (GATE_COMMIT answer B8; revised, addendum 6 and addendum 7; restated as one requirement).** One table and one
    formula. Ceilings in seconds: install and downloads with the smoke check 1,800 (a running total); controls 700 and anchor 700
    (two stages with separate allowances; in practice the controls take about 70 s, so the pair uses about 770 s and the margin
    absorbs the 70 s); per-pair docking and analysis 600 in total, at most 250 per pair; AlphaFold 2,000; MD 1,600, at most 600 per
    complex; endpoints 100; margin 400. The ceilings of the seven slots sum to 7,200; that sum is not the guarantee. The guarantee
    is the allowance: `allowance(stage) = max(0, min(ceiling(stage), REMOTE_TIMEOUT - elapsed_since_T0 - 400 - 100))`, and a stage
    whose allowance is below its first unit's estimate (item 43) is not started. Install, in `run_m4.py`: every pip, download,
    extraction and smoke-check call is run under `timeout -k 10 <limit>` with `limit = min(its own limit, 1,800 - install seconds
    used, allowance)`; exhausting the total, or any call over its limit, is exit 2 (item 8), never 3. Every apt call in
    `onbox_m4.sh` is bounded by `min(its own limit, 1,800 - install seconds used)`; the third term, `REMOTE_TIMEOUT - elapsed -
    500`, is not required of the shell (revised, addendum 7: it cannot bind at `REMOTE_TIMEOUT=7200`, which both launches use);
    `apt-get update` may retry (at most 10 tries, 15 s apart), each try under its own `timeout`, the whole loop at most 300 s (F7).
    The build of the `lightdock` sdist (item 59) runs inside the pip call and so inside the install total, as do the CUDA runtime
    wheels of item 58. Docking: a pair that reaches 250 s is kept as a row with `truncated: true`, is not counted in the mean, and
    the loop continues with the next pair until the stage allowance is gone (F4); C3 is decided if at least 2 pairs finished, else
    VOID. A later stage that hits its ceiling stops and its unfinished inputs are `unmeasured_by_stop`. Planted: `allowance` with
    REMOTE_TIMEOUT 7,200 gives install 1,800 at elapsed 0, AlphaFold 700 at elapsed 6,000 (7,200 - 6,000 - 500) and 0 at elapsed
    6,800 (clamped, not negative, stage not started); install calls with limits 1,000, 1,000 and 1,000 get 1,000, 800 and 0 (the
    third is not started and the stage is exit 2); docking with pair 1 capped and pairs 2 and 3 finished attempts all 3 pairs, n=2,
    C3 decided, and with pairs 1 and 2 capped attempts all 3, n=1, C3 VOID. (E2, F4, F7, F8, F20, G2)
29. **Gate-failure and guard-stop paths (answers 8, 13, 14; revised, addendum 6; restated as one requirement).** A stop is exactly
    one of: guard refusal to start a stage or unit, a stage ceiling, a tool call exceeding its allowance, the outer timeout. A
    failure (exit 2) and an anchor miss (exit 4) are not stops. When a stop happens, all six hold, and each has a planted flow in
    item 31 or 48: (1) the stage that stopped is not in `stages_done`, even when it returned normally; (2) the inputs it left
    unfinished are `unmeasured_by_stop:<kind>` and their records are VOID with the full incomplete-run label (item 35), while every
    input already decided keeps its decision and its record; (3) `run_valid` is not changed, and the stop never sets it false;
    (4) a timed-out tool's row is kept with `incomplete: true` and is not counted in a mean; (5) later stages whose own guard
    allows still start, and `stage_endpoints` always runs (a stop in docking continues with the next pair, F4); (6) the exit is 3
    if at least one input is `unmeasured_by_stop` at the end, else 0. Each early return in `stage_af2`, `stage_aux` and `stage_md`
    raises `GuardStop` or records the stop in run state that `run_stages` reads. `fail_stage` sets `run_valid` false only for
    exit 2 and 4. After an outer timeout `--finalize` follows item 49. Planted: flows (b), (c), (d), (i), (j) of item 31 and the
    finalize and shell flows of items 48 and 49. (B1, B2, B3, E17, E22, F2, F4, F20)
30. **Summary and spread (answers 5, 6; revised, addendum 5).** `m4_summary.json` is written without `sort_keys` and its first
    key is `what_this_run_decides`, stating that the run decides the stand-in protocol only; it then restates every record, the
    gate result and the fallback text (item 11); carries no decision of its own; carries the label "seed spread high; mean is
    uncertain" for any pair with relative SD over 50 percent; and carries the full "incomplete run" label after an early stop. No
    relaunch is made for spread. Selftest reads the written file as text and checks the first key. (E9)
31. **Stage-flow selftest (new, addendum 3, B15; revised, addendum 6 and addendum 8).** `run_stages` takes its stage functions and
    tool runner by injection; the selftest runs the whole flow with fakes and asserts exit code, run_valid, per-input decisions,
    labels and the `RUN_DONE` status strings of item 8 for: (a) all stages finish: exit 0, run_valid true; (b) a time-guard stop
    in AlphaFold after 2 of 9 runs: exit 3, run_valid true, C1 VOID with raw rows kept, C2 to C4 decided; (c) a tool timeout in MD
    on the third complex: exit 3, run_valid true, C2 decided on n=2, others untouched; (d) a ceiling stop in docking: exit 3, C3
    decided on the finished pairs or VOID below 2; (e) a real tool failure: exit 2, run_valid false, all undecided inputs
    `void_by_failure`; (f) anchor miss: exit 4, run_valid false, C1 to C4 `void_by_anchor_miss`; (g) sleep failure: exit 2; (h)
    install, smoke-check and download failure: exit 2, with an anchor VOID record "anchor stage not reached" present (item 54);
    (i) the outer-timeout route (rc 124): exit 3, run_valid true. Addendum 5 adds: (j) docking timeout in the anchor: exit 3,
    anchor undecided; (k) docking with no parsable pose: exit 2, run_valid false; (l) not-an-A100 or zero spread with no stop:
    exit 0 with the VOIDs.
32. **Process groups and outer timeout (new, addendum 3, B12; revised, addendum 6).** Every tool call (colabfold, the docking
    code, the OpenMM worker) runs in its own process group and a timeout kills the group; when the outer `timeout` on
    `run_m4.py` returns 124, or 137 with elapsed time since T0 at least the outer deadline minus 5 s, `onbox_m4.sh` kills the
    recorded process groups, runs `run_m4.py --finalize` (item 49) before the endpoints stage's records are final, and routes the
    outcome as a guard stop, exit 3, not as `fail`/exit 2; rc 137 earlier than that is a failure (exit 2). The route is written
    so that `set -e` cannot abort it: the `--finalize` call and the outer `timeout` call are `RC=0; ... || RC=$?` (item 48).
    Each pgid is recorded with its leader's `/proc/<pid>/stat` start time and command name, removed when the tool returns, and
    signalled only if the leader is alive and both still match (a skipped entry goes to the log). The inner tool timeout is at
    least 100 s shorter than the outer kill (outer kill = stop_at minus elapsed minus 600; inner = stop_at minus elapsed minus
    700) so the inner fires first; an outer firing is itself a recorded event. Selftest: a planted tool that sleeps past its
    allowance is killed with its child and the result is a ceiling stop; planted rc 137 at the deadline gives exit 3, at 100 s
    exit 2; a stale pgid entry with a different start time is not signalled; the shell-level rc 124 flow of item 48. (E23, F1)
33. **Smoke check in the install stage (new, addendum 3, B6; revised, addendum 6, addendum 7, addendum 8 and addendum 9).** After
    every install and inside the 1,800 s install ceiling: import of the AlphaFold-Multimer stack and JAX with a GPU device listed;
    `colabfold_batch --help`; the docking code's entry point `--help` and its conformation-generating script's `--help` (item 52);
    OpenMM imported with `Platform.getPlatformByName("CUDA")` succeeding; and each tool resolved by `shutil.which` against the venv
    PATH with its absolute path recorded (item 38). A failure is exit 2 with a void record before any GPU stage. Every package is
    pinned in the install line as `name==version` (extras in brackets allowed, except for OpenMM; the one extra of item 58 is on
    the JAX CUDA plugin). The OpenMM requirement is two pinned entries, the plain `openmm` distribution and a sibling whose
    distribution name starts `openmm-cuda`, as a pair that resolves together; a bracketed extra on the OpenMM entry is not
    accepted. Which pair, and from what evidence, is item 58 (the pair `openmm==8.2.0` with `openmm-cuda==8.1.1.12` of build 10 and
    build 11 failed to resolve in launch 1 and in the operator's resolve, and is withdrawn). Which form was chosen is stated in a
    comment on `PIP_PINS`, with the evidence files' names. colabfold takes the form whose metadata carries what the smoke check
    imports, with a JAX build compatible with the pinned `colabfold`, without substituting a tool. The smoke check decides in the
    box; the operator's joint resolution (item 66) decides before build 14 and again before launch 2. No trial docking is run in
    the install stage. Planted: a `PIP_PINS` parser case in which the OpenMM requirement has an `openmm-cuda*` sibling passes, an
    OpenMM entry carrying a bracketed extra fails, an entry without `==` fails the selftest, and the pair rule of item 58 holds.
    (E12, E13, F6, G1, H1, J1, J2)
34. **Downloads recorded in full (new, addendum 3, B13; revised, addendum 5).** pip installs run with `--report`; the report (URL
    and archive hash of each wheel or sdist) is kept under `results_m4/out/` and its sha256 is cited in every record's `inputs`
    (E24); each apt package is recorded with version and the SHA256 from `apt-cache show`; the direct downloads keep URL and
    sha256; the pip bootstrap of item 50, when it runs, is recorded the same way.
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
    Launch 1 confirmed it: the summary shows `remote_timeout_seen_s` 7200.0 and `remote_timeout_forwarded` true. (revised, addendum 8)
38. **Tools resolve through the venv (new, addendum 5, E1, E12, E14).** `onbox_m4.sh` exports `PATH="${VENV}/bin:${PATH}"` before
    the first stage; `run_m4.py` builds `child_env` with the venv bin directory (taken from `sys.executable`'s directory) first
    and calls `colabfold_batch`, `lightdock3.py`, `lightdock3_setup.py` and `lgd_*` by absolute venv path where it can; an
    unresolved tool is exit 2 in the install stage. `python3-venv` is a declared apt package; the venv's bundled pip is used,
    after the item 50 check. Selftest: a planted venv directory with an executable stub resolves through `child_env`, not through
    the bare inherited PATH.
39. **Parameter archive extracted, no download in a timed call (new, addendum 5, E3).** The install stage verifies the AlphaFold
    parameter archive's sha256 (recorded), extracts it into `<data>/params`, the same `--data` directory colabfold is given,
    writes the completion marker(s) of item 51, and verifies the multimer parameter files for the 5 models are present before the
    smoke check ends; missing is exit 2. Extraction time is install time, never C1 time. A timed call whose log shows a download
    or extraction gets `download_in_timed_call: true` on its row, is not counted, and C1 is VOID "download inside timed call".
    Selftest: a planted archive extracts to the expected layout; a planted "Downloading" log line sets the flag.
40. **Stand-in pair checks and evidence (new, addendum 5, E4).** After building the pairs, assert: each total length in 750 to
    1,000; the three sequences pairwise different; the three lengths pairwise at least 20 residues apart; one capsid-role set and
    one receptor-role set per pair. More than one copy of a capsid chain may be used to reach the range; if the range or the
    spread still cannot be met, exit 2 with a void record naming the assertion; no silent clamp of `want_cap`. Write
    `results_m4/out/pairs_tag-m4.json` (chain ids and role mapping, sequences, lengths, sha256 of each pair's FASTA and PDB file)
    and copies of the three FASTA files into `results_m4/out/`; each C record cites that file's hash in `inputs`. Selftest: a
    planted short capsid chain fails the range; equal-length pairs fail the spread; planted good pairs pass and the evidence file
    parses.
41. **MD on the merged complex; engine rate file parsed (new, addendum 5, E5, E6; revised, addendum 6).** The MD input is the
    pair's capsid-role chains from the stand-in pair file merged with the top-ranked docking pose of the receptor, one
    structure, chain roles preserved; assert both roles present and a nonzero capsid heavy-atom count before solvation, else exit
    2. Water padding is estimated from the solute's extent so the built system has 120,000 to 180,000 atoms, verified on the built
    system, one rebuild allowed inside the complex's 600 s; if it cannot be met, C2 VOID with the atom count kept. The worker's
    StateDataReporter file is copied to `results_m4/out/` and is the file parsed for the engine's ns/day (the tool's stdout log is
    not); a rate file with no parsable rate line gives `engine_ns_per_day: null` and the label "engine rate line missing" and C2
    still rests on the wall-clock figure. The worker also writes the DCD trajectory of item 16. Selftest: a receptor-only pose
    is refused; a merged complex passes the role check; a planted reporter file in its real column layout parses; one without a
    rate line gives null and the label; 129 against 100 fires the disagreement label.
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
    any JAX or colabfold cache variable the build sets point under `~/m4_run/`. The frozen bootstrap's `~/.local` installs (and
    the warnings they print) are the operator's and are not the build's to change (H7).
46. **Exit-code vocabulary in `RUN_DONE` (new, addendum 5, E22; revised, addendum 6).** `RUN_DONE` carries the exit code and, per
    input C1 to C4, exactly one status of the item 8 table: `decided`, `void_by_rule:<reason>`, `unmeasured_by_stop:<stop kind>`,
    `void_by_anchor_miss` or `void_by_failure:<kind>`, so A2(a), A2(b) and A2(c) are readable from it alone. After exit 4 no input
    is `unmeasured_by_stop`; each voided record also carries `voided_by`. Planted: the anchor-miss and failure flows of item 31
    assert the strings. (F16)
47. **The selftest runs the real stage bodies (new, addendum 5, E28; binding; revised, addendum 6).** Besides the injected-fake
    flows (item 31), the selftest runs the real `stage_*` bodies with the tool runner, clock and filesystem roots injected and
    fake tool executables in a planted venv bin directory (stdlib only, no GPU, no network, still under 300 s). It asserts at
    least: tools resolve through the venv PATH (item 38); the parameter directory is populated, with its marker file(s), before a
    timed call (items 39, 51); the pair assertions (item 40); the MD input holds both chain roles, the reporter file is parsed and
    the trajectory and `frame_interval_ps` are recorded (items 41, 16); the empty-run control times the harness (item 20); the
    three docking failure routes (item 21) and the docking call order simulate, generate, rank (item 52); the pair loop continues
    past a capped pair (item 28); the install total ceiling (item 28); the pip version branch (item 50); the spend arithmetic
    (item 53); and the first key of `m4_summary.json` (item 30).
48. **Shell-level routing, bounded apt, and the test hook (new, addendum 6, F1, F5, F7, F17; revised, addendum 7).** In
    `onbox_m4.sh`: (a) no command whose non-zero status is an expected outcome (`run_m4.py`, `run_m4.py --finalize`, the outer
    `timeout`, the process-group kill helper) is run bare under `set -e`; each is `RC=0; <command> || RC=$?` and the route table
    reads `RC`; the EXIT trap acts only while `FINISHED=0`, and every normal route sets `FINISHED=1` before its own `exit`. (b)
    `write_minimal_void <code>` writes run_valid false for code 2 and 4, run_valid true for code 3 unless an existing
    `RUN_VALID.json` says false (then false is kept), and is never called with 0; it is called only when the runner has not
    written `RUN_DONE`; when the runner wrote `RUN_DONE` and `RUN_VALID.json` the shell rewrites neither, and its exit code equals
    the `RUN_DONE` code; a runner that returns 0 with no `RUN_DONE` is treated as code 2. The "no time left after setting up"
    route is code 3, run_valid true. The per-input statuses it writes follow item 55. (c) Every apt call is bounded as item 28
    says (revised, addendum 7: its own limit and the 1,800 s install total; the `REMOTE_TIMEOUT` term is not required of the
    shell). (d) Test hook: one block in `onbox_m4.sh` between the lines `# BEGIN TEST HOOKS` and `# END TEST HOOKS`, whose first
    line tests `M4_SHELL_TEST`, is the only place `M4_TEST_*` variables are read. When `M4_SHELL_TEST=1`, `M4_TEST_ROOT`
    replaces `~/m4_run`, `M4_TEST_RUNNER` replaces the python runner command (and its `--finalize` form receives `--finalize` as
    an argument), `M4_TEST_INSTALL_CEILING_S` replaces 1,800, and `M4_TEST_BIN` is put first on PATH; the venv step, pip installs,
    downloads and the GPU check are skipped, and the apt steps run through whatever `sudo` the test PATH supplies. Without
    `M4_SHELL_TEST=1` nothing changes. The selftest checks the block markers and that every `M4_TEST_` occurrence lies between
    them, then runs `bash onbox_m4.sh` through `subprocess` in a temporary root (a missing `bash` is a FAIL) for these planted
    flows, each asserting the script's exit code, the content of `RUN_VALID.json` and `RUN_DONE`, and which files were left
    untouched: runner stub rc 0 with its own `RUN_DONE` 0 and `RUN_VALID.json` true: exit 0, both files byte-identical to the
    stub's; rc 3 with its own files: exit 3, files untouched (the trap did not run); rc 3 with no files: exit 3, run_valid true,
    full incomplete-run label; rc 4 with no files: exit 4, run_valid false; rc 2: exit 2, run_valid false; rc 0 with no
    `RUN_DONE`: exit 2; rc 124 at the deadline: the finalize stub is called once and the exit is 3; rc 137 at 100 s: exit 2;
    `REMOTE_TIMEOUT=10`: exit 3, run_valid true; a stub `sudo` that sleeps 60 s with `M4_TEST_INSTALL_CEILING_S=3`: exit 2 within
    30 s with the void record present; a static check that no line invoking the runner lacks `|| RC=$?`; and the two flows of
    item 55. Still no GPU and no network; the whole selftest under 300 s.
49. **`--finalize` rebuilds status from disk (new, addendum 6, F2, F17).** `run_m4.py --finalize` builds its `RunState` from
    `results_m4/out/`, not fresh: for the anchor and each C<i> it reads the record, and a record with decision PASS or FAIL, or
    VOID with `marginal` or a rule reason, is `decided` or `void_by_rule` and is never rewritten (byte-identical afterwards); a
    missing record, or one that carries `LABEL_UNMEASURED`, is `unmeasured_by_stop:outer_timeout`; `run_valid` is false if
    `RUN_VALID.json` or any record says false, else true; a FAIL anchor record gives exit 4, `run_valid` false without a FAIL
    anchor gives exit 2, otherwise exit 3 when at least one input is unmeasured and 0 when none is. Finalize writes only the
    missing records, `m4_summary.json`, `RUN_VALID.json` and `RUN_DONE`, all with the full incomplete-run label when exit is 3.
    Selftest: a planted output directory with a decided C3 record and no other record gives C3 `decided` (record unchanged), C1,
    C2 and C4 `unmeasured_by_stop:outer_timeout`, run_valid true, exit 3; a directory with a FAIL anchor gives exit 4; a directory
    with all four decided gives exit 0.
50. **Recorded pip bootstrap (new, addendum 6, F14).** Before the first pinned install, read `pip --version` of the venv: pip 22.2
    or later proceeds directly; an earlier pip runs one bootstrap inside the install total: `pip download pip==24.0 --no-deps`
    into a directory under `~/m4_run/` with the verbose log kept, the wheel's sha256 computed by the runner, URL (from the log),
    sha256 and seconds written to the downloads file, then that local wheel installed with `--no-index`; every later install
    uses `--report`. No other pip upgrade. An unparsable version string is exit 2. Selftest: "pip 22.0.2 from ..." selects the
    bootstrap, "pip 23.0.1 from ..." does not, a garbage string is exit 2, and the recorded bootstrap entry has URL, sha256 and
    seconds.
51. **Parameter completion marker (new, addendum 6, F12).** After extraction (item 39) the build opens the installed colabfold's
    own download module (the Python source file under the venv's package directory), reads the completion-marker file name(s) it
    checks, writes exactly those marker file(s) into `<data>/params`, and records the names it found; if the module names no
    marker it writes none and records "no marker named". Marker names are never hard-coded from memory. Selftest: a planted
    module source naming one marker yields that file; naming two yields both; naming none yields none and the record.
52. **Docking steps and parameters (new, addendum 6, F13).** The docking sequence for the anchor and for every pair is: simulate,
    then the docking package's conformation-generating script, then `lgd_rank.py`, unless `frozen/ONBOX_CONTRACT.md` states a
    different order, in which case the contract's order is followed and recorded in the anchor record
    (`values.docking_order`). The swarm count and other docking parameters are the same for the anchor and the pairs, are written
    to the anchor record as `values.docking_parameters`, and are not restrained toward the published 6IHB interface. A missing
    pose file stays exit 2 (item 42); an anchor miss with a pose obtained and compared stays exit 4. Selftest: the fake
    docking tool records its call order and it is simulate, generate, rank; a fake that skips generation gives exit 2 (no pose
    file); the anchor record has `docking_parameters` and `docking_order`.
53. **Spend report (new, addendum 6, F10).** `estimated_spend_usd` = seconds since T0 x `PRICE_USD_PER_HOUR` / 3,600; the pre-T0
    seconds are reported beside it and not added (T0 already includes the bootstrap, item 44). Selftest: 3,600 s since T0 with 300
    s pre-T0 gives 1.99 (not 2.16), and 7,200 s gives 3.98.
54. **The shell's and the runner's void records carry the rule-6 keys (new, addendum 6, F11; revised, addendum 7 and addendum
    8).** The shell's minimal void (item 8, row 1, and the code-3 route of item 48) writes `env.txt` (named non-secret variables,
    including the `REMOTE_TIMEOUT` seen), `m4_summary.json` (first key `what_this_run_decides`), an anchor record and C1 to C4
    records each with the provenance.py keys, `values.measured` null, `values.unit`, `values.card_value`, `values.band`, `decision`
    VOID and `run_valid` per item 48(b), plus `RUN_VALID.json` and `RUN_DONE`; a record that already decided on disk is not written
    again and is not shown as void (item 55). It writes through `frozen/provenance.py` when that imports under the system
    `python3` (stdlib), else by hand with the same keys. The runner does the same on every exit-2 and exit-3 path it ends
    on: launch 1's runner wrote C1 to C4 and no anchor record, so the runner also writes
    `endpoint-anchor_tag-m4.json` as a VOID record with `run_valid` as the run has it, `measured` null with
    `null_reasons.measured` "anchor stage not reached" when the anchor was not run, `published`, `tolerance` and the keys of item 3
    (H5). Selftest: the item 48 flows read these files and check the keys; the install-failure flow of item 31 (h) asserts the
    anchor record exists with them.
55. **The shell's void path keeps decided inputs decided (new, addendum 7, G4).** When `write_minimal_void` runs (the runner
    died or never started, so no `RUN_DONE`), it first reads each C<i> record already on disk. A record with decision PASS or
    FAIL, or VOID with `marginal` or a rule reason, is `decided` or `void_by_rule:<reason>` in `RUN_VALID.json`
    `inputs_status`, in `RUN_DONE` and in the summary the shell writes if none exists, and is never rewritten. Only an input with
    no such record is `void_by_failure:<kind>` (code 2) or `unmeasured_by_stop:<kind>` (code 3), as item 8 says; code 4 stays
    `void_by_anchor_miss` for all four. The exit code and `run_valid` are exactly those of item 48(b); only the per-input
    status changes. Planted, two shell-level flows of item 48: a runner stub that writes a decided C3 record and exits 2 with no
    `RUN_DONE` gives exit 2, `run_valid` false, C3 `decided` with its record byte-identical, and C1, C2, C4 `void_by_failure`;
    the same stub exiting 3 gives C3 `decided` and C1, C2, C4 `unmeasured_by_stop`.
56. **Contract and directive precedence (new, addendum 7, G3).** Where `frozen/ONBOX_CONTRACT.md` differs from items 8, 20, 43
    and 46, these items win, by a ruling of record of the gate: exit codes are 0, 2, 3 and 4 (no exit 5); the runner and the
    shell write `RUN_DONE` (items 8, 48); the guard uses the estimate floors of item 43 and no timed dry run on the real input;
    the per-run environment file is `env.txt` and no `env_<tag>.json` is required. Every other contract item (stage order,
    guards, record fields, selftest contract, failure checks) stays binding. Review checks against the contract with this item
    applied and does not cite these four points. No build change.
57. **Build 10 scope (new, addendum 7, G6; superseded by item 61, addendum 8, and then by item 65, addendum 9).** Build 10 was an
    in-place edit of build 9 limited to the OpenMM change to `PIP_PINS` (item 33), the `write_minimal_void` change (item 55) and
    their selftest cases. It is built (selftest 677 of 677) and ran as launch 1. Its `PIP_PINS` pair was wrong (item 58);
    everything else in it is accepted as it ran, including the void path (H5). (revised, addendum 9)
58. **The pins of record (new, addendum 8, H1; replaced in full, addendum 9, J1, J2).** `PIP_PINS` carries exactly these nine
    entries, in this order, each `name==version` (the bracket on the JAX CUDA plugin is the only extra):
    `jax==0.4.35`, `jaxlib==0.4.35`, `jax-cuda12-plugin[with_cuda]==0.4.35`, `jax-cuda12-pjrt==0.4.35`, `colabfold==1.5.5`,
    `alphafold-colabfold==2.3.6`, `openmm==8.1.1`, `openmm-cuda==8.1.1.12`, `lightdock==0.9.4`.
    The OpenMM pair `openmm==8.1.1` with `openmm-cuda==8.1.1.12` replaces build 10's and build 11's `openmm==8.2.0` pair; it is the
    gate's inference (pip refuses `openmm-cuda==8.1.1.12` beside `openmm==8.2.0`; the sibling's version reads as OpenMM 8.1.1),
    not a verified fact, and the test of item 66 on exactly this list decides before the build is made. The `[with_cuda]` extra is
    the JAX project's own GPU install form (it brings the CUDA runtime libraries from the package index) and is also an inference
    tested by item 66. No other name, version or extra is written; no source build of `openmm`; no conda or other non-pip route; no
    `OpenMM-CUDA-12`, `OpenMM-CUDA-13` or `openmm-unofficial-*` distribution; no operator file is read to choose a pin (item 67).
    The comment on `PIP_PINS` says: the OpenMM pair and the extra are the gate's inference (addendum 9, J1 and J2); the sources are
    `out/gate_report_build13.md` and the pip outputs `out/pip_pins_resolve_build11.txt` and
    `out/launch1/results_m4/out/tool_logs/install_pip_install.log`; the test of record is item 66. The OpenMM release is not fixed
    by the design: the installed versions of `openmm` and `openmm-cuda` are recorded (item 6, item 60). Selftest (item 64): the
    parser case. (J1, J2) (revised, addendum 9)
59. **Declared apt packages and the sdist build (new, addendum 8, H2).** `lightdock==0.9.4` has no wheel for CPython 3.10 Linux
    x86_64 and is built by pip from its sdist inside the venv. `onbox_m4.sh` therefore declares exactly five apt packages,
    `python3-venv aria2 curl build-essential python3-dev`, installed in the one declared apt call with the bounds of item 28, each
    recorded with version and the SHA256 from `apt-cache show` (item 34). pip builds the sdist with its default build isolation
    (the build requirements come through pip from the index); the pip report records the sdist's URL and hash. No
    `--no-build-isolation`, no other compiler package, no second source; a failed build is exit 2 (item 8). The smoke check of item
    33 decides that the built package works. Selftest: the apt list parsed from the shell's text equals those five names exactly;
    a sixth name, or a missing one, fails. (H2)
60. **Engine versions come from the install, never from a default (new, addendum 8, H3).** Launch 1's void records named
    `jax_version`, `jaxlib_version` and `jax_cuda_plugin_version` "0.6.0" and `cuda_plugin_version` "0.6.0" although the pins are
    0.4.35 and nothing installed. The build reads each of these (and the OpenMM, docking and wheel-build-tag values) only from the
    pip report of this run or from the installed distribution's metadata after the install; a value that cannot be had is null with
    a non-empty `null_reasons` entry ("not installed: the install stage failed" on a void path). No constant stands in as a
    default. Selftest: a planted pip report naming `jax 0.4.35` gives `jax_version` "0.4.35" in a C record; a planted failed-install
    state gives null with a reason for each of the four keys. (H3)
61. **Build 11 scope (new, addendum 8, H10; superseded by item 65, addendum 9).** Build 11 was an in-place edit of build 10's
    `run_m4.py` and `onbox_m4.sh`, limited to the `PIP_PINS` pair and comment, the declared apt list, the engine and plugin version
    labels, the anchor VOID record on the runner's exit-2 and exit-3 paths and their selftest cases. It is built (selftest 740 of
    740, per the operator); build 13 is identical to it (J5). Build 14 is bounded by item 65, not by this item. (revised,
    addendum 9)
62. **Launch 2 is the last, and what stands before it (new, addendum 8, H4, H9; revised, addendum 9, J7).** Launch 1 ended with exit
    2 at the pip install step, USD 0.30, nothing decided. Launch 2 is authorised on A2(a) only if all five hold: (i) build 14
    exists and its selftest passes with the two sha256 values matching the files on disk (item 36); (ii) the operator's `diff` of
    build 14 against build 11 shows only the lines of item 65's list, and a review of that diff reports zero blocking findings,
    had `frozen/ONBOX_CONTRACT.md` on its read list with item 56 applied, and states the diff is limited to item 65; (iii) the
    second run of the test of item 66, on build 14's own `PIP_PINS`, passed and is in RUN.md and `out/pip_pins_resolve_build14.txt`
    (an index check that only tests that each release exists is not enough); (iv) the launch environment is unchanged (Box); (v)
    the cause is recorded in RUN.md. No third launch exists; a second failure ends the run as unmeasured and what follows is the
    owner's decision. Total spend if launch 2 runs to its caps: 0.30 + 4.31 = USD 4.61, under the USD 10 cap. (J7) (revised,
    addendum 9)
63. **Why build 14 exists (new, addendum 9, J5).** Build 11 and build 13 left `PIP_PINS` unchanged because the operator file
    `out/pip_pins_openmm_cuda_requires.txt`, which the directive told them to read, held the `lightdock` listing and no `openmm-cuda`
    metadata; the file branch of the old item 58 is withdrawn. The build does not look for that file and does not branch on any
    operator file. The build's return states that the pins are those of item 58, taken from this note. No finding is raised against
    builds 11 and 13 for it. (J5)
64. **Selftest case for the pins (new, addendum 9, J1, J2).** The `PIP_PINS` parser case of items 33 and 58 asserts: the list equals
    the nine entries of item 58 in that order; the `openmm` pin's version (8.1.1) equals the version quoted in the comment as the
    one `openmm-cuda` requires; a bracketed extra on `openmm` is rejected; an entry without `==` is rejected; an `openmm-cuda*`
    entry without a plain `openmm` entry is rejected; the bracketed extra on `jax-cuda12-plugin` is accepted and is the only extra in
    the list; the planted good pair is accepted. The selftest's count and the two hash lines move (build 11: 740 of 740). (J1, J2)
65. **Build 14 scope (new, addendum 9, J6; supersedes item 61).** Build 14 is an in-place edit of build 11's `run_m4.py` and
    `onbox_m4.sh` (build 13's files are identical), limited to: the nine `PIP_PINS` entries and their comment (item 58); the
    selftest's `PIP_PINS` parser case (item 64); the selftest's count and hash lines, which move. Every other line stays as build 11
    has it; nothing is refactored, renamed or reordered. It uses no network and reads no operator evidence file. The build's return
    states the real line counts, the two sha256 values (item 36), the new selftest count and the exact lines changed. A changed
    line outside this list is a blocking finding in review. Build 14 is started only after the first run of the item 66 test
    passed. (J6, J7)
66. **The test of record, and when it runs (new, addendum 9, J4; operator's check, listed so the build and review rely on it).**
    Pip's dry-run resolution in a real CPython 3.10 with sdists allowed, in three steps, in one clean CPython 3.10 Linux x86_64
    virtual environment with no GPU and no packages beyond pip. T0: install `pip==24.0` and record `pip --version` (the pip the box
    uses after item 50). T1: `python -m pip install --dry-run --ignore-installed --report out/pip_pins_resolve_build14.json` over
    the nine requirements of item 58 as nine arguments in order; passes only if the exit is 0, the report's `install` list has each
    of the nine distributions at its stated version, `jaxlib`, `jax-cuda12-plugin`, `jax-cuda12-pjrt`, `openmm` and `openmm-cuda`
    each resolve to a `.whl` URL, an `nvidia-cudnn-cu12` entry is present, no output line contains `ResolutionImpossible`,
    `conflicting dependencies` or `does not provide the extra`, and only `lightdock` may be a `.tar.gz`. T2: `python -m pip wheel
    --no-deps --wheel-dir <empty directory> lightdock==0.9.4` with `build-essential` and `python3-dev` present; passes if it exits 0
    and leaves a `lightdock-0.9.4-*.whl`. T1 and T2 run first on the item 58 list before build 14 starts, and again on the lines
    read from build 14's `PIP_PINS` (text-identical to item 58's, checked by `diff`) before launch 2; results go to RUN.md and
    `out/pip_pins_resolve_build14.txt`. Failure of either run means no build (first run) or no launch (second run) and the gate
    rules again; the build never edits pins by hand (F6). The test does not prove the CUDA platform or the JAX GPU device load:
    only the smoke check on the box does (item 33). (J4, J7, J9)
67. **Evidence files are not build inputs (new, addendum 9, J5).** The files `out/pip_pins_check_build9.txt`,
    `out/pip_pins_check_build10_platform.txt`, `out/pip_pins_check_build11.txt`, `out/pip_pins_openmm_listing.txt`,
    `out/pip_pins_openmm_cuda_requires.txt`, `out/pip_pins_resolve_build11.txt`, `out/gate_report_launch1.md` and
    `out/gate_report_build13.md` inform the gate and the operator; build 14 does not read them (the comment of item 58 names
    them as sources only). Selftest: a static check that neither `run_m4.py` nor `onbox_m4.sh` opens a path under `out/pip_pins_`
    or `out/gate_report_`. (J5)

## Box

- Instance: `gpu_1x_a100_sxm4` (A100 SXM4 40 GB, USD 1.99/h) in us-east-1 if it has capacity; else the cheapest single GPU
  with capacity at no more than USD 2.50/h; the operator records which. Launch 1 ran on `gpu_1x_a100_sxm4` (A100-SXM4-40GB,
  driver 570.148.08, CUDA 12.8, python 3.10.12).
- Launcher (revised, addendum 6): the operator's per-launch copy `lambda_run_m4.sh` (made from `frozen/lambda_run.sh` at the
  header's declared points only; the header declares the four added variables, any added fetch line, such as the one for
  `results_m4/out/RUN_VALID.json`, and the changed `REMOTE_TIMEOUT` default of 7200): remote dir `m4_run/`; payload `run_m4.py
  onbox_m4.sh remote_run_m4.sh frozen/provenance.py` and `data/` recursively if it exists; forwarded env `PRICE_USD_PER_HOUR
  BUDGET_LEFT_USD REMOTE_TIMEOUT INSTANCE_TYPE`; fetch from `m4_run/results_m4/out/`. `remote_run_m4.sh` is
  `frozen/remote_run.sh` with only its `cd` line changed to `~/m4_run`; its bootstrap time is counted by the build (item 44).
  Both files stay as launch 1 used them (H8).
- Caps (revised, addendum 7 and addendum 8): `REMOTE_TIMEOUT=7200` exactly for both launches (a smaller value is not authorised,
  G2); `BUDGET_LEFT_USD=5` per launch; `PRICE_USD_PER_HOUR=1.99` (the chosen instance's price, at most 2.50, on the fallback); two
  launches at most within USD 10, of which one is spent (USD 0.30) and one remains (item 62).
- Before build 14 and again before launch 2 the operator runs the test of item 66 (the nine pins of item 58 resolved jointly with
  pip 24.0, and the `lightdock` sdist built into a wheel) and writes the results into RUN.md and
  `out/pip_pins_resolve_build14.txt`; this supersedes the existence check, which tested each pin alone. (revised, addendum 9)
- Payload layout on the box: `~/m4_run/run_m4.py`, `~/m4_run/onbox_m4.sh`, `~/m4_run/frozen/provenance.py`, `~/m4_run/data/...`
  if shipped. Results under `~/m4_run/results_m4/out/`.
- The build's `onbox_command` is a single line the operator runs verbatim on the box through `remote_run_m4.sh`
  (`bash remote_run_m4.sh bash onbox_m4.sh`).

## Local selftest (revised, addendum 9)

`python3 run_m4.py --selftest` is stdlib-only and runs under `timeout 300`: no GPU, no network. It covers every parser
(engine rate line and reporter file, MD log and production wall-clock, AlphaFold timing rows, docking rank and contact tables,
byte counts, nvidia-smi labels including the CUDA version header, pip report, pip version string, `etimes`, the colabfold marker
names), the marginal rule, the planted cases of items 21 to 27, the stage-flow cases of item 31, the real-stage-body cases of
item 47, the shell-level flows of items 48 and 55 (it runs `bash onbox_m4.sh` under the test hook), the finalize flows of item
49, the process-group kill of item 32, the child-environment and venv-PATH cases of items 5 and 38, the `PIP_PINS` case of
items 33, 58 and 64 (the nine entries, the pair rule, the single extra), the declared-apt-list case of item 59, the
engine-version sourcing case of item 60, the anchor VOID record case of item 54, the incomplete-run label of item 35, the void
path of items 8 and 29, the label-key check of item 6, the no-evidence-file-read check of item 67, record writing through
`frozen/provenance.py`, and the file-hash line of item 36. No local tool run (no AlphaFold, docking or MD) and no pip
resolution (that is the operator's check, item 66). Build 11's count was 740 of 740; build 14's is the same or higher by the cases
of items 64 and 67.

## What the runner writes (`results_m4/out/`) (revised, addendum 8)

- `endpoint-anchor_tag-m4.json` and `endpoint-C1_tag-m4.json` to `endpoint-C4_tag-m4.json`, plus one provenance.py record
  for each control (60 s sleep, empty run, unit-and-scale), each with `cell`, `inputs` with hashes, `metric`, `values`,
  `threshold`, `decision_rule` written before values, `decision`, `run_valid`; the labels of item 6 with versions taken from the
  install (item 60); the anchor's `docking_parameters` and `docking_order` (item 52). On an exit-2 or exit-3 end the anchor record
  is written even when the anchor was not reached (item 54).
- Raw rows, one JSON line each (`rows_<arm>_tag-m4.jsonl`): every AlphaFold run (pair, seed, wall-clock, per-model times when
  available, `incomplete` when timed out, `download_in_timed_call`), every docking and analysis timing (`truncated` when it hit
  its per-pair cap), every MD segment (complex, atom count, steps, wall-clock, engine rate or null, `frame_interval_ps`), every
  storage measurement (artifact, apparent bytes).
- `pairs_tag-m4.json` and the three pair FASTA files (item 40); the MD reporter files, the DCD trajectory's size record and the
  raw docking rank tables (items 41, 42, 16).
- `RUN_VALID.json`; `env.txt` (named non-secret variables only, including the `REMOTE_TIMEOUT` seen and the pre-T0 seconds);
  `m4_summary.json` (first key `what_this_run_decides`); download, install, smoke-check and tool logs; the pip report and the
  apt package hashes (item 34), the pip bootstrap entry when it ran (item 50), the colabfold marker record (item 51); the
  `RUN_DONE` marker with the exit code (3 after any guard, ceiling or timeout stop with inputs unmeasured) and the per-input
  status of item 8 (items 46, 55), in which an input decided before an early end stays `decided` or `void_by_rule`.
