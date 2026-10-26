#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/setup data
log="out/setup/setup-$(date +%s%N).log"
exec > >(tee "$log") 2>&1
trap 'echo "setup failed at line $LINENO" >&2' ERR
for tool in /usr/bin/git /usr/bin/cmake /usr/bin/g++ /usr/bin/gcc /usr/bin/make /usr/bin/python3 /usr/bin/nvcc; do
  [[ -x "$tool" ]] || { echo "Required probed tool missing: $tool; enabled NVIDIA apt source cannot supply host build tools" >&2; exit 1; }
done
/usr/bin/python3 - <<'PY'
import subprocess
v=subprocess.check_output(['/usr/bin/cmake','--version'],text=True).split()[2]
if tuple(map(int,v.split('.')[:2])) < (3,20):
    raise SystemExit('CMake >=3.20 required; probed /usr/bin/cmake was 3.22.1')
PY
pin=db3eea23946bca2e90a75eca2b5b3e07158a9e11
if [[ ! -e baseline-published ]]; then
  /usr/bin/git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git baseline-published
fi
[[ -d baseline-published/.git ]] || { echo 'baseline-published is not a Git checkout' >&2; exit 1; }
[[ "$(/usr/bin/git -C baseline-published rev-parse HEAD)" == "$pin" ]] || { echo 'Unexpected checkout pin' >&2; exit 1; }
/usr/bin/git -C baseline-published checkout --detach "$pin"
# Restore only the two host constants changed by the declared adaptive protocol.
/usr/bin/git -C baseline-published restore --source="$pin" -- Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp
rm -f out/representative.json out/anchors_measured.json
cat > data/EXECUTION.json <<'INTAKE_JSON'
{
  "representative_scale": {
    "initial": {
      "options": 8192,
      "paths_per_option": 262144,
      "gpus": 1,
      "method": "streamed",
      "scaling": "strong"
    },
    "timing_target_ms": 10000,
    "adaptive_protocol": [
      {
        "condition": "Initial measured interval <10000 ms",
        "change": "Change host nOptions to 1024 * 1024, rebuild with same command, rerun same arguments.",
        "options": 1048576,
        "paths_per_option": 262144,
        "gpus": 1
      },
      {
        "condition": "Expanded case still <10000 ms",
        "change": "Double host PATH_N, rebuild and repeat until measured interval >=10000 ms; publish final constants and recheck both anchors."
      }
    ],
    "status": "Initial workload source-published; expanded timing cases proposed in brief, no runtime verified.",
    "final_options": null,
    "final_paths_per_option": null,
    "reason": "Final representative timing case requires future measurement; no workloads run.",
    "sources": [
      "brief.md",
      "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp",
      "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarlo_kernel.cu"
    ]
  },
  "inputs": {
    "data_file": "data.json",
    "configuration_file": "baseline.json",
    "external_dataset": null,
    "generation": "Host srand(123) and sample cuRAND initialization.",
    "precision": "float"
  },
  "outputs": {
    "configuration_fields": [
      "Option count",
      "Path count",
      "GPU count"
    ],
    "metrics": [
      "Total time (ms.)",
      "L1 norm",
      "Average reserve"
    ],
    "verdict": [
      "Test passed",
      "Test failed!"
    ],
    "process_exit_status": "Retain exit status.",
    "scoring_interface": {
      "anchor_file": "anchors.json",
      "mc-bs-reserve": "Compare unrounded average reserve > 1.0; printed boundary requires verdict or recomputation.",
      "sample-pass": "Map Test passed to 1, Test failed! to 0; compare == 1.",
      "acceptance": "Both anchors satisfied and successful process exit.",
      "L1": "Record only; no published numeric criterion."
    }
  },
  "timing_scope": {
    "reported_field": "Streamed Total time (ms.)",
    "includes": [
      "Option preprocessing",
      "H2D input transfer",
      "GPU pricing",
      "D2H result transfer",
      "Waiting on completion events"
    ],
    "excludes": [
      "Compilation",
      "Allocation",
      "RNG initialization",
      "CPU result finalization",
      "Black\u2013Scholes validation"
    ],
    "sources": [
      "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp#L147-L194",
      "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarlo_kernel.cu#L190-L223"
    ]
  }
}

