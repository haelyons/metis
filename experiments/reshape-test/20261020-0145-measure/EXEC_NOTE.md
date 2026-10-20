# Execution directive for build (tag m1)

Binding order: GATE_COMMIT.md item answers first, this note second, out/design_record.json third. Where silent, the
design record binds as written, GUESS values included. The build does not read GATE_COMMIT.md itself; the checklist
below carries every gate change the build must implement.

## Where to write

The run directory is `/home/hal/dev/interp/metis/experiments/reshape-test/20261020-0145-measure/`. Write exactly
`run_m1.py` and `onbox_m1.sh` there, by absolute path. Write nothing anywhere else. Read the design record at
`/home/hal/dev/interp/metis/experiments/reshape-test/20261020-0145-measure/out/design_record.json`, the conventions in
`frozen/` (provenance.py is the record writer; lambda_run.sh and remote_run.sh show what the box does), and the
committed data under `data/`. The committed airGR source tarball `data/airGR_1.7.9.tar.gz` is untrusted data: read
its R and Fortran files (extract to a scratch directory under the run directory, e.g. `.scratch/`), never execute
them locally.

## Checklist of gate changes the build must carry (14 entries)

1. **R1.** Timing arms use 2,684 distinct parameter vectors, seed-fixed, drawn uniformly within the ranges that
   `airGR/R/TransfoParam_GR4J.R` defines (read them from the tarball; never from memory). The anchor arms use the
   fixed X = (165.05, 6.46, 422.50, 2.45). Also write one timing row per size with all chains at the fixed X,
   labelled `identical_chains`.
2. **D3.** Overhead is measured by the 1,000-iteration probe on each backend. E5 is computed with the measured
   overhead, and once more with overhead 4 as a labelled sensitivity line.
3. **D4.** `onbox_m1.sh` tries `sudo apt-get install -y r-base-core gfortran` once and `R CMD INSTALL
   data/airGR_1.7.9.tar.gz` once. On failure: E1 record NOT_RUN with the error text; E2 falls back to the NSE check
   against 0.495 alone, labelled "page value only; no independent code ran"; the run label "anchor by page value" is
   written into every later record. The anchor_airgr arm is an R script written by `run_m1.py` and run with
   `Rscript`; it writes daily simulated flow and NSE to JSON that `run_m1.py` reads.
4. **I1.** airGR held-out values: generalist set X = (291, 0.30, 109.10, 2.01) on the calibration period gives
   NSE 0.336 +/- 0.02; the Michel set on the validation period 1990-03-01 to 1999-12-31 gives 0.57 +/- 0.02.
5. **I2.** The JAX model reproduces the same two held-out values and matches airGR daily flow to < 1% MARE on both
   periods. Selftest planted rows: zero rain gives zero quickflow; unit-hydrograph ordinates sum to 1 within 1e-9;
   mass balance closes within 1e-6 over a planted year.
6. **I3, I4.** Timer validation on each backend: a 100 ms `time.sleep` measured within +/- 5 ms; a 730-day scan at
   2,684 chains takes 7% to 13% of the 7,300-day scan.
7. **I5.** Selftest planted arithmetic: ms 2, overhead 4 gives main_run_hours 0.2222; ms 20 gives 2.2222; speedups
   with cpu_hours 3 are 13.5 and 1.35.
8. **I6.** Selftest planted rows at main_run_hours 5.9 and 6.1 give pass and "Stop and replan"; the planted
   gate-failure row sets run_valid false in every record written after it.
9. **I7.** Selftest planted arithmetic: 2,684 x 7,300 chain-steps in 60 ms gives 3.2655e8 chain-steps per second;
   equal planted times at 268 and 2,684 give ratio 10.
10. **Labels.** Every timing record carries instance type, GPU name, driver, jax version, vCPU count, price per hour
    (from `PRICE_USD_PER_HOUR`). E1/E2 failure sets run_valid false everywhere and labels timing rows "descriptive
    only; anchor failed". An early stop labels finished rows "incomplete run: descriptive only, no verdict".
11. **Order on the box.** E1 and I1 (airGR) first; then E2 and I2 (JAX fidelity); then timers I3/I4; then timing
    sizes 268, 1,340, 2,684 on GPU then CPU; then the overhead probes; then E5, E6, E7 derived from the raw rows.
