# Takeaways from the second measurement run

This note covers one speed test of three ways to solve a tridiagonal system of equations. It assumes you have never seen the project.

A tridiagonal system is a chain of N equations. Each equation links only its two neighbours. Each measured sentence below names its solver, which plays the role of the model [^1]. The numbers come from one rented 40 GB data-centre graphics card (GPU) and one CPU core.

Words used throughout:

- **One-thread solver**: the Thomas algorithm, written by hand, running on a single GPU thread per system. It sweeps forward, then back.
- **Parallel solver**: parallel cyclic reduction, written by hand. It uses one GPU thread per equation and about log2(N) rounds.
- **Vendor solver**: the graphics-card maker's own library routine for the same job.
- **CPU library solver**: the standard LAPACK tridiagonal routine, run on one CPU core through scipy.
- **Speedup**: slower solver's median time divided by faster solver's median time. The median is taken over five random systems.
- **Residual**: how badly a computed answer fails to satisfy the equations, as a relative size. Near 1e-16 is as good as double precision allows.


## 1. Research question and hypothesis

The project keeps "cards": written plans that predict an outcome before anything is measured. One card proposed using a GPU's width on a single tridiagonal correction step inside a larger calculation. Width means thousands of threads working at once.

The question was this. Does that card's own decision rule give its predicted outcome ("lever") on its own hardware? And do the card's four numbers still hold once measured?

The hypothesis the card stated is that feeding GPU width to one solve shortens its wall-clock time. The card's decision rule says "lever" only if two things are true. First, the parallel solver must beat the one-thread solver by at least 2 times at N = 2^24 (16,777,216 equations). Second, that speedup must grow as N grows.

The four numbers the card promised to be checked later were these:

- The worst residual, guessed at 1e-13.
- The smallest N where the parallel solver wins, guessed at 1,024.
- The speedup at 2^24, taken from a 2009 study on an older graphics card against a CPU library. That study gave 28.
- The time needed for the whole run, planned at 2 hours.

## 2. What the experiment tried to find

It timed the one-thread solver and the parallel solver at five sizes: 2^10, 2^14, 2^18, 2^22 and 2^24. Each size used five random systems (seeds 0 to 4). The matrices have a diagonal of 3 and off-diagonals of plus or minus 1, so they are safely well behaved.

Before any timing, both hand-written solvers had to pass a check at 2^10 and 2^14. Each had to reach a residual of 1e-10 or lower. Each also had to match two independent references to within 1e-8. The references were the vendor solver and the CPU library solver.

Four extra readings were declared in advance as report-only. They do not decide the card. They are exploratory, and I label them that way below.

- The shape of the parallel solver's time against N.
- The same rule re-read against the CPU library solver instead of the one-thread solver.
- A test solving many systems at once with the one-thread solver.
- The vendor solver's time, as a yardstick.

## 3. What was predicted, and what happened

The run was valid. No stage failed, and no result was voided. Every planted-case control passed. The anchor check passed for both hand-written solvers.

**Anchor check (passed).** The largest residual of the one-thread solver was 1.39e-16, measured on seed 0 at 2^14. The parallel solver's largest was 3.11e-16 at 2^14. The largest difference from either reference was 2.57e-16, for the parallel solver against the CPU library at 2^10. The vendor solver and CPU library solver differed from each other by at most 2.57e-16 [^1].

**Prediction 1: residual about 1e-13, holds if between 1e-14 and 1e-12. Refuted.** The worst residual of the two hand-written solvers was 3.11e-16 (parallel solver, 2^14). The parallel solver's worst residual is 321.4 times below the guess [^1]. The error is in the good direction, but the guess was still wrong by more than the allowed 10 times.

**Prediction 2: the parallel solver already wins at N = 1,024. Held, with a caveat.** Against the one-thread solver, the lower quartile of the speedup at 2^10 was 8.54, above 1. Lower quartile means the value a quarter of the way up the five seeds. The crossover was therefore 2^10. The run labelled it launch-bound, because 0.775 of the parallel solver's time at 2^10 was kernel-launch gaps. See section 5 for what changes with a CPU baseline.

**Prediction 3: the card's rule gives "lever". Held.** Against the one-thread solver, the median speedups at the five sizes were 8.54, 95.90, 517.53, 395.38 and 348.30 [^1]. The parallel solver's 2^24 speedup of 348.30 over the one-thread solver is far above 2. The lower quartile at 2^24 was 348.29, so the result is not within noise. The slope of log speedup against log2(N) was +0.256, so it is positive [^1]. The outcome is "lever". Two adjacent steps fell: 517.53 to 395.38, then 395.38 to 348.30 [^1].

