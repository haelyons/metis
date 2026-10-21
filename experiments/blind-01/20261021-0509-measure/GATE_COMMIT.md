# GATE COMMIT: measure run m4 (card seed:idea:1, tag m4)

Date: 2026-10-21. Written by the gate (a model session) standing in for the owner, who delegated this human role under the
standing rules of 2026-10-20 and 21. Every answer below is the gate's own and is recorded as such. Nothing was run.

## Inputs read (and nothing else)

| File | Note |
|---|---|
| `QUESTION.md` | the compiled measurement question; it quotes the card's sha256 `d4538bfe7fb86d888780206819a7f75846595034bc18ad47e65848d954359813` |
| `CARD.json` | calibration record copied from the card; same sha256 in its `result_json_sha256` |
| `out/design_record.json` | carries `design`, `diff`, `triage` and `gate`; no `halt` and no `error` key, so the run is not a halt record |
| `/home/hal/dev/interp/metis/experiments/immersion-coolants/20261020-1020-measure/GATE_COMMIT.md` | shape example only; its content is not used |
| `/home/hal/dev/interp/metis/experiments/immersion-coolants/20261020-1020-measure/EXEC_NOTE.md` | shape example only; its content is not used |
| `sessions/GATE_2.md` | the standing rules and the task |

No file hash was computed (the gate runs nothing); the only hash relied on is the card's, quoted in two of the inputs above.

## What is being gated, in plain words

One rented single-GPU box (A100 40 GB if it has capacity) first times a 60 s sleep and an empty run to prove the timer works,
then redocks AAVR-PKD2 onto AAV2 and compares it with PDB 6IHB. If that anchor misses, the run stops and no input is reported
as measured. If it passes, the box times four things on three stand-in capsid-receptor pairs: AlphaFold-Multimer hours per run
(3 pairs x 3 seeds, 5 models, 20 recycles, no sequence database), molecular-dynamics speed in explicit solvent
(3 complexes of 120k to 180k atoms), the docking-and-analysis hours per pair, and the bytes written per run scaled to the
card's 216-run grid. Each is read against the card's own band. The card's 54-run pilot, its 216-run grid and its decision rule
are not run.

## Decision on budget and build

**GO.** The design's budget (USD 8) is under the owner's USD 10 cap, so no protocol shortening is forced by cost. The
shortening that the design already carries (3 pairs, 3 seeds, 0.5 ns, no sequence database, one GPU) is ruled below as a
ruling of record.

Arithmetic, launches x hours x price, at `gpu_1x_a100_sxm4` USD 1.99/h:
- per launch, remote command at its cap: 7,200 s = 2.00 h x 1.99 = USD 3.98
- two launches: 2 x 3.98 = USD 7.96
- plus up to 600 s per launch outside the remote command (provisioning, fetch, teardown): 2 x (7,200 + 600) s = 15,600 s
  = 4.333 h x 1.99 = USD 8.62, under the USD 10 cap with USD 1.38 left
- `BUDGET_LEFT_USD=5` per launch: 3.98 is under 5 (the dollar guard cannot bind before the time cap on an A100)
- any alternative single GPU is acceptable only up to USD 2.50/h: 2.00 h x 2.50 = USD 5.00 = `BUDGET_LEFT_USD`; two launches
  USD 10.00 before the outside-the-command allowance, so above USD 2.50/h the operator does not launch and asks
- the card's own pilot line (6 h, USD 95.52 = 8 x 1.99 x 6) is far above the cap, so the owner's cap binds, as QUESTION.md says

## Answers of record

Each answer says what the build must do about it, or that nothing changes and why. Counts: 5 departures, 1 grounding, 1 run
item, 0 author items, 7 instrument items, 0 shared items: 14 answers.

### Diff departures (5)

1. **D1 (is the card's gate applied to the MD speed and the auxiliary hours too?).** ONLY TO THE ALPHAFOLD TIMING. The card's
   gate is `on: af2_h_per_run, <= 1`; QUESTION.md repeats its text under C1 to C3 only because the phase carries it. The
   build applies it to the measured af2_h_per_run and nowhere else. Record C1 carries `gate_value` 1, `gate_pass` (true or
   false) and the card's fallback text verbatim in `gate_else`. Records C2 and C3 carry `gate: "not applicable: the card's gate
   is on af2_h_per_run"`. A C1 decision is PASS or FAIL against the band alone; a measured value in (1, 1.25] is PASS on the band
   with `gate_pass` false, and `m4_summary.json` restates the fallback text. The run does not branch on the gate.

2. **D2 (3 of 9 pairs, 3 seeds, instead of the 54-run pilot).** ACCEPTED, as a ruling of record under standing rule 1 (the pilot
   line costs USD 95.52, the cap is USD 10); no input is dropped. The design's sample binds: 3 stand-in pairs, one per capsid
   slot, 3 seeds each: 9 AlphaFold timings, 3 MD timings, 3 auxiliary timings, 3 storage measurements. QUESTION.md names no
   structure for the 9 card pairs, so the pairs are stand-ins and every record says so ("stand-in pairs built from 6IHB chains,
   not the card's pairs"). The build builds each stand-in as a hetero-multimer from chains of the 6IHB entry (capsid-protein and
   PKD2 chain copies), with total length inside 750 to 1,000 residues and the three lengths spread across that range as far as
   the entry allows; it records chain ids, sequences, lengths and file hash. AlphaFold runs go seed-major (all three pairs at seed 0,
   then seed 1, then seed 2) so a time stop leaves every pair covered. Minimums for a decision: C1 needs at least 3
   completed runs covering all 3 pairs; C2 at least 2 complexes (the median of two is their mean; the record says n=2); C3 at least 2
   pairs; C4 at least one run of each artifact type it scales; below a minimum the record is VOID with the raw rows kept. The
   card's seed-to-seed SD of calls and the 9-pair spread are not measured; the labels say so.

3. **D3 (shortcut alignments, single GPU).** ACCEPTED, with limits. Single GPU: accepted; the quantity is a per-GPU hours per
   run, and scaling to 8 GPUs is not tested (label "one GPU; no multi-GPU scaling"). Alignments: single-sequence input only, no
   sequence database download, and no call to any remote alignment service (sending sequences off the box is not a source the
   design names). Label on every C1 value: "no-MSA: alignment search time excluded; understates the card's setting". The
   decision is still read against the band; a PASS is a PASS for this stand-in protocol only. Full search setup: not authorised
   (it does not fit the time cap). Model setting: 5 models, exactly 20 recycles with early stopping off (the card's "up to 20" at
   its upper end), recorded. The measured value is the mean wall-clock hours of the whole prediction call per run, first-model
   compile included; rows also carry the compile-excluded figure when the engine log gives per-model times, and the decision uses
   the included figure. Downloads allowed, URL and sha256 recorded for each: the PDB entry 6IHB from RCSB, the AlphaFold
   parameter archive from the AlphaFold project's own storage address, and Python wheels and declared apt packages through
   pip and apt; any other host is not allowed. A download that fails stops the run with a void record (exit 2); no substitute
   source.

4. **D4 (what auxiliary hours and storage mean).** ACCEPTED as the design reads them, pinned:
   - aux_h_per_pair = wall-clock hours, per pair, of everything that is neither AlphaFold nor MD: docking of the pair, interface
     analysis (contacts, interface residues, distance to the nearest threefold axis, site class) and writing the call-table row.
     Installs, downloads and setup are excluded. Mean over the 3 pairs. The value is decided against [0.3333, 3] as a GUESS term;
     the record says "producer's reading, design's definition".
   - n_storage_gib = bytes actually written on disk for one grid run (AlphaFold outputs of one run; docking poses and tables of
     one pair; the MD trajectory and logs of one 0.5 ns segment, frame interval recorded), intermediates kept as written, times
     216 runs, divided by 2^30. The decision uses the 216-run figure with intermediates kept. The record also carries the
     432-run figure (x 2), the figure with intermediates deleted, and MD bytes per ns, as information, not decision. Scaling is
     linear in runs. The card's plate-layout call table and bead-panel CSV are small and are not generated.

5. **D5 (invented choices).** ACCEPTED: 0.5 ns production segment after equilibration, AlphaFold seeds 0, 1, 2, one MD velocity
   seed (0) per complex, the 60 s sleep check, the empty-run check, USD 8 as the plan figure under the USD 10 cap (the caps
   in "Pre-authorisation" bind, not the USD 8). REJECTED: the rule "if 3 seeds give a relative SD over 50 percent, a second
   launch doubles the seeds". A spread above 50 percent on any pair is recorded as the label "seed spread high; mean is
   uncertain" and nothing is relaunched for it. The anchor's second independent code (card: LightDock and pyDock, consensus
   pose) is NOT run, as a ruling of record under rule 1 and rule 4: two docking codes with their data do not fit the install
   cap. One pip-installable docking code is used, name and version recorded, and the anchor record carries
   `independent_code: "not run: single docking code"`.

### Grounding (1)

6. **G1 (design-core: reader verdict "unauditable").** ACCEPTED AS-IS, with two binding consequences. (a) The reader re-derived the
   bands and the gate from the card and they match; it found no measurement artifact because nothing has run; the run produces
   them and the post-run reader grounds them. (b) Its first crux (the design's own reading of input 3 and the possible
   shortcut alignments mean a pass decides the proxy question, not the card's protocol): every C record carries the labels
   "stand-in pairs built from 6IHB chains", "no-MSA" (C1), "producer's reading of aux hours" (C3) and "one GPU, one box, 3
   pairs"; `m4_summary.json` says in its first field that the run decides the stand-in protocol only. Its second crux (units
   and scale unproven) is answered by item 7.

### Run queue (1)

7. **R1 (on-box harness controls first: 60 s planted sleep, empty-input dry run, unit-and-scale print before any band
   comparison).** QUEUED CONTROL, binding on the build, and first on the box after the install stage: (a) the planted 60 s sleep
   through the same timer; error at most 5 percent; if not, run_valid false, exit 2, nothing else runs; (b) the empty-input dry
   run (the harness with no tool call): time under 2 s and bytes written under 1 MiB, else the excess is subtracted from later
   values and the record is labelled "setup overhead subtracted"; (c) a unit-and-scale print, one record before any decision:
   raw AlphaFold seconds per run, the MD engine's rate lines and the production wall-clock beside the computed ns/day (agreement
   within 5 percent, else every ns/day is labelled "engine rate and wall-clock disagree" and both are reported), and raw bytes
   per artifact. No band is compared before these records are written.

### Author queue and shared queue

Both are empty in the design record (`author_queue: []`, `shared_queue: []`, `authored: null`): nothing to answer. The
`AUTHOR:` lines are in the instrument queue and are answered next.

### Instrument queue (7): validation controls, all inside the selftest or the run, no extra spend

For every readout the "held-out ground truth" is a planted case whose answer the gate states here, so a script can check it
without a model. The marginal rule used below: a value within 10 percent of a band edge (`edge x 0.9` to `edge x 1.1`) is
decision VOID with `marginal: true`, as the design says "reported as marginal, not decided"; the raw value is kept.

8. **I1 (anchor readout).** QUEUED CONTROL. Contact overlap = the fraction of the reference (6IHB) interface residue-residue
   contacts (any heavy-atom pair at most 4.5 A) that the pose also makes. Selftest, planted: overlap 0.50 with RMSD 9.0
   passes; overlap 0.49 with interface backbone RMSD 5.0 passes; overlap 0.49 with RMSD 5.01 fails; serial vs parallel top-pose
   RMSD 2.0 with identical calls passes, 2.01 fails, 0.0 with different bind/no-bind calls fails. A planted pair of tiny
   structures with 3 of 6 reference contacts recovered gives overlap exactly 0.5; a planted pose shifted 5.0 A along x
   gives RMSD 5.0 (to 4 digits). The anchor record values carry `measured` (the overlap, the RMSD, the serial-parallel RMSD and
   the calls), `published`, `tolerance`. Anchor FAIL: run_valid false in every later record, C1 to C4 written VOID, exit 4.

