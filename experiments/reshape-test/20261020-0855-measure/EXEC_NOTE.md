# Execution directive for build (tag m2)

Binding order: GATE_COMMIT.md item answers first, this note second, out/design_record.json third. Where silent, the
design record binds as written, GUESS values included. The build does not read GATE_COMMIT.md itself; the checklist
below carries every gate change the build must implement.

## Where to write

The run directory is `/home/hal/dev/interp/metis/experiments/reshape-test/20261020-0855-measure/`. Write exactly
`run_m2.py` and `onbox_m2.sh` there, by absolute path. Write nothing anywhere else. Read the design record at
`/home/hal/dev/interp/metis/experiments/reshape-test/20261020-0855-measure/out/design_record.json` and the conventions
in `frozen/` (provenance.py is the record writer; lambda_run.sh and remote_run.sh show what the box does). There is no
`data/` directory: every system is generated on the box from (N, seed).

## The two-files law and the CUDA source

The CUDA C source (Thomas, batched Thomas, PCR, the empty launch-probe kernel, and thin C wrappers for memory, timing
and the cuSPARSE call) lives as a string constant inside `run_m2.py`. On the box, `run_m2.py build` writes it to
`results_m2/build/m2_kernels.cu`, records its sha256, and compiles it with
`nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart`
(add `-arch=sm_80` when nvcc reports the A100; otherwise leave the default). Python calls it through `ctypes`. nvcc is
looked up on PATH, then `/usr/local/cuda/bin/nvcc`, then `/usr/local/cuda-*/bin/nvcc`; `nvcc --version` is recorded.
If nvcc is absent or compilation fails: RUN_VALID false, `m2_summary.json` written, exit 2. No install, no fallback.

## Checklist of gate changes the build must carry (16 entries)