**Prediction 4: speedup at 2^24 near 28, holds if between 9.3 and 84. Refuted.** The one-thread solver took a median 7598.5 ms and the parallel solver 21.8 ms at 2^24, giving 348.30. That is 12.44 times the old figure of 28, above the allowed band [^1].

**Prediction 5: the run needs 2 hours, holds if between 0.67 and 6 hours [^1]. Refuted.** The on-box time from first anchor solve to last sweep row was 0.119 hours, about 7.15 minutes [^1]. The plan over-bought by about 16.8 times [^1].

### Exploratory readings (report-only)

**Shape of the parallel solver's time.** The card says time "grows like log2(N)". The parallel solver took 4.785 ms at 2^22 and 21.816 ms at 2^24, a factor of 2.135 per doubling of N. That is labelled linear-like, since the cut-off is 1.7 [^1]. The card's sentence is wrong at large N.

**CPU library as the baseline.** The CPU library solver took a median 416.7 ms at 2^24. The parallel solver's speedup over it was 0.59, 5.78, 30.71, 18.41 and 19.10 at the five sizes [^1]. The rule still gives "lever" under that baseline. But at 2^10 the CPU is faster, since 0.59 is below 1.

**Many systems at once.** The one-thread solver was run on 256, 256, 256, 64 and 16 systems together at the five sizes. The time ratios to one system were 1.08, 1.76, 1.81, 1.08 and 1.05 [^1]. All sit inside the allowed 0.9 to 3, so the card's claim held [^1].

**Vendor solver.** The vendor solver took 0.0148, 0.0490, 0.0994, 0.800 and 2.943 ms at the five sizes [^1]. The hand-written parallel solver took 2.35, 1.09, 1.62, 5.98 and 7.41 times as long [^1].

## 4. Is this what we expected?

Partly. The headline outcome matched the card: the rule reads "lever". Three of the four numbers did not match. The residual guess, the 28 speedup and the 2-hour plan were all refuted. The crossover guess survived.

The "lever" verdict is weaker than it looks. Its baseline is a single GPU thread, which is the slowest sensible way to run the older method. Against the CPU library solver, the 2^24 speedup is 19.10, not 348.30. Against the vendor solver, the hand-written parallel solver is 7.41 times slower at 2^24. These are exploratory readings. They do not change the card's verdict.

## 5. What in these files does not fit

### Open questions

**1. Why was the 2^24 speedup measured against one GPU thread, not the CPU library?**

The old 28 came from a parallel solver against a CPU library. Against the one-thread solver the run got 348.30, which is 12.44 times too high [^1]. Against the CPU library it got 19.10, which is 0.68 of 28 and inside the band [^1]. Median times at 2^24 were 7598.5 ms (one thread), 416.7 ms (CPU library), 21.8 ms (parallel solver) and 2.94 ms (vendor solver). The one-thread solver is 18.2 times slower than the CPU library solver on one core [^1]. The vendor solver is 2582 times faster than that thread. If the card meant the CPU library, the miss comes from the baseline, not from the old figure travelling badly. The headline would shrink from 348 to 19. The files do not say which baseline the card meant.

**2. Does the CPU library beat the parallel solver at the smallest size?**

Yes, on the CPU baseline. The speedup at 2^10 was 0.59 and at 2^14 it was 5.78. Under that baseline the card's claim of winning at the smallest size fails. The crossover then sits between 2^10 and 2^14. The prediction was marked "holds" only because the one-thread baseline gave 8.54 [^1]. At 2^24 the five CPU library times ran from 370.3 to 484.6 ms. The five one-thread solver times at 2^24 differ by only about 0.004 percent, so the seeds add almost no noise information there.

**3. Do the timed solves include moving data to the GPU?**

The records never say. They show timed blocks of repeated solves on data already on the card. At 2^24 each of four input arrays is 134.2 MB, 536.9 MB in all. At an assumed 25 GB/s link, which is my assumption and not in the files, a copy would take about 21 ms. That is about the parallel solver's 21.8 ms [^1]. The speedup over the CPU library would roughly halve from 19.10, and 348 would fall much further [^1]. The design needs a case with data resident and a case with data copied.

**4. Does speedup really grow with size, when it peaks at 2^18?**

The one-thread solver speedups were 8.54, 95.90, 517.53, 395.38 and 348.30. The rule compares only 2^24 with 2^10, plus a slope of +0.256 over all five. So "grows" passes through its endpoints while the top three levels fall. The one-thread solver cost 317 ns per equation at 2^18 and 451 ns at 2^22. The parallel solver's time grew 29.8 times over that step while size grew 16 times [^1]. Something changes between 2^18 and 2^22. Cache size is one guess, and the files never test it. Any extrapolation to larger N is unsupported.