9. **I2 (C1 readout, af2_h_per_run).** QUEUED CONTROL. Planted: per-run wall-clock 1,800 s gives 0.5 h; mean of runs
   0.5 PASS, 1.5 FAIL, 0.1 FAIL, 1.2 VOID (marginal, upper), 0.21 VOID (marginal, lower), 1.1 PASS with `gate_pass` false and
   the fallback text, 0.9 PASS with `gate_pass` true. Planted logs: with n=2 runs the record is VOID; with 3 runs missing one
   pair VOID.

10. **I3 (C2 readout, md_ns_per_day_a100).** QUEUED CONTROL. Planted: an engine log rate line parses to its number; production
    steps x timestep over wall-clock gives ns/day to 4 digits (planted 250,000 steps x 2 fs in 335 s gives 129.0); median of
    (100, 129, 500) is 129 and PASSes; 40 FAIL; 400 FAIL; 56 VOID (marginal); 60 PASS; 330 VOID (marginal upper); an atom count
    of 119,999 or 180,001 gives VOID (system outside the card's 120k to 180k) and 150,000 passes the size check. A GPU name
    other than A100 gives VOID for C1 and C2 with the raw number kept and the label "not an A100".

11. **I4 (C3 readout, aux_h_per_pair).** QUEUED CONTROL. Planted: pair wall-clocks (3,600 s, 3,600 s, 3,600 s) give mean 1.0 h
    PASS; 0.2 FAIL; 4.0 FAIL; 0.3333 VOID (marginal); 3.2 VOID (marginal); 0.5 PASS; 2.5 PASS. Hours exclude install and
    download wall-clock: a planted record with 7,200 s of install and 1,800 s of docking gives 0.5 h.

12. **I5 (C4 readout, n_storage_gib).** QUEUED CONTROL. Planted: 1,073,741,824 bytes per run = 1.0 GiB per run x 216 = 216.0
    GiB PASS (432-run figure 432.0); 0.1 GiB per run gives 21.6 FAIL; 4.0 gives 864.0 FAIL; 2.9 gives 626.4 VOID (marginal);
    0.35 gives 75.6 PASS. The sum of file sizes under the run's output directories (apparent bytes, not block counts) is the
    byte count; a planted directory with files of 1,000 and 24 bytes sums to 1,024.

13. **I6 (harness validity readout).** QUEUED CONTROL. Planted: measured 62.9 s for the 60 s sleep passes (4.83 percent);
    63.1 s fails (5.17 percent) and gives run_valid false, exit 2. Seed spread: planted AlphaFold timings (1,800, 1,830, 1,790)
    for one pair pass (nonzero SD); (1,800, 1,800, 1,800) fails and gives C1 VOID with "zero spread across seeds: wrong
    variance source" while other inputs stand; planted relative SD 0.6 gives the label "seed spread high; mean is
    uncertain" and nothing else. Empty run: planted 0.5 s and 100 KiB pass; 5 s or 2 MiB fail and trigger the subtraction
    label.

14. **I7 (cost and time readout).** QUEUED CONTROL. Planted: elapsed 3,600 s at USD 1.99/h gives spend 1.99; elapsed 7,200 s
    gives 3.98; the guard with `PRICE_USD_PER_HOUR=1.99`, `BUDGET_LEFT_USD=5`, `REMOTE_TIMEOUT=7200` stops at the time cap, not the
    dollar cap (5.00 / 1.99 = 2.513 h = 9,045 s is above 7,200 s); with a planted price of 2.50 the dollar cap and the time cap
    coincide at 7,200 s; with 3.00 the dollar cap stops at 6,000 s; a stage whose estimated remaining time exceeds the time
    left is not started: the guard writes void (unmeasured) records for the unfinished inputs, keeps finished ones, sets exit
    code 3, and leaves run_valid as it was (a guard stop is not an anchor or harness failure).

## Labels

- Every measured record carries: instance type (`INSTANCE_TYPE`), GPU name, driver (nvidia-smi), CUDA runtime version, engine
  versions and build flags (AlphaFold implementation and its parameter archive hash, the JAX build, the docking code, the MD
  engine and its precision and platform, the compiler or wheel build as installed), start and end wall-clock, price per
  hour, `run_valid`.
- Every C record adds: "stand-in pairs built from 6IHB chains, not the card's pairs", "one GPU; one box; 3 pairs; no
  multi-GPU scaling", and `n` (runs behind the value).
- C1 adds "no-MSA: alignment search time excluded; understates the card's setting"; C2 adds the atom counts and the engine
  precision; C3 adds "producer's reading of aux hours"; C4 adds "linear in runs; intermediates kept; MD length 0.5 ns".
- The anchor adds `independent_code: "not run: single docking code"`.
- Records read from an early-stopped run are labelled "incomplete run: unmeasured inputs are VOID, not holding".

## Checks the gate made before answering

Arithmetic only, on numbers in the inputs. No experiment was run.
- Bands re-derived from the card: 0.5 / 2.5 = 0.2 and 0.5 x 2.5 = 1.25; 129 / 2.5 = 51.6 and 129 x 2.5 = 322.5; 1 / 3 = 0.3333 and
  1 x 3 = 3; 200 / 3 = 66.67 and 200 x 3 = 600. All match QUESTION.md and the design. The gate `af2_h_per_run <= 1` sits inside
  the C1 band (upper edge 1.25), so a value in (1, 1.25] holds the band and fails the gate; it is answered in 1 and 9.
- Card cost lines: 8 x 1.99 = 15.92 per hour; x 6 h = 95.52 (l_pilot); x 24 h = 382.08 (l_main). Both match CARD.json.
- Cap: 7,200 s = 2 h; 2 h x 1.99 = 3.98; two launches 7.96; with 600 s outside the command each 8.62; all under USD 10.
- Time inside a 7,200 s launch, stage ceilings the build must set (item 28 of EXEC_NOTE): install and downloads 2,000 s,
  controls and anchor 700 s, AlphaFold 2,100 s, MD 1,800 s (3 complexes at up to 600 s each; 0.5 ns at 129 ns/day is 335 s),
  endpoints 100 s, margin 500 s: 2,000 + 700 + 2,100 + 1,800 + 100 + 500 = 7,200. AlphaFold at 9 runs may not fit; the
  seed-major order and the minimums (answer 2) cover that.
- The question's "216 vs 432 runs": the card's phase p2_main is 216 runs and its prediction text mentions 432; the decision
  uses 216, the record carries both (answer 4).
- Marginal margins: C1 [0.18, 0.22] and [1.125, 1.375]; C2 [46.44, 56.76] and [290.25, 354.75]; C3 [0.3, 0.3667] and [2.7, 3.3];
  C4 [60.0, 73.34] and [540, 660]. The planted values in answers 9 to 12 were checked against these.
- The design record has no `halt` or `error`; `author_queue` and `shared_queue` are empty; `diff.departures` has 5 entries;
  `triage.instrument_queue` has 7.

## Pre-authorisation

- **A1 (launch 1).** Authorised after the build is ready and its selftest passes: instance `gpu_1x_a100_sxm4` (A100 SXM4 40 GB,
  USD 1.99/h) in us-east-1 if it has capacity, else the cheapest single GPU with capacity at no more than USD 2.50/h; the
  operator records which on every record. `REMOTE_TIMEOUT=7200`, `BUDGET_LEFT_USD=5`, `PRICE_USD_PER_HOUR` set to the chosen
  instance's price.
- **A2 (launch 2).** At most one more, within the same USD 10 total, authorised only if launch 1 (a) halted before the anchor
  decision for a toolchain, install or launcher reason, after the cause is recorded in RUN.md and, if the directive changes, the
  build is re-run (no built file edited by hand); or (b) stopped on its time guard with inputs unmeasured, in which case launch 2
  reruns the anchor first and then only the unfinished inputs. Not authorised: a relaunch to double seeds, to repeat a decided
  input, to change a band, or after an anchor miss (a missed anchor is a result).
- **What stops a launch.** The cost and time guard (spend projected to reach `BUDGET_LEFT_USD`, or the remote timeout), an anchor
  miss (exit 4), the harness sleep check failing (exit 2), any broken infrastructure (exit non-zero with a void record, no
  patching around), or a stage ceiling being hit. A stopped launch writes its summary and `RUN_DONE` before exit.
- **Totals.** At most two launches; USD 7.96 at the cap for the remote commands, USD 8.62 with the allowance for time outside
  them; the project and owner cap of USD 10 is not exceeded and is not raised by this gate.

---

## Addendum 3 (2026-10-21)

Rules on `out/review_build2.md` (review of build 2, execution layer; 15 findings: 6 BLOCKING, 9 ADVISORY). Inputs added for
this addendum: that report, this file as it stood, `EXEC_NOTE.md` as it stood, `sessions/GATE_3.md`. The gate ran nothing and did
not read `run_m4.py`; each ruling rests on the reviewer's line references, taken as reported. Every earlier section above stands
except where an answer below says it is superseded (the stage ceilings in "Checks the gate made before answering" are
superseded by answer B8). Answers are numbered B1 to B15, one per finding, in the report's order. Counts: 15 answers.

**Decision on budget and build (addendum).** GO stands. Build 3 spends no GPU money. Launch spend so far: none is evidenced in
the inputs read. Cap arithmetic is unchanged: 2 launches x 2.00 h x USD 1.99 = USD 7.96; with 600 s outside each, USD 8.62;
under the USD 10 cap. No change to caps, instance or `BUDGET_LEFT_USD`.

1. **B1 (finding 1, BLOCKING: guard or ceiling stop sets run_valid false).** ACCEPTED; the build changes `fail_stage`
   (`run_m4.py:2244-2249`). `set_run_invalid` is called only for exit 2 (infrastructure or harness failure) and exit 4 (anchor
   miss). Exit 3 (guard stop, stage ceiling, outer timeout) leaves `run_valid` as it was, voids only the unfinished inputs,
   keeps finished inputs' decisions, and labels every record written after it "incomplete run: unmeasured inputs are VOID, not
   holding". The `fail ... 3` calls in `onbox_m4.sh` (lines 109, 125, 133, 144, 147, 152, 158-160, 170) route to that guard path.
   Selftest gets planted stage-flow cases (answer B15).

2. **B2 (finding 2, BLOCKING: guard or ceiling stop inside generate exits 0).** ACCEPTED. Each of the three early returns
   (`stage_af2` 1573-1576, `stage_aux` 1517-1518, `stage_md` 1718-1719) raises `GuardStop` (or records the stop in run state
   that `run_stages` reads), so the stage is marked not done. A ceiling stop ends that stage only; a later stage whose own guard
   allows it still starts; `stage_endpoints` always runs. At the end `run_stages` exits 3, not `EXIT_OK`, whenever any input is
   unmeasured because of a guard, ceiling or timeout stop, so the A2(b) relaunch condition is readable from `RUN_DONE`. Exit 0
   only when C1 to C4 are all decided or marginal-VOID by measurement.

3. **B3 (finding 3, BLOCKING: a timed-out AlphaFold or MD call voids everything).** ACCEPTED. In `run_tool`
   (`run_m4.py:1052-1069`) a timeout is distinct from a failure: a timeout (the call exceeded the stage allowance,
   `min(stage_left, seconds_left)`) is a ceiling stop (B2 path, exit 3), not `ToolError`. A real tool failure (non-zero exit,
   crash, missing output) stays broken infrastructure: exit 2, run_valid false, no patching around. A timed-out run's row is kept
   in the raw rows with `incomplete: true` and is not counted in a mean; the stage's finished rows are kept; endpoint records are
   written from finished rows against the minimums in answer 2 (C3 stays decided if finished; C1 or C2 below its minimum is
   VOID with the raw rows kept). No input already finished is voided by a later stage's stop.

4. **B4 (finding 4, BLOCKING: REMOTE_TIMEOUT is not forwarded).** ACCEPTED. This sits in the operator's launcher, not in the
   build's two files: the operator makes `lambda_run_m4.sh` forward `REMOTE_TIMEOUT` with `PRICE_USD_PER_HOUR`,
   `BUDGET_LEFT_USD` and `INSTANCE_TYPE` (the header then declares four added variables, not three) and re-diffs it against
   `frozen/lambda_run.sh` before launch 1. The build adds what it controls: `onbox_m4.sh` and `run_m4.py` record the
   `REMOTE_TIMEOUT` value they see in `env.txt` and `m4_summary.json`; if it is unset the script uses 7200 and the summary
   carries the label "REMOTE_TIMEOUT not forwarded; default 7200 used". No default above 7200 or `BUDGET_LEFT_USD` above 5.

5. **B5 (finding 5, BLOCKING: anchor overlap compares keys that cannot match unless the receptor chain id is "B").** ACCEPTED. The
   build keys contacts by chain role, not by the file's chain id: both the reference (6IHB) contact set and the pose's contact
   set are built after the receptor chain is mapped to the same chain id (and the capsid chain(s) likewise) through one
   mapping function used for both, so `contact_overlap` compares like with like. Selftest, planted: the same planted pose and
   reference give overlap 0.5 with the receptor chain id "B" and the same 0.5 with it "C" and with it "A"; a reference whose
   receptor chain id differs from the pose file's no longer gives 0.0; the native-versus-pose round trip through `write_pdb`
   and `read_pdb_atoms` is in the case. An overlap of exactly 0.0 on a pose with a non-trivial planted overlap fails the
   selftest.

6. **B6 (finding 6, BLOCKING: no check that the declared tools start before the expensive stages).** ACCEPTED. The install
   stage ends with a smoke check inside the install ceiling, after every install and before the controls: import of the
   AlphaFold-Multimer stack and JAX with a listed device of type GPU; `colabfold_batch --help`; the docking code's entry point
   `--help`; OpenMM imported with `Platform.getPlatformByName("CUDA")` succeeding. A failure is exit 2 with a void record
   (rule 4), before any GPU stage is paid for, and counts under A2(a) (a halt before the anchor decision). The build pins every
   package version in the install line (name, version, in the recorded pip report; B13) and chooses the package form that
   carries the CUDA platform for OpenMM and a JAX build compatible with the pinned `colabfold`; it does not substitute a
   tool, and it does not rely on the reviewer's recollection (not verified by the reviewer) that the plain PyPI wheel lacks
   the CUDA platform: the smoke check is the test. Install order: JAX last or pinned such that `colabfold_batch` still
   imports; the smoke check decides.

7. **B7 (finding 7, ADVISORY: HF_TOKEN reaches every subprocess).** ACCEPTED. `onbox_m4.sh` unsets `HF_TOKEN` and
   `HUGGING_FACE_HUB_TOKEN` after the downloads (none of the named sources needs it), and `run_tool` passes every child a
   copied environment with both removed. `env.txt` still names no secret. Selftest: a planted environment containing both
   variables yields a child environment without them.

8. **B8 (finding 8, ADVISORY: docking and analysis have no stage ceiling).** ACCEPTED, and the stage ceilings of EXEC_NOTE
   item 28 are re-set; this supersedes the ceilings in "Checks the gate made before answering" above. New ceilings, in
   seconds: install and downloads with the smoke check 1,800; controls and anchor 700; per-pair docking and analysis 600 in
   total (at most 250 per pair); AlphaFold 2,000; MD 1,600 (at most 600 per complex); endpoints 100; margin 400.
   Sum: 1,800 + 700 + 600 + 2,000 + 1,600 + 100 + 400 = 7,200. A pair that reaches its 250 s keeps a row labelled
   `truncated: true` (a lower bound on its hours), is not counted in the mean, and C3 stays decided on the finished pairs if at
   least 2 finished, else VOID. A stage's allowance is the lesser of its ceiling and the time left minus the margin and the
   endpoints slot.

9. **B9 (finding 9, ADVISORY: "incomplete run" label missing).** ACCEPTED. The constant carries the full label "incomplete run:
   unmeasured inputs are VOID, not holding" next to `LABEL_UNMEASURED = "unmeasured, not holding"`; every record written after a
   guard, ceiling or timeout stop carries the full label (also in `m4_summary.json`). Selftest: a planted early-stopped run's
   records all contain the string.

10. **B10 (finding 10, ADVISORY: "interface backbone RMSD" is the whole receptor chain).** ACCEPTED; the build changes
    `run_m4.py:1409` and `1423`. The RMSD is taken over the backbone atoms (N, CA, C, O) of the receptor residues that make up
    the reference's interface (any heavy atom of the residue within 4.5 A of the capsid in 6IHB), in the capsid's frame, no
    superposition of the receptor. The label names what it is. The serial-versus-parallel top-pose RMSD stays over the whole
    receptor chain and is labelled so. Selftest: a planted pose shifted 5.0 A along x on the interface atoms gives 5.0000; a
    planted pose that moves only non-interface receptor atoms by 20 A gives interface RMSD 0.0000 (and a whole-chain RMSD above
    0), so the two measures are told apart.

11. **B11 (finding 11, ADVISORY: `sudo -n apt-get` does not keep DEBIAN_FRONTEND).** ACCEPTED. `onbox_m4.sh` calls
    `sudo -n env DEBIAN_FRONTEND=noninteractive apt-get ...`. Nothing else changes; `sudo` stays for declared apt packages only.

12. **B12 (finding 12, ADVISORY: outer `timeout` stops only run_m4.py).** ACCEPTED. Every tool call (colabfold, the docking code,
    the OpenMM worker) runs in its own process group, and the timeout path kills the group; when the outer `timeout` on
    `run_m4.py` returns 124, `onbox_m4.sh` kills the process groups it recorded (by group id, not by name) before the endpoints
    stage and routes the outcome as a guard stop, exit 3 (B1, B2), not `fail`/exit 2. The inner tool timeout is set at least
    100 s shorter than the outer kill, so the inner one fires first; an outer-timeout firing is itself a recorded event.
    Selftest: a planted tool that sleeps past its allowance is killed with its child and the result is a ceiling stop.

13. **B13 (finding 13, ADVISORY: wheel URLs and hashes are not recorded).** ACCEPTED. Rule 10 and EXEC_NOTE items 7 and 14 hold
    for pip and apt too: pip installs run with `--report` and the report (URL and archive hash of each wheel) is kept under
    `results_m4/out/`; apt packages are recorded with version and the SHA256 from `apt-cache show` for each package; the two
    direct downloads keep URL and sha256 as before. Records cite the report's file hash in `inputs`.

14. **B14 (finding 14, ADVISORY: build return does not match the files).** ACCEPTED, as a check on the evidence. The selftest
    prints a line `selftest: files sha256 run_m4.py <hash> onbox_m4.sh <hash>` (the script hashes itself and its sibling,
    stdlib) before its pass line, so a log is tied to the files; the build's return states real line counts and those hashes.
    After the build the operator re-runs the selftest locally and compares the hashes before launching. No launch on a log whose
    hashes do not match the files on disk. The last line stays exactly `selftest: PASS` or `selftest: FAIL`.

15. **B15 (finding 15, ADVISORY: selftest does not exercise the stage flow).** ACCEPTED, and it is binding because findings 1 to 3
    sat in that layer. `run_stages` takes its stage functions and tool runner by injection so the selftest can run the whole
    flow with fakes (no GPU, no network, no tool). Planted flows, each asserting exit code, `run_valid`, per-input decisions and
    the labels: (a) all stages finish: exit 0, run_valid true; (b) a time-guard stop in AlphaFold with 2 of 9 runs done:
    exit 3, run_valid true, C1 VOID with raw rows kept, C2 to C4 decided, full incomplete label; (c) a tool timeout in MD on
    the third complex: exit 3, run_valid true, C2 decided on n=2, C1, C3, C4 untouched; (d) a ceiling stop in docking: exit 3,
    C3 decided on finished pairs or VOID below 2; (e) a real tool failure: exit 2, run_valid false, all inputs VOID; (f) anchor
    miss: exit 4, run_valid false, C1 to C4 VOID; (g) sleep failure: exit 2; (h) install, smoke-check and download failure:
    exit 2; (i) the outer-timeout route (rc 124): exit 3, run_valid true. These are in addition to the cases of EXEC_NOTE items
    21 to 27.

**Checks the gate made before answering (addendum).** Arithmetic only. New ceilings: 1,800 + 700 + 600 + 2,000 + 1,600 + 100
+ 400 = 7,200 (checked twice). Old and new totals both 7,200 s = 2.00 h = USD 3.98 at 1.99/h. Per-pair docking cap 3 x 250 = 750,
above the 600 stage total: the stage total binds, which is intended (the per-pair cap only stops one pair eating the stage).
The MD ceiling: 3 x 600 = 1,800 above the 1,600 ceiling; two complexes always fit (2 x 600 = 1,200), the third may not, and C2's
minimum is 2. Inner timeout 100 s below the outer kill: outer kill = stop_at minus elapsed minus 600 per the report, so the inner
tool timeout becomes stop_at minus elapsed minus 700. No planted value of answers 8 to 14 changes.

**Pre-authorisation (addendum).** Unchanged: A1 and A2 above stand. A failed smoke check (B6) is a halt before the anchor
decision for a toolchain or install reason and falls under A2(a). The launcher change of B4 is a launcher reason recorded in RUN.md.
No launch is authorised until build 3 exists, its selftest passes with matching hashes (B14), and the operator has fixed
`lambda_run_m4.sh` (B4).

Build 3 authorised

---

## Addendum 5 (2026-10-21)

Rules on `out/review_build6.md` (review of build 6, execution layer, run on `wf.js`; verdict FAIL: 11 BLOCKING, 15 ADVISORY,
plus 3 operator findings it verified and an 8-point checklist summary). Inputs added for this addendum: that report, this file
as it stood, `EXEC_NOTE.md` as it stood, `sessions/GATE_5.md` is the task and is not a source of rulings. The gate ran nothing
and did not read `run_m4.py`, `onbox_m4.sh` or `frozen/ONBOX_CONTRACT.md`; each ruling rests on the reviewer's line references,
taken as reported. Every earlier section stands except where an answer below says it is superseded. Answers are numbered E1 to
E28: E1 to E26 are the report's findings in its order, E27 the three operator findings, E28 the checklist summary. Counts: 28
answers. The line `Build 5 authorised` at the end is the launcher's literal string for the next build; it does not renumber
the earlier builds.

**Decision on budget and build (addendum).** GO stands. No GPU money has been spent: the reviewer ran nothing and no launch
record is among the inputs. Cap arithmetic unchanged: 2 launches x 2.00 h x USD 1.99 = USD 7.96; with 600 s outside each,
2 x (7,200 + 600) s = 15,600 s = 4.333 h x 1.99 = USD 8.62; under the USD 10 cap with USD 1.38 left; `BUDGET_LEFT_USD=5` per
launch above the 3.98 a launch can cost. No change to caps, instance or `BUDGET_LEFT_USD`. Three of the findings (E1, E3, E5)
and finding 2 would each have spent a launch without a valid record; that is why they are binding and why E28 adds a selftest
layer.

### Blocking findings (E1 to E11)

1. **E1 (finding 1, BLOCKING: tools are called by bare name; the venv's bin is not on PATH).** ACCEPTED. The build resolves every
   tool through the venv: `onbox_m4.sh` exports `PATH="${VENV}/bin:${PATH}"` before the first stage, and `run_m4.py` builds
   `child_env` with the venv's bin directory first (taken from `sys.executable`'s directory, not from the inherited PATH) and
   calls tools by absolute path where it can (`${VENV}/bin/colabfold_batch`, `lightdock3.py`, `lightdock3_setup.py`, `lgd_*`).
   The smoke check resolves each tool with `shutil.which` against that PATH and records the resolved absolute path; an
   unresolved tool is exit 2 inside the install stage. Selftest: a planted venv directory with an executable stub is found
   through `child_env` and not found through the bare inherited PATH.

2. **E2 (finding 2, BLOCKING: the 1,800 s install ceiling is not a stage total).** ACCEPTED. `stage_allowance_s("install")`
   becomes a running total: every apt, pip, download and smoke-check call takes `min(its own limit, install ceiling minus install
   seconds already used, time left minus margin and endpoints slot)`. When the install total is exhausted the stage stops with
   exit 2 (broken infrastructure: nothing measurable exists without the tools; run_valid false, void record, `RUN_DONE`), not
   exit 3, and it falls under A2(a). Selftest: planted install calls whose sum passes 1,800 s stop at 1,800 s, not at the sum of
   the per-call limits.

3. **E3 (finding 3, BLOCKING: the parameter archive is downloaded but never extracted; colabfold fetches its own inside the timed
   call).** ACCEPTED. The install stage verifies the archive's sha256 (recorded), extracts it into `<data>/params` (the same
   `--data` directory colabfold is given), and verifies that the multimer parameter files for the 5 models are present there
   before the smoke check ends; missing files are exit 2. No network access is needed in any timed call. If a timed call's log
   shows a download or extraction anyway, that row carries `download_in_timed_call: true`, is not counted in the mean, and C1 is
   VOID with the label "download inside timed call"; the run is not otherwise stopped. The extraction wall-clock is install time,
   never C1 time. Selftest: a planted archive extracts to the expected layout; a planted log line "Downloading" sets the flag.

