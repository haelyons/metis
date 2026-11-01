Run9 records support **true absence of CUDA work**: measured GPU utilisation 0%; configured baseline CPU/MPI; published FroDock path already CPU/MPI. No recorded CUDA injection or capture failure. Empty CUDA summaries correctly represent this run's CUDA activity. This conclusion does not establish scientific validity or downstream profile-gate acceptance.

| Status field | Finding |
| --- | --- |
| `gpu_util_during_command` | `zero` |
| `compute_api` | `cpu_only` |
| `api_choice` | `published` |
| `nsys_capture_problem` | `no` |
| `published_gpu_workload` | `no` |
| `empty_reports_true_finding` | `yes` |

**1. GPU utilisation during command interval.** Source directory `run9/agent/results/profile/out/profile/` (paths below relative to working directory unless stated). `raw_wall_s.json:1` records:

```json
{"total_wall_s": 5621.4601993279975, "start_monotonic_s": 30267.410915074}
```

Selected telemetry using `start <= sample.t < start + total_wall_s`. End = **35888.871114402** on same monotonic clock. Parsed `gpu_util_raw.jsonl` locally with Python standard library; checked finite timestamps and percentages, utilisation range [0,100], and strictly increasing timestamps. No workload executed.

| Quantity | Measured value |
| --- | ---: |
| Total telemetry samples | 39,680 |
| Samples before command start | 10 |
| Samples during command | **38,622** |
| Samples at/after command end, excluded | 1,048 |
| Mean utilisation during command | **0.0%** |
| Minimum / maximum during command | 0.0% / 0.0% |
| Nonzero samples during command | 0 |
| First included sample | line 11: `t=30267.518397287`, `util=0.0` |
| Last included sample | line 38632: `t=35888.84141169`, `util=0.0` |
| First-sample delay from command start | 0.107482213 s |
| Last-sample distance to command end | 0.029702712 s |
| Median / maximum included sampling gap | 0.145315915 s / 0.243400935 s |

Arithmetic mean = sum of included utilisation percentages / 38,622. Every sample in entire file also equals zero. No averaging over profiler finalization or report export was substituted for command interval. Sampling alone cannot exclude extremely short GPU activity; compute-path evidence below supplies independent support.

Clock interpretation verified against repository `../../../dut/pipeline/m5/profile_nsys.sh:99-120`: sampler stamps `time.monotonic()` before `nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits`; inner launcher measures `bash <command_file>` using same clock. Sampler records arithmetic mean across returned GPUs. `SCHEMAS.md:72,76` confirms shared-command timing and telemetry filtering. Repository root actually three levels above working directory; requested files absent at two-level path.

Box probe `run9/agent/results/probe/out/probe.json:98-117` records 26 host CPUs, NVIDIA H100 PCIe, driver 570.148.08, and CUDA compiler installations. Thus GPU hardware existed; `GPU_COUNT=0` below describes workload configuration, not absent physical GPU. Probe's `cuda_version` value contains unsupported-query text; not treated as valid CUDA version or Nsight error.

**2. Compute API and origin of choice.** Baseline uses CPU/MPI FroDock 3.12 via PINDER, followed by PINDER evaluation. No CUDA, OpenCL, or other GPU compute path appears in recorded configuration. CPU choice belongs to published FroDock implementation selected as baseline; records show no GPU-platform failure followed by CPU backend selection.

Evidence:

- `run9/agent/intake/baseline.json:2-4` identifies FroDock 3.12/PINDER, pinned PINDER commit `ebeb28a2f8411363cef722b7d293c978f7442672`. Lines 18,25 identify upstream Dockerfile, README and adapter as command/configuration sources. Lines 26-38 record published eight-stage adapter: `mpirun -np <mpi_np> --use-hwthread-cpus` invokes `frodockgrid_mpi_gcc` and `frodock_mpi_gcc`, followed by `frodockcluster_gcc` and `frodockview_gcc`. Lines 40-52 record published configuration, MPI default 8 and CPU container base.
- `run9/agent/intake/EXECUTION.json:36`: `"hardware_note": "the FroDock baseline is CPU and MPI only; GPU time is not part of this baseline's timing scope. Host CPU model, core count and mpi_np are recorded with every timing number."` Representative scale fixes 8 systems, holo/apo pairings, 16 jobs, 50 poses/job, MPI ranks 8. Intake selected workload and scale; no evidence of replacing GPU backend with CPU backend.
- `run9/agent/harness/run_command.sh:12-13,22-28` explicitly declares CPU/MPI baseline, exports `CUDA_VISIBLE_DEVICES=""`, sets `BASELINE_GPU_COUNT=0`, method `frodock`, MPI ranks 8. Lines 99-110 validate and print configuration. Lines 119-120 invoke `pinder_methods predict --method frodock`; line 180 invokes `pinder_eval --max_workers 8`.
- Actual profiled `baseline.log:7`: `CONFIG method=frodock subset=pinder-s pairs=holo,apo n_jobs=16 n_solutions=50 mpi_np=8 force=False CUDA_VISIBLE_DEVICES='' host_nproc=26 PINDER_BASE_DIR=data`. Line 8: `GPU_COUNT=0 CUDA_SELECTION=distro:/usr/bin/nvcc MPIRUN=/usr/bin/mpirun FRODOCK_BIN=.../baseline-published/frodock/bin`. `CUDA_SELECTION` reports toolkit discovery, not CUDA execution. Script lines 34-44 perform that discovery unconditionally, with comment stating toolkit unused by CPU baseline.
- `run9/agent/harness/setup.sh:85-99` likewise states CPU/MPI build does not compile against CUDA. Lines 215-242 build published FroDock tools; compiled/prebuilt fallback changes binary provenance, not CPU/GPU API. Actual `run9/agent/results/reproduce/out/setup/setup.log:22-25` and `setup_record.json.frodock_binaries` mark all four tools **compiled**. No prebuilt fallback was selected. Setup record identifies Intel Xeon Platinum 8480+, Open MPI 4.1.2.
- Build log `run9/agent/results/reproduce/out/setup/compile_frodock.log:6851` links `frodock_mpi_gcc` with `mpiCC`, FroDock libraries and `-lfftw3f`; line 7011 links `frodockgrid_mpi_gcc` with `mpiCC` and host libraries. Targeted search found no CUDA/OpenCL compiler or linker invocation. Installed PyTorch and CUDA toolkit entries in setup records establish availability only, not use by this method.
- Read recorded source patch `run9/agent/results/reproduce/out/setup/pinder_frodock_fixes.applied.patch`: fixes action enum, CSV reader, input/path handling and decoy glob copying. Patch retains published MPI/GCC stage names; no GPU-to-CPU platform switch. Harness also restores blank ligand chain labels before evaluation (`run_command.sh:126-174`); no compute API change there.