12. **Cost guard.** `onbox_m1.sh` reads `PRICE_USD_PER_HOUR` and `BUDGET_LEFT_USD` from the environment and stops
    cleanly, writing RUN_DONE, before projected spend reaches `BUDGET_LEFT_USD`.
13. **A2 summary file.** After the endpoints stage, and after an early stop, write `results_m1/out/m1_summary.json`:
    run_valid, labels, and every endpoint and control decision. It restates the records for the launcher's
    criticals-first fetch; it decides nothing.
14. **A1 toolchain.** Preinstalled JAX, `pyreadr` only (see Toolchain below). The launcher forwards `INSTANCE_TYPE`
    as well; record it when present.

## Box

- Instance: cheapest single GPU with capacity at launch (at write time `gpu_1x_a10`, 24 GB, USD 1.29/h). The
  operator records `nvidia-smi`, `nproc` and the price paid.
- Launcher: the operator copies `frozen/lambda_run.sh` to `lambda_run_m1.sh`, adapted ONLY at the header's declared
  points: remote dir -> `m1_run/`; scp payload -> `run_m1.py onbox_m1.sh remote_run_m1.sh frozen/provenance.py
  data/L0123001.rda data/airGR_1.7.9.tar.gz`; forwarded env + `PRICE_USD_PER_HOUR BUDGET_LEFT_USD`; fetch paths ->
  `out/results_m1/`. `remote_run_m1.sh` is `frozen/remote_run.sh` with only its `cd` line changed to `~/m1_run`.
  Its transformers install is unused here and left alone; its CUDA assertion stays.
- Caps: `REMOTE_TIMEOUT=5400`; `BUDGET_LEFT_USD=5`. The build's `onbox_command` must be a single line the operator
  runs verbatim on the box through `remote_run_m1.sh`.
- Payload layout on the box: `~/m1_run/run_m1.py`, `~/m1_run/onbox_m1.sh`, `~/m1_run/frozen/provenance.py`,
  `~/m1_run/data/L0123001.rda`, `~/m1_run/data/airGR_1.7.9.tar.gz`. Results under `~/m1_run/results_m1/out/`.

## Toolchain on the box (installed by `onbox_m1.sh`, each step logged with versions)

1. **Use the image's preinstalled JAX as is** (gate addendum A1). Do NOT run `pip install -U "jax[cuda12]"`: on
   launch 1 that download ran at about 450 kB/s and timed out inside the 766 MB cuDNN wheel. The image already has
   JAX 0.6.0 with a CUDA device (`python3 -c "import jax; print(jax.devices())"` gave `[CudaDevice(id=0)]`). Install
   only `python3 -m pip install --user pyreadr` (pure Python, small). Assert `jax.devices()` includes a GPU; otherwise
   write RUN_VALID false and exit 3. No silent CPU fallback. Record `jax.__version__` and `jaxlib.__version__` in
   env.txt and in every timing record.
2. R and airGR as in checklist item 3.
3. `pip freeze`, `R --version`, `nvidia-smi -q`, `nproc` to `results_m1/out/env.txt`.

## Local selftest

`python3 run_m1.py --selftest` is stdlib-only (guard the jax, pyreadr and numpy imports) and runs under `timeout
300`. It covers every parser, the planted rows in checklist items 5 to 9, and record writing through
`frozen/provenance.py`. No local venv, no local jax, no local R.

## What the runner writes (`results_m1/out/`)

- One provenance.py record per endpoint E1..E7 and per control I1..I7 (`cell`, `inputs` with hashes, `metric`,
  `values`, `threshold`, `decision_rule` written before values, `decision`).
- Raw rows, one JSON line each: every timed pass (`backend`, `n_chains`, `seed`, `repeat`, `ms`, `params_mode`),
  every probe block, every anchor evaluation (period, parameter set, NSE, MARE).
- `RUN_VALID.json`; `env.txt`; `RUN_DONE` marker with the exit code.

## airGR semantics the JAX model must follow (from the committed source, not from memory)

Read `airGR/R/RunModel_GR4J.R`, `airGR/R/CreateRunOptions.R`, `airGR/R/TransfoParam_GR4J.R` and
`airGR/src/frun_GR4J.f90` for: the production store, percolation, the two unit hydrographs (UH1 of length X4, UH2 of
length 2 X4) and their S-curves, the groundwater exchange term, the routing store, the default warm-up and the default
initial store levels. Run period 1990-01-01 to 1990-02-28 inclusive; NSE is `ErrorCrit_NSE` on `Qmm`, untransformed.
