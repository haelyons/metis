Write a baseline harness from "/home/hal/dev/interp/metis/experiments/shakedown-m5/run5/agent/intake"/*.
Never read experiments/, operator/, or control/. Write only under "/home/hal/dev/interp/metis/experiments/shakedown-m5/run5/agent/harness".
The operator already started the dev box. Do not start, stop, or access it; the pipeline runs your scripts.
Run the published build and binary and read measurements from its OUTPUT. Never parse or assert on source text. Measurement checks must fail only on missing or invalid output; the pipeline scores measured values against anchors.
Box probe (collected by the pipeline before harness generation):
{
  "apt_sources": [
    {
      "file": "/etc/apt/sources.list.d/nvidia-docker-container.list",
      "lines": [
        "deb [signed-by=/etc/apt/cloud-init.gpg.d/nvidia-docker-container.gpg] https://nvidia.github.io/libnvidia-container/stable/deb/amd64 /"
      ]
    }
  ],
  "cmake": {
    "path": "/usr/bin/cmake",
    "version": "cmake version 3.22.1"
  },
  "disk_home_avail_bytes": 1430089543680,
  "g++": {
    "path": "/usr/bin/g++",
    "version": "g++ (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0"
  },
  "gcc": {
    "path": "/usr/bin/gcc",
    "version": "gcc (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0"
  },
  "git": {
    "path": "/usr/bin/git",
    "version": "git version 2.34.1"
  },
  "kernel": "6.8.0-60-generic",
  "make": {
    "path": "/usr/bin/make",
    "version": "GNU Make 4.3"
  },
  "memory_kb": 232955528,
  "nproc": 30,
  "nvcc": [
    {
      "path": "/usr/bin/nvcc",
      "version": "nvcc: NVIDIA (R) Cuda compiler driver\nCopyright (c) 2005-2025 NVIDIA Corporation\nBuilt on Fri_Feb_21_20:23:50_PST_2025\nCuda compilation tools, release 12.8, V12.8.93\nBuild cuda_12.8.r12.8/compiler.35583870_0"
    },
    {
      "path": "/usr/local/cuda/bin/nvcc",
      "version": "nvcc: NVIDIA (R) Cuda compiler driver\nCopyright (c) 2005-2025 NVIDIA Corporation\nBuilt on Fri_Feb_21_20:23:50_PST_2025\nCuda compilation tools, release 12.8, V12.8.93\nBuild cuda_12.8.r12.8/compiler.35583870_0"
    },
    {
      "path": "/usr/lib/cuda/bin/nvcc",
      "version": "nvcc: NVIDIA (R) Cuda compiler driver\nCopyright (c) 2005-2025 NVIDIA Corporation\nBuilt on Fri_Feb_21_20:23:50_PST_2025\nCuda compilation tools, release 12.8, V12.8.93\nBuild cuda_12.8.r12.8/compiler.35583870_0"
    }
  ],
  "nvidia": {
    "cuda_version": "Field \"cuda_version\" is not a valid field to query.",
    "driver_version": "570.148.08",
    "gpus": [
      "NVIDIA A10"
    ]
  },
  "os": {
    "id": "ubuntu",
    "name": "Ubuntu",
    "pretty_name": "Ubuntu 22.04.5 LTS",
    "version": "22.04.5 LTS (Jammy Jellyfish)",
    "version_id": "22.04"
  },
  "pip": {
    "path": "/usr/bin/pip",
    "version": "pip 22.0.2 from /usr/lib/python3/dist-packages/pip (python 3.10)"
  },
  "python3": {
    "path": "/usr/bin/python3",
    "version": "Python 3.10.12"
  },
  "sudo_nopasswd": true
}
Use the probe's discovered paths and versions. Never hard-code a toolkit path the probe did not find, even if the brief suggests one. If a required tool is missing, install it with apt only from sources the probe lists; do not add repositories or assume a package exists. Commented source lines are not enabled repositories. If apt cannot supply it, use pip for cmake only; otherwise fail with a clear message.
Write three self-contained bash scripts, invoked from a shared remote working directory with bash harness/<name>:
- setup.sh: build/install the published baseline at its exact intake pin in the stock image. Use sudo only for apt. Preserve stock torch and published source/configuration. Stage source in baseline-published/ and inputs in data/. Do not silently substitute or tune the baseline. Make setup safe to retry once in this directory.
- run_anchors.sh: run the published anchor protocol at the real representative scale declared in EXECUTION.json. Write out/anchors_measured.json as {anchor_id: measured_number}, one finite number per intake anchor. Never copy published values as measurements.
- profile.sh: Run the same baseline once at representative scale. Measure at least 3 timed stages INSIDE the measured run, for example setup or allocation, host-to-device transfers, compute kernels, device-to-host transfers, or host postprocessing. Use the program's own timers or output, CUDA events, nsys if present, or wrapper timings around separable phases. Process-level wrappers (telemetry_start, baseline_process, total process time, etc.) do not count as stages and must not appear in stages.json; any stage wall_s within 2% of total_wall_s counts as a process wrapper. Write out/profile/stages.json as [{stage, kind, wall_s, gpu_s}], with kind compute, transfer, or other (finite nonnegative seconds, gpu_s null when unavailable), and out/profile/total_wall_s.json as {total_wall_s} (finite positive seconds). Sample GPU utilisation with nvidia-smi during the measured run into out/profile/gpu_util.json as a non-empty array [{t, util}], with t finite nonnegative elapsed seconds and util finite percent in [0,100]. Save raw telemetry under out/profile/. Use critical-path stage wall times without double-counting overlap; timed_fraction = min(1, sum(stage.wall_s) / total_wall_s) must be >=0.9. Do not invent GPU timings or replace unavailable GPU timings with allocated time.
Also provide run_evaluation.sh for the published baseline evaluation interface, or make run_anchors.sh handle non-anchor EVAL_MODE. Evaluation uses fresh working directories with baseline-published/, method/, data/, harness/ and payload/ links and absolute BASELINE_DIR, METHOD_DIR, BASELINE_OUT, METHOD_OUT and EVAL_OUT paths. EVAL_PROTOCOL points to the sealed JSON; EVAL_INPUTS and EVAL_SEEDS contain its JSON input and seed specifications; EVAL_COMPUTE_BUDGET is empty except in curve mode. Modes are equivalence, warmup, performance and curve. Run the published configuration on every sealed input/seed, seeds first then input IDs, and write EVAL_OUT/evaluation.json: {records:[{input_id,seed,metrics:{metric_name:finite_number}}],timing_scope,gpu_count,wall_s,compute_budget}. Use null seed for deterministic protocols; timing_scope must equal the seal; wall_s is required for reported_wall scopes; compute_budget is required for curves. Synchronize every used GPU before returning or stopping reported timers; include launch, transfer and merge overhead. Enforce curve budgets in GPU seconds. Always measure actual outputs; never reuse baseline outputs.
Create output directories, preserve logs, and exit nonzero on failure. Read all intake files for pins, commands, data, scale and protocol. Do not run builds or workloads locally.
Return a short completion acknowledgement; the pipeline reads the scripts itself.