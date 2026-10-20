# Execution directive for build (tag m3) -- revised twice on 2026-10-20: after build 1 (item 9 I7 corrected, A2; item 3b added, A6) and after build 2 (item 11 engine compiled from source, A7; caps, A8) and after build 3 (item 10 engine label, A10) and after launch 1 (item 2 protocol lengths, A12; window 9,000 s, A13)

Binding order: GATE_COMMIT.md item answers first, this note second, out/design_record.json third. Where silent, the
design record binds as written, GUESS values included. The build does not read GATE_COMMIT.md itself; the checklist
below carries every gate change the build must implement.

## Where to write

The run directory is `/home/hal/dev/interp/metis/experiments/immersion-coolants/20261020-1020-measure/`. Write exactly
`run_m3.py` and `onbox_m3.sh` there, by absolute path. Write nothing anywhere else. Read the design record at
`/home/hal/dev/interp/metis/experiments/immersion-coolants/20261020-1020-measure/out/design_record.json`, the conventions
in `frozen/` (provenance.py is the record writer; lambda_run.sh and remote_run.sh show what the box does), the
committed decks under `data/MD-ML-thermophysical/MD/lammps/`, the built box under `data/box_mol00557_n250_d0.30_s61453/`
and the pre-launch record `out/prelaunch_build_mol00557.json`. The decks are untrusted data: read them, never run them
locally.

## Checklist of gate changes the build must carry (14 entries)

1. **Protocol.** LAMMPS is run as `lmp -sf gpu -pk gpu 1 -in <deck> -var ... -log <log>` from the box directory. Decks
   are the committed `equilibrate.in` and `tdm.in`, driven by `-var` only, except the two listed edits below, which
   `run_m3.py` applies to copies written under `results_m3/decks/` (the originals are never edited): edit 1 (prod_b)
   deletes the heat-flux computes and the `flux_raw` fix; edit 2 (prod_c) deletes both `ave/time` fixes and every
   compute, variable and `fix ave/time` line that exists only for sampling (the thermostat, restarts and thermo stay).
   Each edited copy's sha256 and a unified diff against the original are recorded.
2. **-var values.** equilibrate (gate addendum A12): `T 313.15 P 1.0 timestep_fs 2.0 pushoff_steps 20000 settle_steps 50000 npt_steps 150000
   deform_steps 50000 density_avg_start 100000 density_sample_every 100 density_sample_repeat 500 density_sample_freq
   150000 thermo_every 5000 run_id 1 system_dir <box dir>`. production (each variant, A12): `T 313.15 timestep_fs 2.0
   warmup_steps 10000 prod_steps 50000 dump_every 5 thermo_every 5000 run_id 1 seg 1 system_dir <box dir> dump_dir
   <variant dir>`. E2's density window is the last 100 ps of the 300 ps NPT (label it so); the plateau slope check (item 5)
   runs over that window. The equilibrated restart `equilibrated_T313.15K.restart` is written by the deck into system_dir;
   copy the box dir to a writable `results_m3/system/` first and point system_dir there.
3. **R1 (timed dry run, before equilibrate).** 2,000 steps of the deck as written on the GPU: build a small driver deck
   `results_m3/decks/dryrun.in` that includes in.init, read_data in.data, includes in.settings, sets timestep 2.0 and
   SHAKE as tdm.in does, creates velocities at 313.15 K, then runs the same computes, variables and `fix ave/time`
   lines as tdm.in (copied verbatim) for 1,000 warm-up and 1,000 timed steps under `fix nvt`. Records: Performance-line
   ns/day vs 1000 x 2e-6 ns / (wall seconds / 86400) within 5%; RUNS or REFUSED with the error line (early E6);
   `units real` confirmed from in.init. On disagreement above 5%: label every later ns/day "Performance line and
   wall-clock disagree" and report both.