INTAKE_JSON
cat > data/anchors.json <<'INTAKE_JSON'
[
  {
    "id": "mc-bs-reserve",
    "quantity": "Average reserve: mean confidence-width / absolute MC-minus-BS error",
    "published_value": 1.0,
    "tolerance": 0,
    "comparison": ">",
    "source": {
      "citation": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp#L426-L486",
      "evidence": "NVIDIA source accepts sumReserve > 1.0f. Adds Confidence / delta only for delta > 1e-6, then divides by full option count.",
      "independence": "Published by NVIDIA, independent of this intake; acceptance threshold, not measured performance."
    }
  },
  {
    "id": "sample-pass",
    "quantity": "Final verdict: 1 for Test passed; 0 for Test failed!",
    "published_value": 1,
    "tolerance": 0,
    "comparison": "==",
    "source": {
      "citation": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp#L485-L486",
      "evidence": "NVIDIA source prints Test passed and exits successfully when sumReserve > 1.0f.",
      "independence": "Published by NVIDIA, independent of this intake; same acceptance predicate as mc-bs-reserve, not a separate measurement."
    }
  }
]

INTAKE_JSON
cat > data/baseline.json <<'INTAKE_JSON'
{
  "repo": "https://github.com/NVIDIA/cuda-samples",
  "tag": "v12.8",
  "commit": "db3eea23946bca2e90a75eca2b5b3e07158a9e11",
  "pin_source": "https://api.github.com/repos/NVIDIA/cuda-samples/git/ref/tags/v12.8",
  "optional_prerequisite_commands": [
    "python3 -m pip install --user cmake==3.31.6",
    "export PATH=\"$HOME/.local/bin:$PATH\""
  ],
  "optional_prerequisite_source": "https://pypi.org/project/cmake/3.31.6/",
  "build_commands": [
    "git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git",
    "cd cuda-samples",
    "git checkout --detach db3eea23946bca2e90a75eca2b5b3e07158a9e11",
    "sample=Samples/5_Domain_Specific/MonteCarloMultiGPU",
    "cmake -S \"$sample\" -B build-mc -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.8/bin/nvcc",
    "cmake --build build-mc --target MonteCarloMultiGPU --parallel"
  ],
  "run_commands": [
    "CUDA_VISIBLE_DEVICES=0 ./build-mc/MonteCarloMultiGPU --method=streamed --scaling=strong"
  ],
  "commands_source": "brief.md, build/run code block",
  "build_sources": [
    "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/CMakeLists.txt",
    "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/README.md#building-cuda-samples"
  ],
  "published_configuration": {
    "nOptions": 8192,
    "PATH_N": 262144,
    "OPT_N": "nOptions * scale",
    "strong_scale": 1,
    "weak_scale": "GPU_N",
    "GPU_N": "cudaGetDeviceCount; brief selects 1 with CUDA_VISIBLE_DEVICES=0",
    "THREAD_N": 256,
    "MAX_OPTIONS_per_GPU": 1048576,
    "grid_cap": "40 * multiProcessorCount",
    "real": "float",
    "DOUBLE_PRECISION": false,
    "caveat": "Devices with <=32 CUDA cores may reduce options; verify printed configuration.",
    "sources": [
      "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp",
      "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarlo_kernel.cu",
      "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/realtype.h#L31-L37"
    ]
  },
  "executed": false,
  "unavailable_evidence": {
    "build_log": null,
    "run_log": null,
    "reason": "Intake forbids builds and workloads."
  }
}