1. **D1.** Thomas kernel: one thread per system (`<<<1,1>>>` for the single system; for the batched arm one block per
   system with one thread, blockDim 1, systems laid out one after another). Forward: for i = 1..N-1, w = a_i /
   b'_{i-1}; b'_i = b_i - w c_{i-1}; d'_i = d_i - w d'_{i-1}, with the previous b' and d' carried in registers; back: x_i =
   (d'_i - c_i x_{i+1}) / b'_i. Scratch arrays b', d' in global memory, written once per step. No variant search.
2. **D2.** An anchor failure (E1) for one solver sets that solver's timing rows to label "descriptive only; anchor
   failed" and writes E3, E4, E5 as NOT_READ. The box continues. If cuSPARSE and scipy disagree with each other
   (>= 1e-8 relative), run_valid is false in every record written after.
3. **D3.** E3's "grows with N": speedup(2^24) > speedup(2^10) AND least-squares slope of ln(speedup) against log2(N)
   over the five levels > 0. The E3 record also lists every adjacent-level decrease.
4. **D4.** E6, E7, E8, E9 records carry `"role": "report-only; does not decide the card"`.
5. **D6.** Every record carries the label "card dramaturg: REJECT (3 blocking, citations)".
6. **R1.** Timed blocks are at least 50 ms (R = max(1, ceil(50 ms / warm-up ms per solve)), R recorded per row). Extra
   arm `launch_probe`: an empty kernel launched R times under the same protocol; ms per launch recorded per level. Every
   PCR row carries `launch_fraction = log2(N) x ms_per_launch / ms_per_solve`; the E3 and E4 records report it at 2^10
   and 2^24; `launch_fraction > 0.5` at 2^10 labels E4 "crossover at 2^10 is launch-bound".
7. **I1.** On the box at N = 2^10, seed 0: x* = ones, d = A x*: readout residual <= 1e-14; x* perturbed by 1e-6
   relative: readout in [1e-7, 1e-5]; cuSPARSE and scipy agree < 1e-8. Three records.
8. **I2 to I10.** Selftest planted arithmetic exactly as listed in GATE_COMMIT.md items I2 to I10 (copied here):
   - I2: residual 1e-13 holds; 5e-15 refuted "too pessimistic"; 5e-12 refuted "too optimistic".
   - I3: Thomas [1, 16, 256, 4096, 16384], PCR [0.5, 0.6, 1, 10, 40] give speedups [2, 26.667, 256, 409.6, 409.6],
     slope > 0, if_lever; equal speedups give if_not; speedup(2^24) = 1.9 gives if_not; lower quartile 1.8 with
     median 3 at 2^24 gives if_lever "within noise". 4 digits.
   - I4: lower quartiles [1.2, 3, 10, 50, 100] give crossover 2^10 (holds); [0.8, 1.5, 10, 50, 100] give 2^14
     (refuted); all below 1 give none (refuted).
   - I5: 28 holds; 100 refuted above (ratio 3.571); 5 refuted below.
   - I6: (10, 11) gives g 1.0488 log-like; (10, 40) gives 2 linear-like; (10, 20) gives 1.4142 between.
   - I7: CPU [0.01, 0.1, 2, 40, 160] against PCR [0.5, 0.6, 1, 10, 40] gives speedup_cpu(2^24) = 4, if_lever under
     the CPU baseline; CPU 60 at 2^24 gives 1.5, if_not.
   - I8: ratios [1.0, 1.1, 1.5, 2.9, 1.2] hold; [1.0, 3.5, 1.5, 2.9, 1.2] fail; throughput factor K / ratio exact.
   - I9: cuSPARSE 10 ms against PCR 30 ms gives ratio 3.
   - I10: 0.5 h refuted below; 2 h holds; 7 h refuted above. On the box: timestamps of the first anchor solve and the
     last sweep row written as the E10 record.
9. **Timers (in-run).** 100 ms `time.sleep` within +/- 5 ms; cudaEvent against wall-clock (perf_counter around a
   synchronise) within 5% on one block; a block of 2R solves against R within 15% at N = 2^14 for Thomas and PCR.
10. **Gate propagation (selftest).** Planted E1 failure for Thomas (residual 1e-9) labels Thomas rows and writes E3,
    E4, E5 NOT_READ; planted reference disagreement (1e-7) sets run_valid false in every record written after it.
11. **Labels.** Every timing record carries instance type (`INSTANCE_TYPE`), GPU name and driver (nvidia-smi), CUDA
    runtime version (cudaRuntimeGetVersion via ctypes), nvcc version, vCPU count, scipy's BLAS/LAPACK vendor string
    (`scipy.__config__` or `numpy.show_config`), price per hour (`PRICE_USD_PER_HOUR`), R, and the labels in items 5
    and 1 ("baseline: one CUDA thread per system, this build's kernel").
12. **cuSPARSE.** `cusparseDgtsv2_nopivot_bufferSizeExt` then `cusparseDgtsv2_nopivot` (m = N, n = 1, ldb = N), through
    the C wrapper in the .so (linked with -lcusparse), buffer allocated once per level outside the timed block. If
    the library is missing at link or load time: the cusparse arm is NOT_RUN, E1 reads against scipy alone with label
    "one reference only", E9 NOT_RUN, the run continues.
13. **CPU floor.** `scipy.linalg.lapack.dgtsv(dl, d, du, b)` overwrites its inputs: make the R input copies before the
    timed block, record the copy count; `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1` exported by
    `onbox_m2.sh`. Anchor reference on the CPU: `scipy.linalg.solve_banded((1, 1), ab, d)`.
14. **Order on the box.** toolchain check and compile; GPU check; anchor (E1, E2, I1); timers; residual_sweep; then the
    timing arms, each over all levels ascending: thomas_gpu, pcr_gpu, cusparse_gpu, thomas_batched_gpu, launch_probe,
    cpu_dgtsv; then endpoints E3 to E10. A cost guard before every stage.
15. **Cost guard and summary.** `onbox_m2.sh` reads `PRICE_USD_PER_HOUR` and `BUDGET_LEFT_USD` from the environment and
    stops cleanly, writing RUN_DONE, before projected spend reaches `BUDGET_LEFT_USD`; a time guard keeps the run
    inside `REMOTE_TIMEOUT` (3,600 s unless set). `results_m2/out/m2_summary.json` is written after the endpoints stage,
    after any early stop, and just before RUN_DONE: run_valid, labels, every endpoint and control decision. It
    restates records; it decides nothing.
16. **Toolchain rule.** No venv. No pip install of anything. Preinstalled numpy and scipy (1.8.0 on the m1 image) are
    used as they are; `import scipy.linalg` failing is exit 2 with RUN_VALID false. The GPU check is
    `cudaGetDeviceCount >= 1` through ctypes on libcudart (and nvidia-smi recorded); failure is exit 3, RUN_VALID
    false, no CPU-only fallback. Versions of numpy, scipy, nvcc, driver, CUDA runtime go to `env.txt` and every record.

## Box

- Instance: `gpu_1x_a100_sxm4` (A100 SXM4 40 GB, 30 vCPUs, USD 1.99/h), us-east-1. If no capacity at launch: the
  cheapest single GPU with capacity; the operator records it and every record carries `INSTANCE_TYPE`.
- Launcher: the operator's per-launch copy `lambda_run_m2.sh` (made from `frozen/lambda_run.sh` at the header's declared
  points only): remote dir `m2_run/`; payload `run_m2.py onbox_m2.sh remote_run_m2.sh frozen/provenance.py`; forwarded
  env `PRICE_USD_PER_HOUR BUDGET_LEFT_USD INSTANCE_TYPE`; fetch from `m2_run/results_m2/out/`. `remote_run_m2.sh` is
  `frozen/remote_run.sh` with only its `cd` line changed to `~/m2_run`. Its transformers install is unused here and left
  alone; its CUDA assertion stays.
