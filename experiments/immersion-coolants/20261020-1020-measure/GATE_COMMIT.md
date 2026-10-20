# GATE COMMIT: measure run m3 (triage wf_0cc4d978-d33)

Date: 2026-10-20. Written by the operating session as gate. The owner set the budget rules on 2026-10-20 and asked to
carry the coolant work to experiment; every other answer below is the gate's own and is recorded as such.

## Inputs read (and nothing else)

| File | sha256 |
|---|---|
| `out/design_record.json` | `5c2506533f8ddebbbbe53c89434fee20222a69c1c3db4b485eb8f9e80293e6b9` |
| `out/triage_wf_0cc4d978-d33_return.json` | `43f391789e6c6a80c00c2cf2b3867629ca0d598639303a9b64c6ff4f580910ae` |
| `out/prelaunch_build_mol00557.json` | `b76d695f7f328d5b80a6c90d5bc8524f205b25b62a51ed0717a22735ab7d138c` |
| `QUESTION.md` | `1530fe29a345fd3474a0c66f84b51d7958344ad96158b33969abb89204295a03` |
| `out/design.json` | `ebaecdcdd728eea1275f05a9422f76a75b6b408572d15f61f886f8ba891aa419` |
| `out/diff.json` | `a2f7de26a6cd0c99fad7484764aafc79b2ae6b2bdfd7fa1909ce776b0b68d2bb` |

## What is being gated, in plain words

One rented A100 box installs LAMMPS, equilibrates a box of 250 nonylcyclohexane molecules with the dataset's own
deck, then times three short production runs: the deck as written (pressure tensor and heat flux every five steps),
pressure tensor only, and no sampling. The first number is the card's throughput, which every cost line in the card
divides by; the card guessed it from an Amber benchmark. The density after equilibration is checked against the
measured value first. The box build itself, where the coolant pilot halted, has already run on the workstation.

## Decision on budget and build