INTAKE_JSON
cat > data/benchmark.json <<'INTAKE_JSON'
{
  "identity": {
    "name": "MonteCarloMultiGPU",
    "publisher": "NVIDIA",
    "repository": "https://github.com/NVIDIA/cuda-samples",
    "tag": "v12.8",
    "commit": "db3eea23946bca2e90a75eca2b5b3e07158a9e11",
    "brief": "brief.md",
    "found": true
  },
  "outcome_definition": {
    "task": "Price European call options with GPU Monte Carlo; validate against analytic Black\u2013Scholes.",
    "acceptance": "Unrounded average reserve > 1.0; final Test passed verdict and successful process exit.",
    "reserve": "Sum Confidence / abs(MC-BS) for errors > 1e-6, divided by all options. Confidence is discounted 1.96-standard-error width.",
    "additional_metric": "L1 norm = sum(abs(BS-MC)) / sum(abs(BS))",
    "published_L1_value": null,
    "published_L1_tolerance": null,
    "L1_reason": "No numeric L1 expectation or acceptance threshold published in supplied brief/source references.",
    "performance_metric": "Streamed Total time (ms.)",
    "published_performance_value": null,
    "performance_reason": "No published timing measurement supplied."
  },
  "citations": {
    "host": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp",
    "kernel": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarlo_kernel.cu",
    "analytic_reference": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarlo_gold.cpp#L43-L81",
    "precision": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/realtype.h#L31-L37",
    "cmake": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/CMakeLists.txt",
    "sample_description": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/README.md",
    "readme": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/README.md#building-cuda-samples",
    "licence": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/LICENSE",
    "os_support": "https://docs.nvidia.com/cuda/archive/12.8.0/cuda-installation-guide-linux/index.html#system-requirements",
    "driver_requirements": "https://docs.nvidia.com/cuda/archive/12.8.0/cuda-toolkit-release-notes/index.html#cuda-driver",
    "tag_resolution": "https://api.github.com/repos/NVIDIA/cuda-samples/git/ref/tags/v12.8",
    "cmake_wheel": "https://pypi.org/project/cmake/3.31.6/"
  },
  "source_licences_and_intended_use_permissions": {
    "status": "permitted",
    "intended_use": "Local running and modification for benchmark intake/reproduction.",
    "sample_licence": "NVIDIA cuda-samples BSD-3-Clause-style grant",
    "source": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/LICENSE",
    "conditions": [
      "Preserve notices, conditions and disclaimer when redistributing.",
      "No NVIDIA or contributor endorsement without permission."
    ],
    "cuda_eula": "https://docs.nvidia.com/cuda/eula/index.html",
    "cuda_eula_review": null,
    "cuda_eula_reason": "Licence links CUDA EULA; independent review of installed toolkit terms not supplied.",
    "data_licence": "No external dataset; inputs generated by sample."
  },
  "stock_cuda_image_feasibility": {
    "stock_environment": null,
    "status": "unknown pending reproduction",
    "target": "Lambda Stack, Ubuntu 22.04, CUDA Toolkit 12.8, driver 570",
    "requirements": [
      "Host C/C++ toolchain",
      "CUDA development files including cuRAND",
      "CMake >=3.20",
      "Supported NVIDIA GPU and compatible driver"
    ],
    "documented_evidence": [
      "Brief cites Ubuntu 22.04 support and CUDA 12.8 GA driver >=570.26.",
      "Sample supports standalone CMake configuration and hardcodes architecture list."
    ],
    "sources": [
      "https://docs.nvidia.com/cuda/archive/12.8.0/cuda-installation-guide-linux/index.html#system-requirements",
      "https://docs.nvidia.com/cuda/archive/12.8.0/cuda-toolkit-release-notes/index.html#cuda-driver",
      "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/CMakeLists.txt",
      "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/README.md#building-cuda-samples"
    ],
    "reason": "Actual stock image contents, exact driver patch/GPU, build and execution not verified. Brief reports source/documentation checks only.",
    "documentation_discrepancies": "Top-level prerequisites say CUDA 12.8, introductory sentence 12.6, sample README 12.5."
  },
  "memory": {
    "data_GiB": null,
    "peak_working_set_GiB": null,
    "total_GiB": null,
    "size": "unknown",
    "external_dataset_bytes": 0,
    "reason": "No download required, but generated buffers, device allocations and peak working set not quantified; path count alone does not establish memory use."
  },
  "scoring_and_repeatability": {
    "anchors_count": 2,
    "anchors_file": "anchors.json",
    "rounding_rule": "At six-decimal reserve boundary use verdict or recompute unrounded statistic.",
    "retain": [
      "Configuration fields",
      "L1 norm",
      "Average reserve",
      "Final verdict",
      "Process exit status",
      "Streamed Total time (ms.)"
    ],
    "record_environment": [
      "GPU model/count",
      "Grid size",
      "CUDA toolkit",
      "Driver patch",
      "libc"
    ],
    "host_seed": 123,
    "gpu_rng": "curand_init(blockIdx.x + gridDim.x * device_id, threadIdx.x, 0, ...)",
    "seed_cli": null,
    "caveats": [
      "GPU geometry changes random streams.",
      "Host inputs depend on libc rand().",
      "Upstream warns samples are not intended for performance measurements and GPU Boost affects results."
    ],
    "repetition_count": null,
    "repetition_reason": "No repeated-run count or aggregation rule supplied."
  },
  "evidence_status": {
    "primary_basis": "Readable supplied brief and its citations.",
    "independent_fetch": "NVIDIA LICENSE retrieved and verified; source fetches failed (web cache misses; shell network domain blocked).",
    "builds_or_workloads_run": false,
    "gate_scripts": [],
    "gate_scripts_reason": "No gate scripts named in task or brief."
  },
  "search_candidates": [],
  "search_reason": "No benchmark search; extracted only named benchmark."
}