4. **E4 (finding 4, BLOCKING: stand-in pairs are not checked against item 12 and the evidence is not recorded).** ACCEPTED. After
   building the three pairs the build asserts: each pair's total length is in 750 to 1,000; the three sequences are pairwise
   different and the three lengths pairwise differ by at least 20 residues (the answer-2 spread, "as far as the entry allows",
   now with a floor); the pair has one capsid-role chain set and one receptor-role chain set. If the 6IHB chains cannot meet the
   range, the build may use more than one copy of a capsid chain (answer 2 allows chain copies) before giving up; if it still
   cannot, exit 2 with a void record that says which assertion failed (no silent clamp: `want_cap` clamping is an error, not a
   behaviour). Evidence is written into `results_m4/out/`: `pairs_tag-m4.json` (chain ids and role mapping, sequences, lengths,
   sha256 of each pair's FASTA and PDB file) and copies of the three FASTA files; each C record cites that file's hash in
   `inputs`. Selftest: a planted short capsid chain fails the range assertion; planted equal-length pairs fail the spread
   assertion; planted good pairs pass and the evidence file parses.

5. **E5 (finding 5, BLOCKING: MD runs on the receptor alone, not on a docked complex).** ACCEPTED. The MD input is the
   merged complex: the pair's capsid-role chains from the stand-in pair file plus the top-ranked docking pose of the receptor,
   written as one structure, with the chain roles preserved; the build asserts both roles are present and the heavy-atom count of
   the capsid part is nonzero before solvation, else exit 2. Water padding is chosen so the solvated total is inside 120,000 to
   180,000 atoms (estimated from the solute's extent before building, then verified on the built system; one rebuild allowed
   inside the complex's 600 s). If the target cannot be met, C2 is VOID with the atom count kept, per answer 10; the
   range is not widened. Selftest: a planted receptor-only pose is refused; a planted merged complex passes the role check; a
   planted solvation count of 119,999 or 180,001 is VOID.

6. **E6 (finding 6, BLOCKING: the engine's rate line is never parsed).** ACCEPTED. The worker's StateDataReporter file (the
   `out_json + ".log"` in `work_m4`) is copied to `results_m4/out/` and is the file parsed for the engine's ns/day; the tool's
   stdout log is not. `rates_disagree` then works as answer 7(c) and item 17 say (more than 5 percent apart: label "engine rate
   and wall-clock disagree", both reported). The unit-and-scale record carries the engine rate lines. If the rate file exists
   and no rate line parses, the row carries `engine_ns_per_day: null` and the label "engine rate line missing"; the C2 decision
   still rests on the wall-clock figure. The C4 MD bytes count the trajectory and every log of the segment, this file included.
   Selftest: a planted file in the reporter's real column layout parses to its number; a planted file with no rate line gives
   null and the label; the disagreement label fires on a planted 129 versus 100.

7. **E7 (finding 7, BLOCKING: the empty-input control runs a tool, not the harness).** ACCEPTED, as answer 7(b) says. The
   empty-input control times the harness itself: the same timer, work-directory creation and record path as a real call, around
   a no-op command (`/bin/true` or `sleep 0`) with no AlphaFold, JAX, TensorFlow or docking import, and measures the bytes in the
   directory that harness call created. `adjusted_seconds` subtracts only that harness overhead. The 2 s and 1 MiB thresholds
   and the "setup overhead subtracted" label stand. Selftest: a planted slow-import tool is not what the control times; a planted
   harness overhead of 5 s triggers the label and the subtraction; 0.5 s and 100 KiB do not.

8. **E8 (finding 8, BLOCKING: no pose and tool timeouts become an anchor miss, exit 4).** ACCEPTED, three routes, no overlap.
   (a) A docking call that exceeds its allowance is a ceiling stop: exit 3, run_valid as it was, the anchor undecided, C1 to C4
   VOID "unmeasured, not holding" with the full incomplete-run label; it falls under A2(b). (b) A docking tool that exits
   non-zero, or exits zero and leaves no parsable ranked pose, is a harness failure: exit 2, run_valid false, raw output kept;
   it falls under A2(a) and is not an anchor result. (c) Exit 4 only when a pose was obtained and compared and the tolerance
   was missed. `anchor_decision` never receives a missing pose. Selftest: the three routes planted in the stage flow with the
   expected exit code, run_valid and records for each.

9. **E9 (finding 9, BLOCKING: `m4_summary.json` does not state the stand-in scope first).** ACCEPTED. The summary is written
   without `sort_keys` and with `what_this_run_decides` as its first key (stand-in protocol only), then the run_valid and exit
   fields, the records, the gate result, the fallback text and `unmeasured_inputs`. Other JSON files may stay sorted. Selftest
   reads the written file as text and checks that the first key is `what_this_run_decides`, not only that the key exists.

10. **E10 (finding 10, BLOCKING: per-record labels are missing).** ACCEPTED. Every measured record's `machine` carries: the CUDA
    runtime version (the driver's "CUDA Version" from the `nvidia-smi` header, parsed, plus the JAX CUDA plugin package version
    from pip; absent values are written as null with a reason, never omitted); start and end wall-clock (UTC, ISO 8601, of the
    stage or run that produced the value, not the record's write time); the AlphaFold parameter archive sha256; the JAX,
    jaxlib and CUDA-plugin versions and the wheel build tags from the pip report (the build flags as far as a wheel states them);
    the OpenMM version, platform and precision; the docking code and version; instance type, GPU name and driver; price per
    hour. Selftest: a planted `nvidia-smi` header parses to its CUDA version; every record kind written by the selftest flow
    carries every label key.

11. **E11 (finding 11, BLOCKING: the C2 record omits the atom counts and engine precision).** ACCEPTED. The C2 record's `values`
    carries the atom count of each complex, the engine precision, platform and version, `timestep_fs`, `production_ns`, `n` and
    the per-complex wall-clock and engine rates, in addition to the item-6 labels. Selftest: a planted C2 record has these keys.

### Advisory findings (E12 to E26)

12. **E12 (finding 12, package forms unverified).** ACCEPTED as a risk, no new authorisation. The build chooses the package forms
    whose package metadata carries what the smoke check imports (colabfold with its `alphafold` extra if the pinned release
    declares one; the OpenMM form that carries the CUDA platform if the pinned release declares one), pins every version, and
    leaves the verdict to the smoke check, as B6 says. A smoke-check failure is exit 2, a clean void record, and A2(a) covers the
    relaunch; the cause is recorded in RUN.md and the build is re-run, not patched. The reviewer's recollection is not a ruling.

13. **E13 (finding 13, docking CLI and output format untested before the paid anchor).** ACCEPTED in part. The fallback to the
    lexicographically first pose is removed: the top pose is the first row of the tool's own rank list by its score, and if
    the named pose file is missing the run is exit 2 (E8b), never `sorted(glob)[0]`. The first thing the anchor stage does with
    the docking output is parse the rank table; an unparsable table is exit 2 with the raw table kept in `results_m4/out/`, so the
    format is learned from the first launch's void record under A2(a). The smoke check stays `--help` only (a trial docking
    inside the install ceiling is not authorised: it would spend the install allowance on an untested guess). Selftest: planted
    rank tables with the columns the design assumes parse; a table without a rank column is refused, not guessed.

14. **E14 (finding 14, onbox steps before the first stage can fail with no void record).** ACCEPTED. `python3-venv` joins the
    declared apt packages (recorded with version and `apt-cache show` sha256, B13). `pip install --upgrade pip` is removed: no
    unrecorded download; the venv's bundled pip is used and pinned packages are installed with `--report`. `onbox_m4.sh` sets its
    exit trap before the venv step, so any abort before `run_m4.py` starts writes a minimal void record, `RUN_VALID.json`
    (false) and `RUN_DONE` with exit 2 from the shell itself (stdlib `python3 -c` or plain shell, no venv needed).

15. **E15 (finding 15, failing control and anchor records carry run_valid true).** ACCEPTED; item 3's sentence is revised. The
    run is marked invalid before the failing record is written, so the failing sleep record, the failing anchor record and every
    record after carry `run_valid` false; records written before the failing decision keep true. `RUN_VALID.json` and the
    summary agree. Selftest: a planted sleep failure and a planted anchor miss produce a failing record with `run_valid` false.

16. **E16 (finding 16, `estimated_s` is never passed to the guard).** ACCEPTED. Every `guard_before_stage` call and every unit
    inside a stage passes an estimate: the mean of the finished units of that kind if any, else a stated floor (anchor serial or
    parallel 60 s, docking pair 60 s, AlphaFold run 120 s, MD complex 150 s, storage 20 s, endpoints 30 s). A unit whose
    estimate exceeds the allowance is not started and is recorded as a guard stop (B2 path, exit 3). This also supplies the
    "guard arithmetic from measured rates" the reviewer says the contract wants (E28). Selftest: a planted stage with 100 s left
    and a 150 s estimate is not started.

17. **E17 (finding 17, `stage_aux` after a ceiling stop with 2 of 3 pairs is recorded as done).** ACCEPTED. A stage that
    stopped on a ceiling, guard or timeout is not in `stages_done` even when it returned normally; C3 stays decided on the two
    finished pairs (B8). Selftest: flow (d) asserts `stages_done` lacks the stage and C3 is decided on 2.

18. **E18 (finding 18, one launcher fetch line not in frozen).** ACCEPTED as additive and harmless; not a build matter. The
    operator declares it in the header of `lambda_run_m4.sh` (see Operator actions). Nothing changes in the build's two files,
    which already write `RUN_VALID.json`.

19. **E19 (finding 19, frozen bootstrap time before T0 is unrecorded and eats the margin).** ACCEPTED, handled in the build, not by
    editing the frozen file. `onbox_m4.sh` sets its T0 to the start of its parent `remote_run_m4.sh` (`ps -o etimes= -p $PPID`),
    plus 30 s for the ssh start, so the bootstrap counts against `REMOTE_TIMEOUT` and `STOP_AT`; if the parent time cannot be
    read, it assumes 300 s and labels "bootstrap time assumed 300 s". The pre-T0 seconds are recorded in `env.txt` and the
    summary. Stage allowances already take the lesser of ceiling and time left, so a slow bootstrap shortens the stages near the
    end instead of eating the 400 s margin. The 7,200 s ceiling sum is a ceiling sum, not a promise. Selftest: a planted `etimes`
    value moves T0; a garbage value takes the 300 s default and the label.

20. **E20 (finding 20, writes and sudo beyond the declaration).** ACCEPTED in part. Caches the build controls are moved under
    `~/m4_run/`: `PIP_CACHE_DIR`, `XDG_CACHE_HOME`, `MPLCONFIGDIR`, `JAX_COMPILATION_CACHE_DIR` (if used) and `TMPDIR` point
    there. The frozen bootstrap's `~/.local` installs are the operator's file and stay: the payload rule of 5 concerns what the
    build writes and ships, and the bootstrap is not the build's. `sudo -n env DEBIAN_FRONTEND=noninteractive apt-get update`
    is accepted as the mandatory first step of the declared apt installs; no other sudo call is allowed, and the apt packages
    stay the declared ones only.

21. **E21 (finding 21, C1 `gate_pass` reported on a VOID C1).** ACCEPTED. `gate_pass` is computed only when C1 holds a valid
    measurement: PASS, FAIL, and the marginal VOID (a real number the gate can read, answer 9 keeps `gate_pass` there). For a VOID
    from not-an-A100, a below-minimum count, zero spread, a stop or `download_in_timed_call`, `gate_pass` is null and
    `gate: "not evaluated: C1 VOID (<reason>)"`. The summary does not restate the fallback text as triggered for a null gate.
    Selftest: planted VOID reasons give null; 1.2 (marginal) gives false with the fallback text; 0.9 gives true.

22. **E22 (finding 22, exit 3 also returned for VOIDs that are not guard stops).** ACCEPTED; item 29 is revised. Exit 3 only when
    a guard stop, ceiling stop, tool timeout or outer timeout left an input unmeasured. VOIDs by rule with no stop (not an A100,
    zero spread, a marginal value) end with exit 0; `RUN_DONE` carries the exit code and the void reasons per input. Exit 2 and 4
    as before. A2(b) therefore reads exit 3 only as "stopped on its time guard". Selftest: planted not-an-A100 and zero-spread
    flows exit 0 with the VOIDs; planted stop flows exit 3.

23. **E23 (finding 23, outer-timeout edge cases).** ACCEPTED. (a) `onbox_m4.sh` routes rc 124 and rc 137 as the outer-timeout
    route (exit 3 path, B12) when elapsed time since T0 is at least the outer deadline minus 5 s; rc 137 earlier than that is a
    failure (exit 2, a kill by something else). (b) `kill_recorded_groups` records, with each pgid, the leader's `/proc/<pid>/stat`
    start time and command name, removes the entry when the tool returns, and signals a group only if its leader is alive and
    both still match; otherwise it skips it and writes the skip to the log. Selftest: planted rc 137 at the deadline routes to
    exit 3, rc 137 at 100 s to exit 2; a planted stale pgid entry whose start time differs is not signalled.

24. **E24 (finding 24, pip report hash not cited in `inputs`).** ACCEPTED; item 34 stands as written and the build does it: each
    record's `inputs` lists the pip report file with its sha256 and the apt hash file, besides the rows file. Selftest: a C record
    from the selftest flow has an `inputs` entry for the pip report.

25. **E25 (finding 25, C4 docking bytes under-count).** ACCEPTED. The docking bytes of one pair are the apparent bytes of the whole
    per-pair docking output directory tree (setup files and copied structures, swarm directories, rank tables, every pose file
    the tool wrote), not `Path(pose).parent`. Selftest: a planted tree with a nested swarm directory and a top-level
    `setup.json` sums every file.

26. **E26 (finding 26, `frozen/ONBOX_CONTRACT.md` was not reviewed).** ACCEPTED. The contract stays binding under rule 5, its stage
    order, guards, record fields, selftest contract and failure checks are directive, and nothing here loosens it; the build reads
    it. The gate did not read it either (it is not on the gate's list) and rules only on what the report says about it: stage
    order matches item 1, records and state are atomic, guard arithmetic from measured rates exists only in the AlphaFold loop;
    the last is answered by E16. The next review must have the contract on its read list and check the build against it.

### Operator findings and checklist summary (E27, E28)

27. **E27 (the three operator findings, verified by the reviewer).** ACCEPTED AS-IS. (1) `M4_OUT_DIR`, `REMOTE_T` and `STOP_AT` are
    set before first use: not defects. (2) Only the two files were written, selftest 253 of 253, hashes and line counts match the
    build return: nothing changes. (3) The contract was not read by the reviewer: see E26.

28. **E28 (checklist summary, points 1 to 8).** ACCEPTED. Point 1 (EXEC_NOTE items 6, 8, 12, 13, 14, 17, 20, 28, 29, 30 and 33 not
    carried) is the list answered by E1 to E11 and E15 to E17, and those items are revised in EXEC_NOTE. Points 2 to 6 and 8 (cost
    and time clamps, records, secrets, writes, launcher copy, `onbox_command`) read as carried or are answered above; nothing more
    changes. Point 7 (the selftest runs fakes for the stages and never runs the real `stage_*` bodies, so findings 1, 3, 5, 6 and 7
    were invisible) is BINDING on the build: the selftest must also run the real `stage_*` bodies, with the tool runner,
    clock and filesystem roots injected and fake tool executables placed in a planted venv bin directory (stdlib only, no GPU,
    no network, still under 300 s), asserting at least: tools resolve through the venv PATH (E1), the parameter directory is
    populated before a timed call (E3), pair assertions (E4), the MD input holds both chain roles (E5), the engine rate file is
    parsed (E6), the empty-run control times the harness (E7), and the three docking failure routes (E8). The selftest's count
    line and file-hash line stay as in B14.

**Checks the gate made before answering (addendum).** Arithmetic and cross-reading only. Cap: 7,200 s = 2.00 h x 1.99 = 3.98;
two launches 7.96; with 600 s each outside 8.62; under 10. Ceilings unchanged and still sum to 7,200: 1,800 + 700 + 600 + 2,000 +
1,600 + 100 + 400 = 7,200. Hitting the install total now ends in exit 2, not 3 (E2); the earlier B8 text about ceiling stops
applies to the later stages only. MD per complex: 0.5 ns at 129 ns/day is 335 s, inside the 600 s per-complex cap with system
build and equilibration; at 60 ns/day it is 720 s and the complex is cut by the cap (C2 then rests on fewer complexes, minimum 2
of 3). Estimate floors of E16 (60, 60, 120, 150, 20, 30 s) are each below their ceiling. E21 keeps the answer-9 planted case 1.2
(VOID, marginal, `gate_pass` false). Counting: the report has 26 numbered findings (11 + 15), 3 operator findings and an 8-point
summary; answers E1 to E28 cover all.

**Pre-authorisation (addendum).** Unchanged: A1 and A2 stand. A launch-1 halt for a toolchain, install, parameter-extraction,
docking-format or bootstrap reason is under A2(a); a ceiling or time-guard stop with inputs unmeasured is under A2(b). A failed
smoke check or a docking table that does not parse is exit 2 and falls under A2(a), not an anchor result. No launch is authorised
until the new build exists, its selftest passes with matching hashes (B14), and the operator has diffed `lambda_run_m4.sh`
against `frozen/lambda_run.sh` and declared the fetch line of E18.

Build 5 authorised

## Operator actions

OPERATOR: declare in the header of `lambda_run_m4.sh` the added fetch line for `results_m4/out/RUN_VALID.json` (or remove it; the out directory fetch already covers the file) and re-diff the file against `frozen/lambda_run.sh` before launch 1.
OPERATOR: leave `remote_run_m4.sh` as `frozen/remote_run.sh` with only the `cd` line changed to `~/m4_run`; the build now counts the bootstrap time itself, so no change to the frozen bootstrap is needed.
OPERATOR: before launch 1 re-run `python3 run_m4.py --selftest` locally and compare the two printed sha256 values with the files on disk; keep `REMOTE_TIMEOUT=7200`, `BUDGET_LEFT_USD=5`, `PRICE_USD_PER_HOUR=1.99` (or the chosen instance's price, at most 2.50) and `INSTANCE_TYPE` forwarded as before.

---

## Addendum 6 (2026-10-21)

Rules on `out/gate_report_build7.md`: the operator's mechanical note (three rulings asked: (a), (b), (c)) and review 3 of build 7
(execution layer, run on `wf.js`; verdict FAIL: 7 BLOCKING, 10 ADVISORY, 4 operator findings it verified, an 8-point checklist
summary). Inputs added for this addendum: that report, this file as it stood, `EXEC_NOTE.md` as it stood, and the task text of
this session, which is not a source of rulings. The gate ran nothing and did not read `run_m4.py`, `onbox_m4.sh` or
`frozen/ONBOX_CONTRACT.md`; each ruling rests on the reviewer's line references, taken as reported, and the reviewer's
"unverified" and "as far as I recall" findings are ruled as risks with a mechanical test or an operator check, never on the
recollection itself. The two shape-example files named in the task are outside this session's readable directory; this addendum
follows the shape of the sections above. Every earlier section stands except where an answer below says it is superseded: F14
supersedes the "no `pip install --upgrade pip`" sentence of E14, and F8 restates the controls and anchor ceiling of B8. Answers
are numbered F1 to F22: F1 to F7 the blocking findings (report numbers 1 to 7), F8 to F17 the advisory findings (report numbers 8
to 17), F18 the four operator findings, F19 the checklist summary, F20 to F22 the operator's three asks (a), (b), (c). Counts: 22
answers. The line `Build 6 authorised` at the end is the launcher's literal string for the next build; it does not renumber the
earlier builds (the build it authorises is build 8).

**Decision on budget and build (addendum).** GO stands. No GPU money has been spent: no launch record is among the inputs and
review 3 ran nothing. Cap arithmetic unchanged: 2 launches x 2.00 h x USD 1.99 = USD 7.96; with 600 s outside each, 2 x (7,200 +
600) s = 15,600 s = 4.333 h x 1.99 = USD 8.62; under the USD 10 cap with USD 1.38 left; `BUDGET_LEFT_USD=5` per launch above the
3.98 a launch can cost. No ruling below adds a launch, a download source or install time beyond the 1,800 s install total (the
pip bootstrap of F14 and the bounded apt calls of F7 sit inside it). Findings 1, 2, 3, 4, 5 and 7 would each have spent a launch
with a wrong outcome or an unscorable record; finding 6 would have spent the install stage; that is why they are binding.

### Blocking findings (F1 to F7)

1. **F1 (finding 1, BLOCKING: `set -e` aborts `onbox_m4.sh` on the runner's exit 3; the trap then overwrites the outcome).**
   ACCEPTED. In `onbox_m4.sh` no command whose non-zero status is an expected outcome (`run_m4.py`, `run_m4.py --finalize`, the
   outer `timeout`, any `kill_recorded_groups` helper) is ever run bare under `set -e`: each is written in the form
   `RC=0; <command> || RC=$?` (or runs between `set +e` and `set -e`), and the route table after it reads `RC`. The EXIT trap acts
   only while `FINISHED=0`; every normal route (runner rc 0, 2, 3, 4, outer timeout 124 or 137) sets `FINISHED=1` before the script's
   own `exit`. The outer-timeout route ends as exit 3 with run_valid as it was. Tests: item 48 of EXEC_NOTE (shell-level flows) and a
   static check that no line invoking the runner lacks the `|| RC=$?` form.

2. **F2 (finding 2, BLOCKING: `--finalize` builds a fresh `RunState`; decided inputs are reported unmeasured).** ACCEPTED. The
   finalize path rebuilds status from the records on disk, as EXEC_NOTE item 49 states: decided records are read and never
   rewritten, `run_valid` is read from `RUN_VALID.json` and the records (false if any says false), the anchor decision from its
   record, and only inputs with no decided record become `unmeasured_by_stop:outer_timeout`. A relaunch of a decided input
   stays unauthorised (A2), which is why a wrong "unmeasured" there is blocking. Test: a planted output directory holding a decided C3
   and no other record; finalize reports C3 decided (and its record byte-identical afterwards), C1, C2 and C4 unmeasured, run_valid
   true, exit 3.

3. **F3 (finding 3, BLOCKING: C4's MD bytes are not the quantity item 16 defines; no trajectory, no frame interval).** ACCEPTED.
   The MD worker writes a trajectory with OpenMM's `DCDReporter` at a fixed frame interval of 10 ps (5,000 steps at 2 fs, 50
   frames over the 0.5 ns segment), recorded as `frame_interval_ps` on the MD row and in C4's values; the interval is a recorded
   choice and is not tuned toward the band. The MD bytes of C4 are the apparent bytes of the trajectory file plus every log of the
   segment (the reporter file, the tool's stdout and stderr logs, the worker's build and run JSON files); `system.xml`,
   `solvated.pdb` and any checkpoint are not in the decision value and are reported as `md_setup_bytes` (information).
   `md_bytes_per_ns` is the MD bytes over the 0.5 ns production. Test: item 16 and item 47 as revised (a planted `md_` directory
   with a 1,000-byte trajectory, 100-byte reporter file, 24-byte log, 5,000-byte `system.xml` and 7,000-byte `solvated.pdb`
   gives MD bytes 1,124 and `md_setup_bytes` 12,000; the worker's source text names `DCDReporter`; a real-stage-body run with a
   fake worker that writes a trajectory records a non-null `frame_interval_ps`).

4. **F4 (finding 4, BLOCKING: a pair at its 250 s cap ends the pair loop, so pairs 2 and 3 never run).** ACCEPTED. The pair loop
   keeps the capped pair as a `truncated: true` row and continues with the next pair; it stops only when the stage allowance is
   gone or the guard refuses a unit (estimate above allowance, item 43). C3 is decided when at least 2 pairs finished (not
   truncated), else VOID with every row kept. Test, in the real `stage_aux` body with a fake docking runner: pair 1 capped, pairs 2
   and 3 finished gives 3 rows (one truncated), n=2, C3 decided; pairs 1 and 2 capped and pair 3 finished gives 3 rows, n=1, C3
   VOID; the number of attempted pairs equals 3 in both.

5. **F5 (finding 5, BLOCKING: `write_minimal_void` always writes run_valid false, including for exit 3 and exit 0).** ACCEPTED.
   `write_minimal_void <code>` follows the item 8 table: code 2 and code 4 write `run_valid: false`; code 3 writes
   `run_valid: true` unless an existing `RUN_VALID.json` says false, in which case false is kept (a guard stop leaves run_valid as it
   was); code 0 is never passed (a runner that returns 0 without a `RUN_DONE` is treated as code 2). The shell calls it only when
   the runner has not written `RUN_DONE`; when the runner wrote `RUN_DONE` and `RUN_VALID.json`, the shell neither rewrites them nor
   lets the trap rewrite them, and its own exit code equals the one in `RUN_DONE`. The "no time left after setting up" path
   (the code-3 call at report line 226) writes run_valid true, exit 3, label "incomplete run: unmeasured inputs are VOID, not
   holding". Test: item 48 flows.

6. **F6 (finding 6, BLOCKING: `PIP_PINS` names plain `openmm==8.2.0`; item 33 requires the CUDA-carrying form).** ACCEPTED, and
   made mechanical because the reviewer's recollection is not a ruling and the gate cannot read package metadata. The build
   writes the OpenMM requirement in the form that pulls the CUDA platform: the pinned release's CUDA extra (`openmm[cuda12]` if
   that extra is declared by 8.2.0) or a sibling pinned requirement whose distribution name starts `openmm-cuda`; which form it
   chose, and that it is a choice, is stated in a comment on `PIP_PINS`. Every entry of `PIP_PINS` is `name==version`
   (extras in brackets allowed). The metadata question (does the pinned release declare the extra, is the CUDA plugin
   distribution's name as written) is decided by the operator's check before launch 1 (Operator actions); a mismatch is a build
   re-run under A2(a)'s rule, never a hand edit. The smoke check of item 33 stays the in-box test. Test: a planted `PIP_PINS`
   parser case: the OpenMM entry carries an extra or has an `openmm-cuda*` sibling; an entry without `==` fails the selftest.

7. **F7 (finding 7, BLOCKING: `apt-get update` and `apt-get install` have no `timeout`).** ACCEPTED. Every apt call in
   `onbox_m4.sh` runs as `timeout -k 10 <limit> sudo -n env DEBIAN_FRONTEND=noninteractive apt-get ...`, with
   `limit = min(its own limit, 1,800 minus install seconds used so far, REMOTE_TIMEOUT minus elapsed minus 500)` (item 28's
   install running total, kept in the shell as seconds since T0 minus the seconds at install start, not only counted afterwards).
   `apt-get update` keeps its retries (at most 10 tries, 15 s apart) but each try takes its own `timeout` and the whole update
   loop is bounded at 300 s. A call that times out, or an exhausted install total, is exit 2 with a void record (E2; A2(a)); no
   guard exists yet at this point, so the shell writes the void record itself (F11). Test: item 48 (a planted `sudo` that
   sleeps 60 s with the test install ceiling at 3 s ends the script as exit 2 within 30 s with the void record).

### Advisory findings (F8 to F17)

8. **F8 (finding 8, ADVISORY: controls and anchor take separate 700 s allowances, up to about 770 s together).** ACCEPTED AS BUILT, with
   item 28 restated to say what is true: controls and anchor are two stages with separate allowances (the controls take about 70 s
   in practice: the 60 s sleep and the empty run), the combined use is bounded by 1,400 s in the worst case and about 770 s in
   practice; the 400 s margin absorbs the 70 s. What guarantees the 7,200 s is the allowance clamp (the lesser of ceiling and time
   left minus margin and endpoints slot), not the ceiling sum, and item 28 now says so. No code change; planted clamp cases are in
   item 28.

9. **F9 (finding 9, ADVISORY: the unit-and-scale record holds worked examples only; item 20 lists raw values that cannot exist
   before the controls).** ACCEPTED; the directive was self-contradictory and is corrected, not the build. The record written
   after the controls states what it holds: `values.kind: "worked_examples"` and `values.raw_values_in` listing the rows files that
   will hold the raw AlphaFold seconds, engine rate lines and bytes. The raw values are not copied into a second record. Item
   20 and answer 7(c) are read that way (the raw values exist in the rows files and the band comparison still waits for the
   controls). Test: the planted record has both keys and `raw_values_in` names the AlphaFold, MD and storage rows files.

10. **F10 (finding 10, ADVISORY: `spend_usd` adds `pre_t0_seconds` although T0 already includes the bootstrap).** ACCEPTED; numbered
    item 53. `estimated_spend_usd` = (seconds since T0) x price / 3,600 and nothing else; the pre-T0 seconds are reported
    beside it, not added. The guard already used `stop_at_s`. Test: planted elapsed 3,600 s with pre-T0 300 s gives 1.99, not 2.14;
    7,200 s gives 3.98.

11. **F11 (finding 11, ADVISORY: the shell's minimal void records lack `unit`, `card_value`, `band`, and no `env.txt` or
    `m4_summary.json` is written on an early abort).** ACCEPTED, because rule 6 asks a script to score the records without a model
    and a shell abort is a launch outcome. Numbered item 54: the shell's minimal void writes `env.txt` (named non-secret variables,
    including the `REMOTE_TIMEOUT` seen), `m4_summary.json` (first key `what_this_run_decides`), an anchor record and C1 to C4
    records, each with the provenance.py keys, `values.measured` null, `values.unit`, `values.card_value`, `values.band`, `decision`
    VOID, `run_valid` per F5, and `RUN_VALID.json` and `RUN_DONE`. It writes through `frozen/provenance.py` when that imports under
    the system `python3` (stdlib), else with the same keys by hand. Test: item 48 flows read these files.

12. **F12 (finding 12, ADVISORY, unverified: no completion marker in `params/`, so colabfold may fetch its own archive inside the
    first timed call and C1 is VOID with exit 0).** ACCEPTED as a risk and made a numbered item (51), because that outcome would
    consume the launch with no relaunch authorised. After extraction the build reads the installed colabfold's own download
    module in the venv (the Python source file under the package directory) for the completion-marker file name(s) it checks,
    writes exactly those marker files into `<data>/params`, and records the names it found; if the module names no marker, it
    writes none and records "no marker named". Marker names are never hard-coded from memory. The E3 rule stands (a download in a
    timed call voids C1). Pre-authorisation A2 gains (c) below. Test: a planted package source naming a marker yields that marker
    file; one naming none yields none and the record; a planted module naming two markers writes both.

13. **F13 (finding 13, ADVISORY, unverified: no conformation-generating step; `-s 2` swarms; an anchor miss is probable).** ACCEPTED in
    part. (a) The build restores the docking step that writes the pose files, between simulation and ranking (simulate, then the
    docking package's conformation-generating script, then `lgd_rank.py`), unless `frozen/ONBOX_CONTRACT.md` states a different
    order, in which case the contract's order is followed and recorded. The smoke check adds that script's `--help` and its
    `shutil.which` path. A missing pose file stays exit 2 (E8b). (b) The swarm count and other docking parameters are the build's
    engineering choice, are the same for the anchor and for the pair dockings, are recorded in the anchor record
    (`values.docking_parameters`), and are not restrained toward the published interface: restraining to 6IHB contacts would make
    the anchor trivially pass and is not authorised. A miss with a pose obtained and compared is exit 4 and a result; no relaunch (A2).
    Item 52. Test: the planted docking call sequence is simulate, generate, rank in that order; the anchor record has
    `docking_parameters`; a fake docking tool that skips generation gives exit 2 (no pose file).

14. **F14 (finding 14, ADVISORY, unverified: `pip install --report` needs pip 22.2 or later; Ubuntu 22.04's venv pip may be
    22.0.2; E14 forbids upgrading).** ACCEPTED, and E14's ban is superseded in this one respect, because failing the first install
    step as exit 2 would spend a launch on a known toolchain gap. Item 50: the build reads `pip --version`; if it is 22.2 or later
    it proceeds; if earlier it runs one recorded bootstrap inside the install total: download `pip==24.0` with `pip download
    pip==24.0 --no-deps` into a directory under `~/m4_run/` with the verbose log kept, compute the wheel's sha256 itself, record
    URL (from the log), hash and wall-clock in the downloads file, then install that local wheel with `--no-index`; every later
    install uses `--report`. No other pip upgrade is allowed. The source is PyPI, which is already a named source (item 14).
    Test: planted `pip --version` strings: "pip 22.0.2 ..." selects the bootstrap, "pip 23.0.1 ..." does not, and a garbage string is
    exit 2; the bootstrap's recorded entry has URL, sha256 and seconds.

15. **F15 (finding 15, ADVISORY: the launcher copy keeps `REMOTE_TIMEOUT=${REMOTE_TIMEOUT:-5400}`).** ACCEPTED; operator matter, no
    build change. The launch environment sets `REMOTE_TIMEOUT=7200` explicitly, and the copy's default is changed to 7200 and declared
    in its header (Operator actions). The build already labels an unset value (item 9).

16. **F16 (finding 16, ADVISORY: after an anchor miss C1 to C4 are written "unmeasured, not holding" and `RUN_DONE` says
    `unmeasured_by_a_stop`).** ACCEPTED; item 46 is revised. `RUN_DONE` names, per input, exactly one of `decided`,
    `void_by_rule:<reason>`, `unmeasured_by_stop:<stop kind>`, `void_by_anchor_miss`, `void_by_failure:<kind>`. After exit 4 every
    input is `void_by_anchor_miss` and none is `unmeasured_by_stop`; after exit 2 every input not decided before the failure is
    `void_by_failure:<kind>`. The record labels stay as before and each voided record also carries `voided_by`. Test: the planted
    anchor-miss flow (f) and failure flow (e) assert these strings.

17. **F17 (finding 17, ADVISORY: the selftest never runs the shell script or `--finalize`).** ACCEPTED and made binding, because
    findings 1, 2 and 5 sit entirely in that gap. Item 48 adds a shell-level layer and item 49 a finalize layer, both inside the
    selftest. The shell layer runs `onbox_m4.sh` itself through `subprocess` (stdlib; `bash` is required, a missing `bash` is a
    selftest FAIL, not a skip) in a temporary root, with planted runner exit codes, under the test hook defined in item 48. Still
    no GPU, no network, under 300 s.

### Operator findings and checklist summary (F18, F19)

18. **F18 (the four operator findings, verified by the reviewer).** ACCEPTED AS-IS. (1) `M4_BASE` is read only as a fallback after
    `--base` and the script always passes `--base`: not a defect. (2) The `.keys` text at `run_m4.py:5389` is a selftest regex over
    the program's own source; nothing reads `.keys`: not a defect. (3) Only `run_m4.py` and `onbox_m4.sh` are new under the run
    directory: consistent with rule 5. (4) The contract binding: stands; on its docking order the answer is F13(a) (the contract's
    order wins where it states one).

19. **F19 (checklist summary, points 1 to 8).** ACCEPTED. Point 1 (EXEC_NOTE items 16, 28, 29, 32, 33 and 46 not carried) is answered
    by F1 to F7 and F16 and those items are revised in EXEC_NOTE. Point 2 (cost and time; apt is the unbounded step) is F7. Point
    3 (finalize loses decided status) is F2. Points 4 to 6 (secrets clean; writes only under `~/m4_run/`; launcher differs only at
    declared points) and 8 (`onbox_command` is `bash remote_run_m4.sh bash onbox_m4.sh`) read as carried; nothing changes
    except F15's launcher default. Point 7 (selftest log ends `selftest: PASS`, 418 of 418, hashes agree with the build return):
    accepted as evidence; the operator's local re-run and hash comparison (B14) remains the check, and the next count will be
    higher because items 48 and 49 add cases.

### The operator's three asks (F20 to F22)

20. **F20 (ask (a): each item cited in two or more reviews restated as one unambiguous, mechanically testable requirement with a planted
    selftest case, or dropped with the reason).** ACCEPTED; none is dropped, because each carries a standing rule (items 6, 8 and 29
    carry rules 6, 4 and 3 and 4; item 28 carries rule 2). In EXEC_NOTE, items 28 and 29 (cited in all three reviews) and items 6 and 8
    (cited in two) are rewritten in place, marked `(revised, addendum 6)`: item 6 as a per-record-kind key list held in one constant
    that the selftest checks against every record the flow writes; item 8 as a table of events with exit code, run_valid and
    `RUN_DONE` status; item 28 as a ceiling table plus one allowance formula with planted clamp values; item 29 as six numbered
    consequences of a stop, each with its planted flow. Review 4 judges the build against those restated texts, not against the older prose.

21. **F21 (ask (b): every advisory finding accepted as-is for launch 1 of record, or made a numbered item).** Rulings: F8 accepted as
    built (item 28 restated, no code change); F9 numbered as the corrected wording of item 20 (no new item); F10 numbered item 53; F11
    numbered item 54; F12 numbered item 51; F13 numbered item 52; F14 numbered item 50; F15 accepted as an operator matter (no build
    item); F16 numbered as the revision of item 46; F17 numbered items 48 and 49. No advisory is left unanswered and none is deferred
    silently. The four findings the reviewer marked "unverified" (F12, F13, F14, and F6's metadata) are ruled as mechanical items and
    operator checks, not as facts.

22. **F22 (ask (c): is build 8 authorised; may launch 1 proceed on build 8 if review 4 reports zero blocking findings whatever its
    advisory ones).** BUILD 8 IS AUTHORISED (the literal line below). YES: if review 4 of build 8 reports zero BLOCKING findings, launch
    1 may proceed on build 8 with its advisory findings recorded in RUN.md and not ruled again, provided all of: (i) the build's own
    selftest passes and the operator's local re-run prints the same two sha256 values as the files on disk (B14); (ii) the operator
    actions below are done; (iii) review 4 had `frozen/ONBOX_CONTRACT.md` on its read list (E26) and states it checked against it;
    (iv) A1's instance and cap limits hold. "Blocking" means a finding that would make a launch end with the wrong exit code or
    run_valid, an unscorable or missing record, a repeat of a decided input, a spend past the caps, or a read of a secret; an advisory
    is anything else. If review 4 reports any blocking finding, the gate rules again in an addendum 7, and no launch happens. No GPU
    money is spent by builds or reviews, so this loop costs no launch budget.

**Checks the gate made before answering (addendum).** Arithmetic and cross-reading only. Cap: 7,200 s = 2.00 h x 1.99 = 3.98; two
launches 7.96; with 600 s each outside 8.62; under 10. Ceilings unchanged: 1,800 + 700 + 600 + 2,000 + 1,600 + 100 + 400 = 7,200;
the controls (about 70 s) add to that only against the 400 s margin (F8), and the allowance clamp is what holds the total. F7: the
update loop bound 300 s and each install call limit sit inside the 1,800 s install total. F10 planted: 300 s of bootstrap is already
inside T0, so 3,600 s since T0 is USD 1.99 (3,600 / 3,600 x 1.99), and the wrong figure the finding describes is (3,600 + 300) / 3,600
x 1.99 = 2.156. F3 planted: 1,000 + 100 + 24 = 1,124 and 5,000 + 7,000 = 12,000; 50 frames x 10 ps = 0.5 ns. F4 planted: pair caps
250 + 250 leave 100 s of the 600 s stage total, above the 60 s pair estimate, so a third pair still starts. Counting: the report has
17 numbered findings (7 blocking, 10 advisory), 4 operator findings, an 8-point summary and 3 asks; answers F1 to F22 cover all.
The report's checklist point 7 (418 of 418) was not re-run; the gate cannot.

**Pre-authorisation (addendum).** A1 stands unchanged. A2 stands with one addition: **A2(c)** launch 2 is also authorised, within the
same USD 10 total, if launch 1 ended with C1 VOID for `download_in_timed_call` (no measurement exists for it; the cause is recorded in
RUN.md and the build is re-run if its code changes); launch 2 then reruns the anchor first and only the unfinished inputs. A shell
abort before `run_m4.py` starts (exit 2 with the shell's void record, F11) is a halt under A2(a). Not authorised, as before: a
relaunch to double seeds, to repeat a decided input, to change a band, or after an anchor miss. No launch is authorised until the
new build exists, its selftest passes with matching hashes (B14), review 4 meets F22, and the operator has done the actions below.

Build 6 authorised

## Operator actions

OPERATOR: the three lines of addendum 5 stand (declare the `RUN_VALID.json` fetch line in the header of `lambda_run_m4.sh`; `remote_run_m4.sh` is `frozen/remote_run.sh` with only the `cd` line changed to `~/m4_run`; re-run `python3 run_m4.py --selftest` locally and compare the two sha256 values with the files on disk before launch 1).
OPERATOR: set `REMOTE_TIMEOUT=7200` in the launch environment and change line 41 of `lambda_run_m4.sh` from `${REMOTE_TIMEOUT:-5400}` to `${REMOTE_TIMEOUT:-7200}`, declared in the file's header with the other changed points (F15).
OPERATOR: before launch 1 read the package-index metadata for every requirement in `PIP_PINS` of `run_m4.py` (each pinned version exists; each extra named in a requirement is declared by that release; any `openmm-cuda*` sibling name exists) and write the result into RUN.md; a mismatch is a build re-run, not a hand edit (F6).
OPERATOR: put `frozen/ONBOX_CONTRACT.md` on the read list of review 4 (F22).

---

## Addendum 7 (2026-10-21)

Rules on `out/gate_report_build9.md`: the operator's mechanical note (three rulings asked: (a), (b), (c)) and review 4 of build 9
(execution layer, run on `wf.js`; verdict FAIL: 1 BLOCKING, 3 ADVISORY, a "verified, no finding" list). Inputs added for this
addendum: that report, this file as it stood, `EXEC_NOTE.md` as it stood, and the task text of this session, which is not a
source of rulings. The gate ran nothing and did not read `run_m4.py`, `onbox_m4.sh`, `frozen/ONBOX_CONTRACT.md` or
`out/pip_pins_check_build9.txt`; each ruling rests on the reviewer's and the operator's line references, taken as reported. The
two shape-example files named in the task are outside this session's readable directory; this addendum follows the shape of the
sections above. Every earlier section stands except where an answer below says it is superseded: G3 settles where the contract
and the directive differ, and G2 records that F7's third apt-limit term is not required for launch 1. Answers are numbered G1 to
G8: G1 the blocking finding (report number 1), G2 to G4 the advisory findings (report numbers 2 to 4), G5 the "verified, no
finding" list, G6 to G8 the operator's three asks (a), (b), (c). Counts: 8 answers. The line `Build 7 authorised` at the end is the
launcher's literal string for the next build; it does not renumber the earlier builds (the build it authorises is build 10).

**Decision on budget and build (addendum).** GO stands. No GPU money has been spent: no launch record is among the inputs and
review 4 ran nothing. Cap arithmetic unchanged: 2 launches x 2.00 h x USD 1.99 = USD 7.96; with 600 s outside each, 2 x (7,200 +
600) s = 15,600 s = 4.333 h x 1.99 = USD 8.62; under the USD 10 cap with USD 1.38 left; `BUDGET_LEFT_USD=5` per launch above the
3.98 a launch can cost. No ruling below adds a launch, a download source, a package source or install time beyond the 1,800 s
install total. Finding 1 would have spent a launch (USD 3.98 at most, with the box paid for) on a run that ends at the smoke check
with no measurement and consumes A2(a); that is why it is binding.

### Blocking finding (G1)

1. **G1 (finding 1, BLOCKING: `run_m4.py:405` writes `openmm[cuda12]==8.2.0`; the pinned release declares no `cuda12` extra, so pip
   installs the plain package and the smoke check fails after the box is paid for).** ACCEPTED; it is a build re-run, not a hand
   edit (F6). The build changes the OpenMM requirement in `PIP_PINS` and its comment (`run_m4.py:381-392` and `405`): the form
   with a bracketed extra is no longer acceptable for OpenMM. The requirement is a pair of pinned entries, the plain OpenMM
   distribution at the pinned version and a sibling pinned requirement whose distribution name starts `openmm-cuda`
   (`name==version`). The build chooses that sibling's name and version from the operator's index listing (Operator actions),
   which it reads as an input, and from nothing it recalls: it uses no network, and it does not guess a name or a version that the
   listing does not show as existing. If the listing shows no distribution whose name starts `openmm-cuda`, the build changes
   nothing, returns a statement saying so, and the gate rules again in an addendum 8; no launch happens. The comment on `PIP_PINS`
   states which form was chosen, that it is a choice, and the listing file's name. The smoke check
   (`Platform.getPlatformByName("CUDA")`) stays as it is and is still the in-box test. Test, in the selftest: the `PIP_PINS`
   parser case of item 33 now requires an `openmm-cuda*` entry and rejects a bracketed extra on the OpenMM entry; every entry
   stays `name==version`.

### Advisory findings (G2 to G4)

2. **G2 (finding 2, ADVISORY: `apt_limit` implements two of F7's three terms; the "no time left" check comes after the apt stage).**
   ACCEPTED AS-IS for launch 1 of record, no code change. The reviewer shows it cannot bind at the authorised settings: with
   `REMOTE_TIMEOUT=7200` and `BUDGET_LEFT_USD=5` apt is capped at 1,800 s in total and 300 s for the update loop, the elapsed
   bootstrap is far below 4,900 s, and spend stays inside the caps (F22's advisory definition). The condition that keeps it
   advisory is made binding on the launch instead of the build: launch 1 and launch 2 run with `REMOTE_TIMEOUT=7200` exactly (see
   Pre-authorisation); a smaller value is not authorised. EXEC_NOTE item 48(c) is revised to say the third term is not required of
   the shell, so review 5 does not cite it again. The selftest flow for `REMOTE_TIMEOUT=10` is accepted as it stands.

3. **G3 (finding 3, ADVISORY: `frozen/ONBOX_CONTRACT.md` items 2, 3 and 9 versus the directive).** SETTLED IN THE DIRECTIVE, by a
   ruling of record; the build does not change. Where the contract and EXEC_NOTE items 8, 20, 43 and 46 differ, the gate rules
   that those items win: exit codes are 0, 2, 3 and 4 and there is no exit 5; the runner and the shell write `RUN_DONE` under
   items 8 and 48; the guard uses the estimate floors of item 43 and no timed dry run on the real input; the per-run environment
   file is `env.txt` (item 3) and no `env_<tag>.json` is required. Reason: each of these is a mechanical choice that spends no money
   without a valid record, which the reviewer confirms, and the contract's own rule that the directive may tighten but not loosen is
   met here by the gate itself, as the owner's delegate, naming each point it relaxes; every other contract item stays binding
   as E26 says. This is recorded as EXEC_NOTE item 56. Review 5 checks the build against the contract and the directive
   with this ruling applied and does not cite these points again.

4. **G4 (finding 4, ADVISORY: when the runner dies without `RUN_DONE`, `write_minimal_void` marks all four inputs void in
   `RUN_VALID.json` and the summary even where decided C records are on disk).** ACCEPTED, and made a numbered item (55) although the
   reviewer rated it advisory, for the reason of F2: A2 and the operator read the per-input status from `RUN_DONE` and
   `RUN_VALID.json` alone (item 46), and a decided input shown as void invites a relaunch that A2 does not authorise. The change is
   local to the shell's void path (`onbox_m4.sh:284-287`): before writing, `write_minimal_void` reads each C record already on
   disk; a record with decision PASS or FAIL, or VOID with `marginal` or a rule reason, is shown in `RUN_VALID.json`
   `inputs_status`, in `RUN_DONE` and in a summary the shell has to write as `decided` or `void_by_rule:<reason>`, and the
   record is never rewritten (`put` keeps not overwriting); only inputs with no such record are `void_by_failure:<kind>` (code 2) or
   `unmeasured_by_stop:<kind>` (code 3), as item 8 says. The exit code and `run_valid` are unchanged (item 48(b)). Test: a new
   shell-level flow of item 48: a runner stub that writes a decided C3 record and exits 2 with no `RUN_DONE` gives exit 2,
   `run_valid` false, C3 `decided`, its record byte-identical, and C1, C2 and C4 `void_by_failure`; the same stub with exit 3 gives C3
   `decided` and C1, C2, C4 `unmeasured_by_stop`.

### The "verified, no finding" list and the operator's three asks (G5 to G8)

5. **G5 (the reviewer's "verified, no finding" list).** ACCEPTED AS-IS; nothing changes. It covers: operator finding 1 (the
   `M4_TEST_*` names read only inside the test-hook block, only with `M4_SHELL_TEST` exactly `1`, none forwarded by the launcher;
   `M4_BASE` a fallback after `--base`); operator finding 2 (the `.keys` text at `run_m4.py:6983` is a selftest regex over the
   program's own source; no environment dump; `env.txt` named variables only); `HF_TOKEN` unset before the runner starts and
   stripped from every child; the caps (price default 1.99, `BUDGET_LEFT_USD` clamped to at most 5, `REMOTE_TIMEOUT` to at most 7,200,
   an unset one labelled, STOP_AT and the outer kill as built); the launcher and bootstrap copies differ from the frozen files only at
   declared points and `onbox_command` is `bash remote_run_m4.sh bash onbox_m4.sh`; the selftest log (658 of 658, last line
   `selftest: PASS`, hashes matching the files then); the shell routes (no `set -e`, `RC=0; ... || RC=$?` everywhere, the trap acting
   only while `FINISHED=0`, sudo only for declared apt, nothing written outside `~/m4_run/`); and downloads only from RCSB, the
   AlphaFold storage address, pip and apt with URL and hash recorded. The seven pins other than OpenMM exist on the index with none
   missing or unpinned; the operator's check is accepted as evidence for that, and it is repeated on build 10 (Operator actions).

6. **G6 (ask (a): rule on the one blocking finding; if it is a code change, authorise build 10 as an in-place edit limited to that
   change and to any advisory item chosen as binding).** BUILD 10 IS AUTHORISED (the literal line below), as an in-place edit of
   build 9's `run_m4.py` and `onbox_m4.sh`, limited to: the G1 change to `PIP_PINS` and its comment, the G4 change to
   `write_minimal_void`, the selftest cases those two changes need (the `PIP_PINS` parser case, the two shell flows of G4), and
   the selftest's own count and hash lines, which move. Every other line stays as build 9 has it, selftest cases included; the
   build does not refactor, rename or reorder anything. The build's return states the real line counts, the two sha256 values
   (B14), the new selftest count, and the exact lines changed. This is EXEC_NOTE item 57. A changed line outside that list is a
   blocking finding in review 5.

7. **G7 (ask (b): each advisory finding accepted as-is for launch 1 of record, or made a numbered item).** Rulings: advisory 2
   (G2) accepted as-is, with the launch condition `REMOTE_TIMEOUT=7200` and a revision of item 48(c) so the directive says what is
   built; advisory 3 (G3) settled in the directive as item 56, no build change; advisory 4 (G4) made item 55. No advisory is left
   unanswered and none is deferred silently. Advisories recorded in RUN.md and not ruled again if they recur in review 5: G2's and
   G3's, as ruled here.

8. **G8 (ask (c): is launch 1 pre-authorised on build 10 when review 5 reports zero blocking findings, with the launch environment
   restated).** YES. If review 5 of build 10 reports zero BLOCKING findings (as F22 defines blocking), launch 1 may proceed on
   build 10 with its advisory findings recorded in RUN.md and not ruled again, provided all of: (i) the build's own selftest
   passes and the operator's local re-run prints the same two sha256 values as the files on disk (B14); (ii) the operator actions
   below are done, the package-index check on build 10 included, and its result (every pin found, no `EXTRA-NOT-DECLARED`, none
   missing) is written into RUN.md; (iii) review 5 had `frozen/ONBOX_CONTRACT.md` on its read list and states it checked against
   it with G3 applied; (iv) A1's instance and cap limits hold. The launch environment of record, to be set by the operator and
   recorded on every record: `REMOTE_TIMEOUT=7200`, `BUDGET_LEFT_USD=5`, `PRICE_USD_PER_HOUR=1.99`,
   `INSTANCE_TYPE=gpu_1x_a100_sxm4`, region us-east-1; if that instance has no capacity, the cheapest single GPU with capacity at
   no more than USD 2.50/h, with `INSTANCE_TYPE` and `PRICE_USD_PER_HOUR` set to its values and the other three unchanged. If review
   5 reports any blocking finding, the gate rules again in an addendum 8 and no launch happens. No GPU money is spent by builds or
   reviews, so this loop costs no launch budget.

**Checks the gate made before answering (addendum).** Arithmetic and cross-reading only. Cap: 7,200 s = 2.00 h x 1.99 = 3.98; two
launches 7.96; with 600 s each outside 8.62; under 10. Ceilings unchanged and still sum to 7,200: 1,800 + 700 + 600 + 2,000 +
1,600 + 100 + 400 = 7,200. G2: 5 / 1.99 h = 9,045 s above 7,200 s, so the time cap binds before the dollar cap and apt's own 1,800 s
total (plus 300 s for the update loop, inside it) is below the 7,200 - 500 = 6,700 s that F7's third term would allow at elapsed 0;
the term can bind only if `REMOTE_TIMEOUT` is below about 2,300 s, which is why 7,200 exactly is made a launch condition. G4 planted:
one decided C3 record on disk and three missing give one `decided` and three `void_by_failure` (or `unmeasured_by_stop`); the
count is 4. Counting: the report has 4 numbered findings (1 blocking, 3 advisory), a "verified, no finding" list, and 3 asks;
answers G1 to G8 cover all. The report's selftest count (658 of 658) and the index check were not re-run; the gate cannot.

**Pre-authorisation (addendum).** A1 stands unchanged. A2 stands with (a), (b), (c) as before; a smoke-check failure from a package
that did not install is under A2(a). Both launches run with `REMOTE_TIMEOUT=7200` exactly (G2); a smaller value is not authorised.
Not authorised, as before: a relaunch to double seeds, to repeat a decided input, to change a band, or after an anchor miss. No
launch is authorised until build 10 exists, its selftest passes with matching hashes (B14), review 5 meets G8, and the operator has
done the actions below.

Build 7 authorised

## Operator actions

OPERATOR: write an index listing, before build 10 is made, of every distribution on the package index whose name starts `openmm-cuda` (names and available versions) and of the extras declared by the pinned OpenMM release, into `out/pip_pins_openmm_listing.txt`; build 10 reads that file and `out/pip_pins_check_build9.txt` as inputs and uses no network (G1).
OPERATOR: after build 10, re-run the package-index check on every requirement in `PIP_PINS` of `run_m4.py` (each pinned version exists, each extra named is declared, each `openmm-cuda*` name exists) and write the result into RUN.md; any mismatch is a build re-run, not a hand edit (F6, G8).
OPERATOR: put `frozen/ONBOX_CONTRACT.md` on the read list of review 5 and state G3's ruling to it (G8).
OPERATOR: before launch 1 re-run `python3 run_m4.py --selftest` locally and compare the two printed sha256 values with the files on disk (B14); the earlier lines of addenda 5 and 6 (the `RUN_VALID.json` fetch line declared, `remote_run_m4.sh` with only its `cd` line changed, `lambda_run_m4.sh` default `REMOTE_TIMEOUT` 7200 declared in its header) stand.
OPERATOR: launch environment of record for both launches: `REMOTE_TIMEOUT=7200` (not lower), `BUDGET_LEFT_USD=5`, `PRICE_USD_PER_HOUR=1.99` (the chosen instance's price, at most 2.50, if the fallback is used), `INSTANCE_TYPE=gpu_1x_a100_sxm4` in us-east-1 (else the cheapest single GPU with capacity at no more than USD 2.50/h); record which on every record (G8).