**5. How much small-size time is launch overhead, and were all blocks at least 50 ms?**

The design expected launch gaps to inflate small-size time by at most about 2 times. Measured launch share of parallel-solver time was 0.775 at 2^10 and 0.703 at 2^14. That would allow up to about 4.4 times [^1]. Timed blocks under 50 ms numbered 52 of 125 timing rows, so the design's rule was often missed. I counted 77 of 150 when the launch-probe rows are included. Examples are the parallel solver at 2^10, 2^14 and 2^18, and the vendor solver at four sizes. The 8.54 and 95.90 speedups mostly measure launch cost [^1]. The empty-kernel test cost 50 microseconds per launch at 2^24, which is block scheduling, not launch delay.

**6. Why was the many-systems test never compared with the parallel solver?**

The ratios were 1.08, 1.76, 1.81, 1.08 and 1.05, all inside the band [^1]. At 2^10, 256 systems took 0.3218 ms, which is 1.26 microseconds each. One parallel-solver solve took 34.8 microseconds [^1]. If the real calculation has many independent systems, plain Thomas is about 27 times faster per system at 2^10. At 2^24 it loses: 16 systems took 7965 ms. The ratios 1.76 and 1.81 at 2^14 and 2^18 are unexplained. Only 256 GPU threads were busy, a tiny part of the card.

**7. Does "linear-like" describe the parallel solver, with one factor of 2.135 from two levels?**

The factor of 2.135 uses only 2^22 and 2^24. Exactly linear would be 2.0, so the time is steeper than linear at the top [^1]. From 2^10 to 2^14 the factor is 1.11 per doubling, which would read as log-like. Neither label fits. The word "linear-like" hides a flat stretch followed by a superlinear one.

**8. Could the 2-hour estimate ever have been judged too low, and what did 0.119 hours cover [^1]?**

Every stage started with a time cap near 3482 s, about 0.97 hours. So the upper half of the band could never be seen [^1]. The 0.119 hours counts first anchor solve to last sweep row [^1]. It excludes setup and installs. The 16.8 times over-buy is therefore not like for like [^1]. The stage log shows a budget_left of 6.0 dollars throughout [^1]. Scipy 1.8.0 and numpy 1.26.4 are both recorded [^1]. The files I read do not state that this pair is unsupported, so I cannot confirm that part.

### Further things I found

- **The floor library differs from the card.** The card names MKL as the CPU floor. The run recorded OpenBLAS 0.3.20 behind scipy, on one thread [^1]. The vendor field reads as unnamed.
- **Installs happened despite the design.** The design planned no installs. The first lines of the run log show a setup step adding transformers, accelerate and scikit-learn.
- **The card was rejected by its own reviewer.** The run labels record "card dramaturg: REJECT (3 blocking, citations)". The run went ahead anyway.
- **The five seeds are not independent boxes.** The summary says the seeds are five generated systems on one machine. Tight spreads reflect one machine, not run-to-run variation across machines.
- **"Refuted" on the residual is symmetric by design.** The band is 10 times either way. A result 321.4 times better than guessed counts as refuted, though nothing went wrong [^1].
- **The growth rule is weak.** It passes with a fall of 32.7 percent from the 2^18 peak to 2^24.
- **The CPU side is the noisy side.** The CPU library times at 2^24 ran 370.3 to 484.6 ms, a spread of 31 percent. The one-thread solver spread was about 0.004 percent [^1].
- **Dates.** Files on disk are stamped 11:00, but the run's records say 09:51 to 09:58 UTC. They were evidently copied afterwards.

[^1]: This project has no language models. Each measured sentence names the solver or baseline it describes, which plays the role of the model.

## Raw samples, verbatim

Five rows were picked at random with a fixed seed. Each is one line, exactly as stored.

An input row: the generated system fingerprint used for one-thread solver timing.

```json
{"N": 16777216, "a": {"first8": [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, -1.0], "n": 16777216, "sha256": "e2b5410920d7d30d82dc31deed0379efba4a78c7aa8ff9c56fd04e84427fd379"}, "anchor_failed": [], "b": {"first8": [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0], "n": 16777216, "sha256": "295948a1de46b54fe093d2551510ebae242f0f646074021e80916926a61b5080"}, "c": {"first8": [1.0, 1.0, 1.0, 1.0, -1.0, 1.0, -1.0, -1.0], "n": 16777216, "sha256": "0fb0a08dbb35aa22ab440bb3b11379747910fd2e15c8a0667576817a46846be3"}, "context": "thomas_gpu", "d": {"first8": [0.276472080635235, -0.5187778639281005, 0.814970759465404, 0.4022427886374344, -0.16567555068627843, -1.171986060213274, 0.9237282420657763, -0.01891539322137044], "n": 16777216, "sha256": "08bcb0906132a2770167fb1e6f00cef2af71e91ed9e970a294227b3d5363239b"}, "kind": "system", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "one_reference_only": false, "run_valid": true, "seed": 4, "t_written_utc": 1792490101.1019228}
```