Reproduction corroboration: `run9/agent/harness/run_anchors.sh:31-37` directly invokes same `bash harness/run_command.sh` and propagates failure. `SCHEMAS.md:54,72` requires same command and environment for anchors/profile; profiler source lines 116-129 implements that behavior without environment rewriting. Final anchors log `run9/agent/results/reproduce/0116-anchors.log:5-6` prints same CPU/MPI configuration; lines 11117 and 16202 show `PREDICT_EXIT=0`, `EVAL_EXIT=0`; line 16203 shows command exit 0. Earlier `0112-anchors.log` and `0114-anchors.log` also print zero-GPU configuration before their failures. No recorded GPU failure induced change of backend between attempts.

**3. Nsight capture diagnostics.** `nsys-version.txt:1`: `NVIDIA Nsight Systems version 2025.3.1.90-253135822126v0`. `profile_nsys.sh:127-130` requests `--trace=cuda,nvtx,osrt --sample=none` around shared command. Targeted case-insensitive searches across original `baseline.log` and `stats.log` found no injection failure, unsupported CUDA API warning, static CUDA runtime warning, untraced-process warning, failed CUDA tracing, or detached-child warning.

`baseline.log:1-2` does contain:

```text
WARNING: CPU context switch tracing not supported, disabling.
Try the 'nsys status --environment' command to learn more.
```

This concerns CPU context-switch tracing; no accompanying CUDA capture failure. `baseline.log:11119,16204` reports prediction/evaluation exit 0; lines 16205-16209 show collection and generated `baseline.nsys-rep`. Other messages include Python logging-format errors, FroDock ligand-size warnings, MPI process exit 1 messages (e.g. lines 48-56), and evaluation missing-system penalties. Those concern workload behavior; none reports Nsight injection failure or CPU fallback from GPU API. Their scientific implications remain outside this diagnosis.

Original `stats.log:2,6,10` reports `PROCESSED (EMPTY RESULTS)` for kernel, memory and API reports. Matching lines:

```text
4: SKIPPED: out/profile/baseline.sqlite does not contain CUDA kernel data.
8: SKIPPED: out/profile/baseline.sqlite does not contain GPU memory data.
12: SKIPPED: out/profile/baseline.sqlite does not contain CUDA trace data.
```

All three original summary CSVs have exactly zero bytes. `nsys_capture_problem=no` means these records show no CUDA capture problem; does not certify Nsight tracing for arbitrary future GPU runs. Existing CPU-context warning does not explain missed CUDA work here.

**4. Published GPU description.** Recorded published baseline is CPU/MPI FroDock, not described as GPU workload. `intake_mirror/BRIEF_run5.md:1-23` asks scientific docking/parallel-search questions; line 12 asks whether restructuring search *could* exploit GPU hardware. That proposed investigation is distinct from assertion that existing baseline already uses GPU. Materials lines 54,57-58 describe FroDock 3.12 and GNU/MPI tools. Intake's published adapter/configuration records and CPU-only hardware note above support `published_gpu_workload=no`.

Materials identity caveat retained: `BRIEF_run5.md:40,44` and `baseline.json.material_identity_caveat` identify owner-approved unverified FroDock mirror. Identity with original study distribution remains unestablished. CPU/MPI classification describes recorded published configuration and actual mirrored baseline run; no claim of proven byte identity with original distribution.

Read prior `run9_diag2/{status.json,REPORT.md}` and `run9_diag3/{status.json,REPORT.md}` as requested. Their parser/empty-export findings agree with original files. Recomputed telemetry and inspected original command/intake/build records independently rather than relying on prior `workload_has_cuda_kernels` classification. Combined evidence supports `empty_reports_true_finding=yes`: this recorded CPU/MPI workload did no CUDA compute work, so zero CUDA timing is correct. Empty exports alone would not support same conclusion for other workloads.

Local read-only diagnosis except requested outputs under `run9_diag4/`. Used directory/file sizes before targeted reads; large `.nsys-rep`, SQLite, decoy archives and result trees were not opened. Logs inspected by head, tail and targeted searches. No workloads, box contact, network fetches, git commands, credential or `.keys` reads, or reads under `~/.codex/`. No pipeline or harness changes.