INTAKE_JSON
cat > data/data.json <<'INTAKE_JSON'
{
  "status": "available",
  "required_inputs": [
    {
      "name": "European call option parameters",
      "kind": "generated",
      "availability": "available",
      "access_instructions": "Sample generates inputs locally with srand(123), no download.",
      "configuration": {
        "options": 8192,
        "S_range": [
          5,
          50
        ],
        "X_range": [
          10,
          25
        ],
        "T_range": [
          1,
          5
        ],
        "R": 0.06,
        "V": 0.1
      },
      "source": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp#L316-L327",
      "licence": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/LICENSE"
    },
    {
      "name": "GPU Monte Carlo random streams",
      "kind": "generated",
      "availability": "available",
      "access_instructions": "Sample initializes cuRAND states; no seed CLI.",
      "initialization": "curand_init(blockIdx.x + gridDim.x * device_id, threadIdx.x, 0, ...)",
      "source": "https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarlo_kernel.cu#L131-L138",
      "licence": "CUDA toolkit/cuRAND terms apply; sample code licence linked in benchmark.json."
    }
  ],
  "external_data_required": false,
  "missing_required_data": [],
  "pins": {
    "generator_repository": "https://github.com/NVIDIA/cuda-samples",
    "generator_commit": "db3eea23946bca2e90a75eca2b5b3e07158a9e11"
  },
  "input_hashes": null,
  "hash_reason": "Generated inputs have no supplied fixed file hashes; libc and GPU geometry affect generated sequences.",
  "splits": null,
  "splits_reason": "Pricing benchmark has no training/validation/test dataset split.",
  "seeds": {
    "host_srand": 123,
    "device_seed_expression": "blockIdx.x + gridDim.x * device_id",
    "device_sequence_expression": "threadIdx.x",
    "device_offset": 0
  },
  "generated_buffer_GiB": null,
  "size_reason": "Generated input allocation sizes and peak working set not supplied."
}

INTAKE_JSON
/usr/bin/cmake -S baseline-published/Samples/5_Domain_Specific/MonteCarloMultiGPU -B baseline-published/build-mc -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/bin/nvcc
/usr/bin/cmake --build baseline-published/build-mc --target MonteCarloMultiGPU --parallel
/usr/bin/nvcc --version
/usr/bin/ldd --version
if command -v nvidia-smi >/dev/null; then nvidia-smi; fi
printf '%s\n' 'Published baseline ready; inputs generated internally with srand(123) and cuRAND.'