An input row: the generated system fingerprint used for parallel solver timing.

```json
{"N": 262144, "a": {"first8": [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, -1.0], "n": 262144, "sha256": "b62d08a5ecf27c3a273b0ba990ca5d057cb1064c60469a70ad4ffd650d0c569d"}, "anchor_failed": [], "b": {"first8": [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0], "n": 262144, "sha256": "fe5439c2b011ec45fd12206b6f36c36f4d5a0e433070dfba337e6369938ca237"}, "c": {"first8": [1.0, -1.0, 1.0, 1.0, 1.0, -1.0, 1.0, 1.0], "n": 262144, "sha256": "3deb6dd52cf42787975119736c02839ef3e39b7beca11dbcdd8afcec5c80737f"}, "context": "pcr_gpu", "d": {"first8": [-0.5289394796393546, -0.8021523777922626, 0.4092672367525235, 0.9808994085506736, -0.28371766505553736, 0.2126220765650628, -0.5122409840628848, -0.804789456234628], "n": 262144, "sha256": "1c9d4501a73fd365ccf3f56637b5007c3421719146122d5f37620d2a2c2d069b"}, "kind": "system", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "one_reference_only": false, "run_valid": true, "seed": 4, "t_written_utc": 1792490125.3763971}
```

An output row: one timing of the one-thread solver.

```json
{"K": 1, "N": 16777216, "R": 1, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "thomas_gpu", "block_at_least_50ms": true, "block_dim": 1, "block_ms": 7598.57470703125, "degenerate": null, "grid": 1, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "ms_per_solve": 7598.57470703125, "one_reference_only": false, "run_valid": true, "seed": 3, "t_written_utc": 1792490099.6330864, "warmup_ms": [7613.25341796875, 7598.34033203125], "x_all_zero": false, "x_finite": true, "x_first8": [0.4858339846436915, 0.09004596052209478, -0.08469506984409962, -0.5191058190665746, -0.08251707041533349, -0.03677784537515155, -0.35350881187299743, -0.858629709765579]}
```

An output row: one timing of the vendor solver.

```json
{"K": 1, "N": 16777216, "R": 17, "anchor_failed": [], "anchor_status": null, "arm": "cusparse_gpu", "block_at_least_50ms": true, "block_ms": 51.316734313964844, "buffer_bytes": 537001984, "copies_in_timed_block": 17, "copies_made": 19, "copy_rule": "one right-hand-side copy per solve, made before the timed block", "degenerate": null, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "ms_per_solve": 3.018631430233226, "one_reference_only": false, "run_valid": true, "seed": 0, "t_written_utc": 1792490141.453078, "warmup_ms": [3.0402560234069824, 3.1037440299987793], "x_all_zero": false, "x_finite": true, "x_first8": [0.6075402993412365, 0.06100850417175658, 0.06456682918909255, 0.08331669779459235, -0.30744345506579757, 0.1155971595029857, -0.0024099841672812067, 0.6290760657074215]}
```

An output row: one timing of the CPU library solver.

```json
{"N": 262144, "R": 11, "anchor_failed": [], "anchor_status": null, "arm": "cpu_dgtsv", "block_at_least_50ms": true, "block_ms": 55.084218999922996, "copies_in_timed_block": 11, "copies_made": 13, "copy_rule": "dgtsv overwrites its inputs; one input copy per call, made before the timed block", "degenerate": null, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "mkl_num_threads": "1", "ms_per_solve": 5.007656272720272, "omp_num_threads": "1", "one_reference_only": false, "openblas_num_threads": "1", "run_valid": true, "seed": 0, "solver_status": 0, "t_written_utc": 1792490314.3089788, "warmup_ms": [4.941432999999051, 4.947831000094993], "x_all_zero": false, "x_finite": true, "x_first8": [-0.08387418168427681, -0.22580580719882387, -0.10950277566928442, 0.32556062571111305, -0.1592872501953151, 0.21055459023441056, 0.0298577177677514, 0.6598599201515274]}
```

## Gate outputs

```
/tmp/claude-1000/s/trunc.md: 1.3 codes/1000 words (3 codes, 2383 words); threshold 10.0
0 unscoped result sentence(s)
```
