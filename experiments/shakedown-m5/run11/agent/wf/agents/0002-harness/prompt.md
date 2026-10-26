Write a baseline harness from "/home/hal/dev/interp/metis/experiments/shakedown-m5/run11/agent/intake"/*.
Never read experiments/, operator/, or control/. Write only under "/home/hal/dev/interp/metis/experiments/shakedown-m5/run11/agent/harness".
The operator already started the dev box. Do not start, stop, or access it; the pipeline runs your scripts.
Scope: setup.sh builds and checks only the baseline. The pipeline owns profiling and profiler installation; do not write profile.sh or install profiling tools. A repair must change only the failing script and stay within its scope. Run the published build and binary and read measurements from its OUTPUT. run_command.sh is the canonical measured command and complete environment, including working directory, arguments, CUDA_VISIBLE_DEVICES and GPU count. run_anchors.sh must invoke bash harness/run_command.sh without overriding its environment or duplicating the workload command; parse its saved output for anchor measurements. The fixed profiler invokes that identical file with bash from the same working directory. Keep output paths stable and preserve logs. Every later run script must preserve the published configuration. Validate printed configuration against the actual command and environment. Preserve consistency in repairs; read the other harness scripts while editing only the failing script. Never parse or assert on source text. Measurement checks must fail only on missing or invalid output; the pipeline scores measured values against anchors.
Script budgets in seconds: setup.sh=1200, run_anchors.sh=1200, fixed profiler=1200, run_evaluation.sh=1200 per invocation (also run_anchors.sh when used as the evaluation adapter); complete evaluation scorer=2400. Use one fixed scale from EXECUTION.json, no scale search or doubling loops, and finish well within the budget.
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
    "version": "cmake version 3.28.3"
  },
  "disk_home_avail_bytes": 5832206266368,
  "g++": {
    "path": "/usr/bin/g++",
    "version": "g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0"
  },
  "gcc": {
    "path": "/usr/bin/gcc",
    "version": "gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0"
  },
  "git": {
    "path": "/usr/bin/git",
    "version": "git version 2.43.0"
  },
  "kernel": "6.8.0-1046-nvidia",
  "make": {
    "path": "/usr/bin/make",
    "version": "GNU Make 4.3"
  },
  "memory_kb": 464156216,
  "nproc": 52,
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
    "driver_version": "580.105.08",
    "gpus": [
      "NVIDIA H100 80GB HBM3",
      "NVIDIA H100 80GB HBM3"
    ]
  },
  "os": {
    "id": "ubuntu",
    "name": "Ubuntu",
    "pretty_name": "Ubuntu 24.04.4 LTS",
    "version": "24.04.4 LTS (Noble Numbat)",
    "version_id": "24.04"
  },
  "pip": {
    "path": "/usr/bin/pip",
    "version": "pip 24.0 from /usr/lib/python3/dist-packages/pip (python 3.12)"
  },
  "python3": {
    "path": "/usr/bin/python3",
    "version": "Python 3.12.3"
  },
  "sudo_nopasswd": true
}
Use the probe's discovered paths and versions. Accept either a complete CUDA toolkit root containing bin/nvcc, include/cuda_runtime.h and lib64/libcudart.so, or the distro layout with /usr/bin/nvcc, /usr/include/cuda_runtime.h and libcudart.so under /usr/lib/x86_64-linux-gnu. Have the scripts check all three selected paths with ls on the box. Prefer a complete toolkit root when both layouts exist; otherwise accept the complete distro layout without requiring /usr/lib64/libcudart.so. Use the same selected compiler, include and library paths in every script, including repairs. For a complete root, pass it explicitly via CUDAToolkit_ROOT or -DCMAKE_CUDA_COMPILER=<root>/bin/nvcc and prepend <root>/bin to PATH. For the distro layout, use /usr/bin/nvcc with its distro include and library paths explicitly; do not treat /usr as a toolkit root requiring lib64. Never rely on /usr/bin/nvcc when a complete toolkit root exists. Never hard-code a toolkit path the probe did not find, even if the brief suggests one. If a required tool is missing, install it with apt only from sources the probe lists; do not add repositories or assume a package exists. Commented source lines are not enabled repositories. If apt cannot supply it, use pip for cmake only; otherwise fail with a clear message.
Write three self-contained bash scripts, invoked from a shared remote working directory with bash harness/<name>:
- setup.sh: build/install the published baseline at its exact intake pin in the stock image. Use sudo only for apt. Preserve stock torch and published source/configuration. Stage source in baseline-published/ and inputs in data/. Do not silently substitute or tune the baseline. Make setup safe to retry once in this directory.
- run_anchors.sh: run the published anchor protocol at the real representative scale declared in EXECUTION.json. Write out/anchors_measured.json as {anchor_id: measured_number}, one finite number per intake anchor. Never copy published values as measurements.
- run_command.sh: only the exact measured baseline run command and its complete environment at the fixed representative scale. Run the published binary, save its stdout/stderr for run_anchors.sh to parse, and propagate its exit status. Do not measure stages, sample telemetry, install tools, or write profiling outputs. run_anchors.sh invokes this file; the pipeline profiles this same file.
Also provide run_evaluation.sh for the published baseline evaluation interface, or make run_anchors.sh handle non-anchor EVAL_MODE. Evaluation uses fresh working directories with baseline-published/, method/, data/, harness/ and payload/ links and absolute BASELINE_DIR, METHOD_DIR, BASELINE_OUT, METHOD_OUT and EVAL_OUT paths. EVAL_PROTOCOL points to the sealed JSON; EVAL_INPUTS and EVAL_SEEDS contain its JSON input and seed specifications; EVAL_COMPUTE_BUDGET is empty except in curve mode. Modes are equivalence, warmup, performance and curve. Run the published configuration on every sealed input/seed, seeds first then input IDs, and write EVAL_OUT/evaluation.json: {records:[{input_id,seed,metrics:{metric_name:finite_number}}],timing_scope,gpu_count,wall_s,compute_budget}. Use null seed for deterministic protocols; timing_scope must equal the seal; wall_s is required for reported_wall scopes; compute_budget is required for curves. Synchronize every used GPU before returning or stopping reported timers; include launch, transfer and merge overhead. Enforce curve budgets in GPU seconds. Always measure actual outputs; never reuse baseline outputs.
Create output directories, preserve logs, and exit nonzero on failure. Read all intake files for pins, commands, data, scale and protocol. Do not run builds or workloads locally.
Return a short completion acknowledgement; the pipeline reads the scripts itself.