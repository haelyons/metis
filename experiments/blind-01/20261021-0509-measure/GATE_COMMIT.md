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
   PKD2 chain copies), with total length inside 750 to 1,000 residues and the three lengths spread across that range as far as the
   entry allows; it records chain ids, sequences, lengths and file hash. AlphaFold runs go seed-major (all three pairs at seed 0,
   then seed 1, then seed 2) so a time stop leaves every pair covered. Minimums for a decision: C1 needs at least 3 completed
   runs covering all 3 pairs; C2 at least 2 complexes (the median of two is their mean; the record says n=2); C3 at least 2
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