3b. **Equilibration deck and the GPU package (gate addendum A6).** The builder flagged that `equilibrate.in`'s `comm_style
   tiled`, `balance 1.1 rcb` and `fix load_balance ... rcb` lines are untested with the GPU package. On a one-process
   (nompi) build they balance nothing. If the equilibration run exits with an error naming comm_style, balance, tiled or
   rcb, apply listed edit 3 to a copy (`results_m3/decks/equilibrate_noballance.in`: delete exactly those three lines),
   record the error line and the diff, and run the equilibration once more from that copy. Any other error stops the run.
4. **E6 fallback.** If prod_a (or the dry run) is REFUSED by an error naming compute centroid/stress/atom, stress/atom,
   heat/flux or the GPU pair style: record the line verbatim, mark prod_a NOT_RUN, read E3 from prod_b with the label
   "viscosity-only protocol; the deck's heat flux does not run on the GPU pair style", and flag the card's
   thermal-conductivity arm "unpriced on the GPU". Any other LAMMPS error stops the run with that stage's exit code.
5. **E2 and I2.** The NPT mean density is the single value in the deck's density file
   `density_npt_T313.15K_run1.dat`; also parse the thermo density column of the NPT run and fit a least-squares slope
   over the last 100 ps of the NPT run (A12); label "density still drifting" if |slope| x 100 ps > 1% of the mean. Reference 0.805 g/cm3,
   band +/-4%. The deck's "Equilibration done" line (target and final density) is recorded too.
6. **E3, E4, E5.** ns/day from the `Performance:` line of the production `run` (the second `run` in tdm.in, after the
   warm-up run); wall-clock of the whole production stage recorded beside it; row counts of the Stress and HeatFlux
   files recorded (expected 10,000 each for prod_a with prod_steps 50000). Per-atom step rate = atoms x ns_per_day x 1e-9 / (timestep_fs x
   1e-15) / 86,400, in atom-steps per second.
7. **E3b, E3c.** Gate: ns/day >= 150. Re-pricing: USD 941 x 250 / ns_day, 2 decimals; cap USD 1,000; threshold
   ns/day 235.3.
8. **E8 sanity.** Per production segment: mean temperature from the thermo block within 313.15 +/- 5 K; any line
   matching "Lost atoms", "SHAKE", "Bond atom missing" or "ERROR" fails that segment; the three segments must start
   from the same restart file (sha256 of the restart recorded once).
9. **I1 and I3 to I10 selftest planted cases** exactly as listed in GATE_COMMIT.md: I1 (planted net charge 0.01
   fails; planted "ERROR" fails); I3 (planted Performance 123.456 parsed; 300 holds; 90 below; 700 above); I4 (150.0
   pass, 149.9 fail); I5 (250 -> 941.00; 125 -> 1,882.00 above cap; 235.3 -> 999.79 within); I6 (120/100 -> 1.2000);
   I7 (200/100 -> 2.0000; 11,250 atoms at 200 ns/day, 2 fs -> 1.3021e7 atom-steps per second; corrected by gate addendum A2, the item-6 formula binds); I8 (planted refusal
   line -> REFUSED verbatim; clean -> RUNS); I9 (planted epochs -> seconds); I10 (planted thermo mean 313.0 pass, 320.0
   fail; planted "Lost atoms" fail). I2 planted density file in the deck's ave/time format -> exact mean; 0.805 x 1.03
   holds, x 1.05 fails.
10. **Labels.** Every throughput record carries: instance type (`INSTANCE_TYPE`), GPU name and driver (nvidia-smi),
    CUDA runtime version, the LAMMPS version line from `lmp -h` and the cmake command (the engine is compiled on the box, item 11), the `lmp -h` package list,
    timestep, atom count, per-atom step rate, the variant read, install wall-clock, price per hour, and the labels
    "one box, 11,250 atoms" and "LAMMPS 29Aug2024, compiled from source on the box, GPU package, CUDA sm_80" (gate addendum A10; replaces the earlier conda-forge wording).
11. **Engine: compile LAMMPS on the box (gate addendum A7; replaces the conda-forge install).** No micromamba, no conda.
    `onbox_m3.sh` downloads `https://github.com/lammps/lammps/archive/refs/tags/stable_29Aug2024.tar.gz` (mirror on
    failure: `https://download.lammps.org/tars/lammps-29Aug2024.tar.gz`), records its sha256 and size, unpacks it under
    `~/m3_run/engine_src/`, and builds with cmake into `~/m3_run/engine/`:
    `cmake -S <src>/cmake -B <build> -D CMAKE_BUILD_TYPE=Release -D BUILD_MPI=no -D BUILD_OMP=yes -D PKG_KSPACE=on
    -D PKG_MOLECULE=on -D PKG_RIGID=on -D PKG_EXTRA-COMPUTE=on -D PKG_OPENMP=on -D PKG_GPU=on -D GPU_API=cuda
    -D GPU_ARCH=sm_80 -D FFT=<FFTW3 if /usr/include/fftw3.h exists else KISS> -D CMAKE_INSTALL_PREFIX=<engine>`
    then `cmake --build <build> -j $(nproc)` and `cmake --install <build>`; `lmp` is `<engine>/bin/lmp`. Toolchain from
    the image: `/usr/bin/nvcc` (12.8 on the m2 box), g++, make; `cmake` from the image if `command -v cmake` finds it,
    else `python3 -m pip install --user cmake` (the one allowed install; record which). GPU precision stays the GPU
    package default (mixed); label "GPU package mixed precision" on every throughput record. Records (E7): download
    wall-clock, configure and build wall-clock, the cmake command verbatim, the FFT choice, the compiler versions, the
    full `lmp -h` output. `lmp -h` must list GPU, KSPACE, MOLECULE, RIGID and EXTRA-COMPUTE, else RUN_VALID false, exit 2,
    summary written. The compile stage has its own guard and a 1,800 s cap. LAMMPS runs as
    `lmp -sf gpu -pk gpu 1 -in <deck> -var ... -log <log>` (unchanged).