- Caps: `REMOTE_TIMEOUT=3600`; `BUDGET_LEFT_USD=6` per launch; two launches at most within USD 8.
- Payload layout on the box: `~/m2_run/run_m2.py`, `~/m2_run/onbox_m2.sh`, `~/m2_run/frozen/provenance.py`. Results
  under `~/m2_run/results_m2/out/`; the compiled library under `~/m2_run/results_m2/build/`.
- The build's `onbox_command` must be a single line the operator runs verbatim on the box through `remote_run_m2.sh`.

## Local selftest

`python3 run_m2.py --selftest` is stdlib-only (guard the numpy, scipy and ctypes-CUDA imports) and runs under `timeout
300`. It covers every parser, a pure-Python Thomas on a 16-equation planted system to validate the residual function
and the I1 perturbation band, the planted rows in checklist items 8 and 10, and record writing through
`frozen/provenance.py`. No local venv, no local CUDA, no local scipy.

## What the runner writes (`results_m2/out/`)

- One provenance.py record per endpoint E1..E10 and per control I1..I10, timers, gate-propagation (`cell`, `inputs`
  with hashes, `metric`, `values`, `threshold`, `decision_rule` written before values, `decision`).
- Raw rows, one JSON line each: every timed block (`arm`, `N`, `seed`, `R`, `block_ms`, `ms_per_solve`,
  `launch_fraction` where defined, labels), every residual (`solver`, `N`, `seed`, `rel_residual`, pairwise
  differences), every system's fingerprint (first 8 values of a, b, c, d; sha256 of each array).
- `RUN_VALID.json`; `env.txt`; `m2_summary.json`; `RUN_DONE` marker with the exit code.

## Numerical definitions the build must follow

- System: a_i, c_i in {-1, +1} by seed-fixed random signs (a_0 and c_{N-1} unused and set to 0); b_i = 3; d_i standard
  normal; `numpy.random.default_rng(seed)`, draws in the order a-signs, c-signs, d. float64 everywhere.
- Relative residual: ||A x - d||_2 / ||d||_2 with A x computed as a_i x_{i-1} + b_i x_i + c_i x_{i+1} in float64 numpy on
  the CPU. Pairwise difference: ||x - x_ref||_2 / ||x_ref||_2.
- PCR: standard parallel cyclic reduction, one thread per equation per round, stride s = 1, 2, 4, ..., N/2 (log2(N)
  rounds), zero coefficients outside [0, N); ping-pong buffers; final x_i = d_i / b_i. One kernel launch per round,
  blockDim 256.
- Speedup(N) = median over seeds of Thomas ms / median over seeds of PCR ms; lower quartile of the per-seed ratio
  Thomas_ms(seed) / PCR_ms(seed) is the noise-rule quantity.