**Budget: APPROVED.** Hard cap USD 10 for this run, at most two launches together, `gpu_1x_a100_sxm4` at USD 1.99/h
if it has capacity (the card's GPU), else the cheapest single GPU with capacity, recorded on every record. Within the
owner's calibration limit (about USD 10). Project cap USD 500; spent so far USD 2.60.

**Design: APPROVED FOR BUILD** with the changes below and nothing else.

## Answers of record

Each item gets one verdict: ACCEPTED AS-IS, REJECTED, or QUEUED CONTROL.

### Diff departure questions (7)

- **D1 (one molecule, 11,250 atoms).** ACCEPTED AS-IS. The per-atom step rate (atom-steps per second) is reported on
  every throughput record so the reader can scale to the card's larger boxes; the label reads "one box, 11,250 atoms".
- **D2 (packing at 0.3 g/cm3).** ACCEPTED AS-IS. The deck's NPT and deform stages define the liquid; E2 checks the
  result against the reference. The pilot's 0.75 is not repeated.
- **D3 (shortened equilibration).** ACCEPTED AS-IS, with the control under I2 below (plateau check inside the density
  series, not only its mean).
- **D4 (three variants; (b) stands in for (a) on refusal).** ACCEPTED AS-IS. The label on E3 names which variant it read.
- **D5 (conda-forge CUDA build).** ACCEPTED AS-IS. The build string actually installed and `lmp -h`'s package list are
  on every record; the label reads "LAMMPS 2024.08.29, conda-forge CUDA build, GPU package".
- **D6 (2 fs over the deck's 1 fs).** ACCEPTED AS-IS. The card's held_fixed binds. E8 is the stability check.
- **D7 (one GPU reads the per-GPU rate).** ACCEPTED AS-IS.

### Grounding (reader verdict: unauditable)

- **G1.** The isolated reader ran for the first time in this program. It confirmed the pre-launch artifacts (net charge
  0.0, 250 molecules, density 0.3, 11,250 atoms read without error) and flagged two things: the builder's exit code
  was in no artifact (the builder log was empty), and the box outputs do not exist yet. ANSWERED: the operator wrote
  `out/prelaunch_build_mol00557.json` (both attempts' exit codes and wall-clocks, the metadata, the read check, the
  file hashes); it is an input of this gate. The box outputs are what the run produces; the post-run reader grounds them.

### Run queue (1)

- **R1 (timed GPU dry run before the full sequence).** QUEUED CONTROL, binding on the build. The install arm's dry run
  becomes a 2,000-step run of the deck as written (`tdm.in` with warmup_steps 1000, prod_steps 1000, dump_every 5,
  starting from the raw packed box through a minimal `read_data` path, or from `equilibrate.in`'s first stage if the
  deck cannot start from in.data; the builder decides and records which) with `-sf gpu -pk gpu 1`. Records: (a) the
  Performance line's ns/day against 1000 x 2 fs / wall-clock of that run, agreement within 5% (the units check the
  skeptic asked for); (b) whether the deck as written is accepted by the GPU pair style (an early E6 reading); (c) the
  `units real` line of in.init confirmed. If (a) disagrees by more than 5%, every later ns/day is labelled "Performance
  line and wall-clock disagree" and both numbers are reported.

### Instrument queue (10): validation controls, all inside the run or the selftest, no extra spend

- **I1 (E1 readout).** QUEUED CONTROL: the selftest parses the committed `out/prelaunch_build_mol00557.json` and
  `metadata.json` and reproduces the E1 decision; a planted metadata with net charge 0.01 fails; a planted read log
  with "ERROR" fails.
- **I2 (E2 readout).** QUEUED CONTROL: the selftest parses a planted density file in the deck's `fix ave/time`
  format and gets the planted mean exactly; planted 0.805 x 1.03 holds, x 1.05 fails. On the box: the thermo density
  column over the last 250 ps of NPT must have a least-squares slope whose magnitude is under 1% of the mean per 100
  ps (plateau check); if not, E2 carries the label "density still drifting".
- **I3 (E3 readout).** QUEUED CONTROL: the selftest parses a planted LAMMPS log with a `Performance:` line
  (`Performance: 123.456 ns/day, 0.194 hours/ns, ...`) and gets 123.456; planted 300 holds within [100, 625];
  planted 90 refuted below; planted 700 refuted above.
- **I4 (E3b readout).** QUEUED CONTROL: planted 150.0 passes, 149.9 fails.
- **I5 (E3c readout).** QUEUED CONTROL: planted 250 gives USD 941.00; planted 125 gives USD 1,882.00 (above the cap);
  planted 235.3 gives USD 999.79 (within). 2 decimals.
- **I6 (E4 readout).** QUEUED CONTROL: planted prod_b 120 against prod_a 100 gives ratio 1.2000.
- **I7 (E5 readout).** QUEUED CONTROL: planted prod_c 200 against prod_a 100 gives ratio 2.0000; atom-steps per
  second for 11,250 atoms at 200 ns/day with a 2 fs step = 11,250 x 200e-9 / 2e-15 / 86,400 = 1.3021e10, exact to
  4 digits.
- **I8 (E6 readout).** QUEUED CONTROL: the selftest feeds a planted LAMMPS error line ("ERROR: Pair style
  lj/cut/coul/long/gpu does not support compute centroid/stress/atom") and gets REFUSED with that line verbatim; a
  planted clean log gets RUNS.
- **I9 (E7 readout).** QUEUED CONTROL: planted install start and end epochs give the wall-clock to the second; the
  builder wall-clock is read from `out/prelaunch_build_mol00557.json` (12 s).
- **I10 (E8 readout).** QUEUED CONTROL: the selftest parses a planted thermo block and gets its mean temperature;
  planted 313.0 passes, 320.0 fails; a planted "Lost atoms" line fails.

## Labels

- Every throughput record carries: instance type, GPU name, driver, CUDA runtime version, the installed LAMMPS build
  string, `lmp -h` package list, timestep, atom count, per-atom step rate, the variant it read, the install wall-clock,
  price per hour, and the labels "one box, 11,250 atoms" and "LAMMPS 2024.08.29, conda-forge CUDA build, GPU package".
- If the install fails: RUN_VALID false, exit 2, `m3_summary.json` written with the install log's last lines.
- If the box stops before all variants run: finished rows are reported, each labelled "incomplete run: descriptive only,
  no verdict".

## Checks the gate made before answering

Arithmetic only, on numbers in the inputs. No experiment was run.
- Atom count 250 x 45 = 11,250. Box 66.28 A at 0.3 g/cm3; at 0.805 g/cm3 the side is 66.28 x (0.3/0.805)^(1/3) = 47.9 A,
  above twice the 12 A cutoff plus skin: fine for PPPM and the pair style.
- Equilibration steps: 50,000 x 0.5 fs + (100,000 + 250,000 + 100,000) x 2 fs = 25 ps + 900 ps = 0.925 ns.
  Production: 3 x (25,000 + 100,000) x 2 fs = 0.75 ns. At 100 ns/day the box computes for about 24 min; at 30 ns/day
  about 80 min, inside a 3,600 s cap only if the time guard trims prod_c; REMOTE_TIMEOUT is set to 5,400 s.
- Density window: `fix ave/time 100 1250 250000 ... start 125000` samples steps 125,100 to 250,000 (1,250 samples
  every 100 steps) and writes once at step 250,000: consistent.
- Cap: 5,400 s = 1.5 h at USD 1.99/h = USD 2.99 per launch; two launches USD 5.97 within the USD 10 cap.

## Pre-authorisation

- **A1 (second launch).** If launch 1 halts before prod_a for a toolchain or launcher reason, one more launch is
  authorised within the same USD 10 cap after the cause is recorded in RUN.md and, if the directive changes, the build
  is re-run through pipeline.js build mode. No built file is edited by hand.

---

## Addendum after build 1 (2026-10-20, 11:2xZ): ruling on the per-atom step rate; build 2 authorised

**New input of record.** `out/build1_m3_wf_2975691d-aa9_STOPPED_return.json`: the build stopped by design because the
directive's planted value for the per-atom step rate (checklist item 9, I7: "1.3021e10") contradicts the directive's own
formula (item 6), which gives 11,250 x 200e-9 / 2e-15 / 86,400 = 1.3021e7 atom-steps per second. The builder implemented
both, ran the selftest (282 of 283 passed), and stopped. The gate's arithmetic was wrong by 1,000x; the formula is right.

- **A2 (I7 planted value).** REJECTED: 1.3021e10. REPLACED BY: 1.3021e7 (the formula binds; independent check: 200 ns/day
  at 2 fs is 1e8 steps per day = 1,157.4 steps per second; x 11,250 atoms = 1.3021e7). The gate's own I7 line above is
  superseded by this one.
- **A3 (builder readings 1 to 4).** ACCEPTED AS-IS: (1) the four sanity text matches apply to each production run's own
  output, from its thermo header to its "Loop time" line (LAMMPS prints "Finding SHAKE clusters" before every run);
  (2) on the box the E1 gate checks the parts present (net charge, atom count) and reads PASS_ON_PARTS_PRESENT; the full
  E1 record stands in `out/prelaunch_build_mol00557.json`, read locally; (3) the dry run's wall-clock is bracketed by
  LAMMPS `shell date` stamps around `run 1000 pre no`; (4) edit 2 also deletes `variable dump_every`.
- **A4 (other build choices).** ACCEPTED AS-IS: a stage stop or a guard stop sets run_valid false; the guard's estimate
  constants (margin 1.25, 60 s per stage, 120 s free, 600 s billed outside the run, 100 ns/day before any measurement)
  are the builder's and are recorded in the summary.
- **A5 (build 2).** The build is re-run through pipeline.js build mode with the corrected directive (EXEC_NOTE.md item 9,
  I7). No built file is edited by hand; build 1's files are archived under `out/build1_stopped/` with their hashes in
  `out/BUILT_HASHES_build1_stopped.txt`.

- **A6 (equilibration deck under the GPU package).** QUEUED CONTROL, binding on the build: if `equilibrate.in` errors on
  its `comm_style tiled` / `balance rcb` / `fix load_balance` lines under the GPU package, those three lines are deleted
  in a recorded copy (listed edit 3) and the equilibration is re-run once; the error line and the diff are recorded.
  On a one-process build these lines balance nothing.

Everything else in this gate stands.

---

## Addendum after build 2 (2026-10-20, 11:4xZ): the engine route; build 3 authorised

**New input of record.** `out/build2_m3_wf_4df87803-b95_STOPPED_return.json`: build 2 stopped by design. The builder read
every revision of conda-forge's `lammps-feedstock/recipe/build.sh` from 2024-04-14 to 2026-09-20: all set `PKG_GPU=OFF`
and build the CUDA variants with KOKKOS instead (the 2024 recipe pinned `Kokkos_ARCH_MAXWELL50`). The pinned engine
cannot run `-sf gpu`. The coolant pilot's RUN_LOG (step 4d, 2026-10-18) had reported the same and the gate missed it.
Selftest 313 of 313. No box was launched; USD 0 spent.

- **A7 (engine).** REJECTED: the conda-forge CUDA build and the "install nothing else" rule for the engine. REPLACED BY:
  compile LAMMPS `stable_29Aug2024` from the official source tarball on the box with the GPU package for CUDA, sm_80,
  and the packages the decks need (KSPACE, MOLECULE, RIGID, EXTRA-COMPUTE, OPENMP), single process (no MPI). Toolchain
  from the image: nvcc 12.8 (`/usr/bin/nvcc`, confirmed on the m2 box), g++, make; `cmake` from the image if present,
  else `python3 -m pip install --user cmake` (the one allowed install). FFT: FFTW3 if `fftw3.h` is on the image, else
  LAMMPS's built-in KISS FFT; which one is recorded. GPU precision: the GPU package default (mixed), recorded as a label
  "GPU package mixed precision" (the card's Amber proxy, SPFP, is mixed too). Source: `https://github.com/lammps/lammps/archive/refs/tags/stable_29Aug2024.tar.gz`,
  mirror `https://download.lammps.org/tars/lammps-29Aug2024.tar.gz`; sha256 of the tarball recorded; `lmp -h` must list
  GPU, KSPACE, MOLECULE, RIGID, EXTRA-COMPUTE, else exit 2. Option (a), KOKKOS, is not taken: it changes the switches, the
  refusal names and the arch, and the deck's centroid stress has no KOKKOS form.
- **A8 (caps).** `REMOTE_TIMEOUT` raised to 7,200 s (2 h, USD 3.98 per launch at USD 1.99/h; two launches USD 7.96 within
  the USD 10 cap); `BUDGET_LEFT_USD=5` per launch stays. The time guard trims prod_c, then prod_b, as before. The
  compile is a stage with its own guard and a 1,800 s cap; E7 records its wall-clock against the card's `l_dry` line.
- **A9 (build 3).** The build is re-run through pipeline.js build mode with the revised directive (EXEC_NOTE.md item 11
  rewritten; Box caps). No built file is edited by hand; build 2's files are archived under `out/build2_stopped/`.

Everything else in this gate and its first addendum stands.

---

## Addendum after build 3 (2026-10-20, 12:0xZ): the engine label; build 4 authorised

**New input of record.** `out/build3_m3_wf_881fe8ab-bfb_return.json`: build 3 is ready (selftest 365 of 365) and flags one
contradiction the gate left in the directive: checklist item 10 still required the label "LAMMPS 2024.08.29, conda-forge
CUDA build, GPU package" after item 11 moved the engine to a source compile.

- **A10 (engine label).** REJECTED: the conda-forge wording. REPLACED BY: "LAMMPS 29Aug2024, compiled from source on the
  box, GPU package, CUDA sm_80". The true engine facts the builder already placed beside the label (version line, cmake
  command, tarball address and sha256, FFT choice, "GPU package mixed precision") stand.
- **A11 (build 4).** Re-run through pipeline.js build mode; only the label constant is expected to change. Build 3's files
  are archived under `out/build3/`. No built file is edited by hand.

Everything else stands.

---

## Addendum after launch 1 (2026-10-20, 12:2xZ): protocol lengths and the window; launch 2 authorised

**New input of record.** `out/launch1/results_m3/out/` (box 7fd3a46cdc944565ad8bb8617ce6e206, A100 SXM4, us-east-1,
12:07:xxZ to 12:14:xxZ): the compile succeeded in 113 s (cmake 3.22.1 from the image, g++ 11.4, nvcc 12.8, KISS FFT,
`lmp -h` lists GPU with mixed precision, KSPACE, MOLECULE, RIGID, EXTRA-COMPUTE); the timed dry run of the deck as
written RUNS on the GPU package (R1 RUNS_AGREE: Performance 13.52 and 13.38 ns/day on two 1,000-step runs, 78 steps per
second, 880 katom-steps per second, wall-clock agreeing within 5%); the cost and time guard then stopped the run before
the box copy: the remaining stages at the measured rate (875,000 steps) need about 10,558 s against 7,009 s left
(exit 3, run_valid false, as designed). No MD beyond the dry run; nothing measured against E2 to E8.

- **A12 (protocol lengths).** REJECTED: the -var values of item 2 (equilibration 50,000 / 100,000 / 250,000 / 100,000
  steps; production 25,000 + 100,000 per variant). REPLACED BY: equilibration `pushoff_steps 20000 settle_steps 50000
  npt_steps 150000 deform_steps 50000 density_avg_start 100000 density_sample_every 100 density_sample_repeat 500
  density_sample_freq 150000` (10 ps strain relaxation at 0.5 fs, 100 ps NVT, 300 ps NPT with the density mean over
  the last 100 ps, 100 ps deform; the paper reports the density plateau within about 0.2 ns); production `warmup_steps
  10000 prod_steps 50000` per variant (20 ps + 100 ps). Total 450,000 steps: at the dry run's 78 steps per second
  this is 5,770 s, inside the window below even if the dense liquid runs no faster than the dilute box. E2's window is
  "the last 100 ps of a 300 ps NPT", labelled as such; E10-style readings are unchanged. The E3 Performance line now
  averages a 100 ps segment; the dry run already shows the line is stable to 1% between two 1,000-step runs.
- **A13 (window).** `REMOTE_TIMEOUT=9000` (2.5 h, USD 4.98 at USD 1.99/h), `BUDGET_LEFT_USD=5`. Launch 1 billed about
  0.12 h (USD 0.25); launch 2 at most USD 4.98; total within the USD 10 cap. The guard's estimate model (the dry-run rate
  for every stage, margin 1.25) stays as built.
- **A14 (launch 2).** Authorised after build 5 through pipeline.js build mode with the revised item 2 and caps. No built
  file is edited by hand; build 4's files are archived under `out/build4/`.
- **Finding of record, before any verdict.** The dry run's 13.5 ns/day on the deck as written is 18.5x below the card's
  PROXY and 11x below its gate; the dense liquid will not be faster. This is a reading on a dilute 0.3 g/cm3 box and is
  not E3; E3 is read after equilibration as designed.

Everything else stands.