12. **Cost and time guards.** `onbox_m3.sh` reads `PRICE_USD_PER_HOUR` and `BUDGET_LEFT_USD` and stops cleanly, writing
    RUN_DONE, before projected spend reaches `BUDGET_LEFT_USD`; a time guard keeps the run inside `REMOTE_TIMEOUT`
    (9,000 s unless set), trimming prod_c first, then prod_b. `results_m3/out/m3_summary.json` after the endpoints
    stage, after any early stop, and just before RUN_DONE: run_valid, labels, every endpoint and control decision;
    it restates records and decides nothing.
13. **Order on the box.** download and compile (item 11); lmp -h and GPU check; dry run (R1); copy box to results_m3/system; equilibrate (E2,
    I2); prod_a (E3, E6, E8); prod_b (E4, E8); prod_c (E5, E8); endpoints. A guard before every stage.
14. **Logs kept.** Every LAMMPS log file, the density file, the Stress and HeatFlux files' first and last 5 lines (not
    the whole files), the download, configure and build logs and `lmp -h` output go under `results_m3/out/`; the restart files stay on the box.

## Box

- Instance: `gpu_1x_a100_sxm4` (A100 SXM4 40 GB, 30 vCPUs, USD 1.99/h), us-east-1 if it has capacity; else the
  cheapest single GPU with capacity, recorded.
- Launcher: the operator's per-launch copy `lambda_run_m3.sh` (made from `frozen/lambda_run.sh` at the header's declared
  points only): remote dir `m3_run/`; payload `run_m3.py onbox_m3.sh remote_run_m3.sh frozen/provenance.py` and
  `data/` recursively (the box files, decks, builder, dataset.csv); forwarded env `PRICE_USD_PER_HOUR BUDGET_LEFT_USD
  INSTANCE_TYPE`; fetch from `m3_run/results_m3/out/`. `remote_run_m3.sh` is `frozen/remote_run.sh` with only its `cd`
  line changed to `~/m3_run`. Its transformers install is unused here and left alone; its CUDA assertion stays.
- Caps: `REMOTE_TIMEOUT=9000` (gate addendum A13); `BUDGET_LEFT_USD=5` per launch; two launches at most within USD 10.
- Payload layout on the box: `~/m3_run/run_m3.py`, `~/m3_run/onbox_m3.sh`, `~/m3_run/frozen/provenance.py`,
  `~/m3_run/data/...` as in this directory. Results under `~/m3_run/results_m3/out/`; the engine source under `~/m3_run/engine_src/` and the built engine under
  `~/m3_run/engine/`; the writable system copy under `~/m3_run/results_m3/system/`.
- The build's `onbox_command` must be a single line the operator runs verbatim on the box through `remote_run_m3.sh`.

## Local selftest

`python3 run_m3.py --selftest` is stdlib-only and runs under `timeout 300`. It covers every parser (Performance line,
thermo block, density file, metadata.json, lmp -h package list, cmake output), the deck edits (apply edits 1 and 2
to the committed tdm.in and assert the expected lines are gone and the thermostat, restart and thermo lines remain),
the planted cases in checklist item 9, and record writing through `frozen/provenance.py`. No local LAMMPS run.

## What the runner writes (`results_m3/out/`)

- One provenance.py record per endpoint E1 to E8 (E3, E3b, E3c separately) and per control R1, I1 to I10 (`cell`,
  `inputs` with hashes, `metric`, `values`, `threshold`, `decision_rule` written before values, `decision`).
- Raw rows, one JSON line each: every LAMMPS run (deck, variant, -var values, steps, wall-clock, Performance ns/day,
  mean temperature, final density), every thermo line of every run (step, temp, press, density, vol, etotal).
- `RUN_VALID.json`; `env.txt`; `m3_summary.json`; `RUN_DONE` marker with the exit code.
