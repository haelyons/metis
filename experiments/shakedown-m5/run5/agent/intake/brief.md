# Public pipeline shakedown: MonteCarloMultiGPU

Repository: https://github.com/NVIDIA/cuda-samples; pin tag `v12.8`, commit `db3eea23946bca2e90a75eca2b5b3e07158a9e11` ([tag resolution](https://api.github.com/repos/NVIDIA/cuda-samples/git/ref/tags/v12.8)).
The sample prices European call options by Monte Carlo and validates against its analytic Black–Scholes implementation ([description][description], [reference][gold]).
Target: Lambda Stack, Ubuntu 22.04, CUDA Toolkit 12.8, driver 570; NVIDIA lists Ubuntu 22.04 support and CUDA 12.8 GA driver >=570.26 ([OS support](https://docs.nvidia.com/cuda/archive/12.8.0/cuda-installation-guide-linux/index.html#system-requirements), [driver table](https://docs.nvidia.com/cuda/archive/12.8.0/cuda-toolkit-release-notes/index.html#cuda-driver)).

Build only this sample; requires a host C/C++ toolchain, CUDA development files including cuRAND, and CMake >=3.20 ([sample CMake][cmake]). Commands below assume `/usr/local/cuda-12.8`; adjust to the installed toolkit location. Optional pip CMake installation uses a published Linux wheel ([package](https://pypi.org/project/cmake/3.31.6/)).
```bash
python3 -m pip install --user cmake==3.31.6  # omit if suitable cmake is installed
export PATH="$HOME/.local/bin:$PATH"
git clone --branch v12.8 --depth 1 https://github.com/NVIDIA/cuda-samples.git
cd cuda-samples
git checkout --detach db3eea23946bca2e90a75eca2b5b3e07158a9e11
sample=Samples/5_Domain_Specific/MonteCarloMultiGPU
cmake -S "$sample" -B build-mc -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.8/bin/nvcc
cmake --build build-mc --target MonteCarloMultiGPU --parallel
CUDA_VISIBLE_DEVICES=0 ./build-mc/MonteCarloMultiGPU --method=streamed --scaling=strong
```
Standalone configuration is supported; this tag's sample CMake hardcodes its architecture list, so no architecture override is assumed ([build instructions][readme], [CMake, L11][cmake]).

Published source configuration: `nOptions = 8 * 1024`, `PATH_N = 262144`, `OPT_N = nOptions * scale`; weak scaling uses `scale=GPU_N`, strong scaling uses 1. GPU count comes from `cudaGetDeviceCount`, not a fixed upstream number ([host, L269–279][host]).
This brief fixes GPU count to **1**, options to **8,192**, paths to **262,144 per option** using the run command above; check the three printed configuration fields ([host, L307–314][host]). The tiny-GPU adjustment can reduce options on devices with <=32 CUDA cores ([host, L62–79][host]).
Other source constants: `THREAD_N=256`, `MAX_OPTIONS=1024*1024` per GPU; grid size is capped at `40 * multiProcessorCount`; default `real` is float, with `DOUBLE_PRECISION` disabled ([kernel, L49, L74][kernel], [host, L81–85][host], [precision][precision]).

Anchors below use `comparison` explicitly: tolerance 0 does not turn a strict lower bound into an equality target. Both are checkable from the final sample output; retain the process exit status too.
```json
[
  {"id":"mc-bs-reserve","quantity":"Average reserve: mean confidence-width / absolute MC-minus-BS error","published_value":1.0,"tolerance":0,"comparison":">"},
  {"id":"sample-pass","quantity":"Final verdict: 1 for Test passed; 0 for Test failed!","published_value":1,"tolerance":0,"comparison":"=="}
]
```
Source line for both anchors: `printf(sumReserve > 1.0f ? "Test passed\n" : "Test failed!\n");` ([host, L485][host]); L486 applies the same predicate to success/failure exit status.
Reserve adds `Confidence / delta` only when absolute error exceeds 1e-6, then divides by the full option count; confidence is the discounted 1.96-standard-error width ([host, L426–442][host], [kernel, L167–179][kernel]). At the six-decimal printed boundary, use the verdict or recompute the unrounded statistic.
Record `L1 norm = sum(abs(BS-MC))/sum(abs(BS))`; upstream publishes neither an expected numeric L1 nor an L1 acceptance threshold here. Do not invent one. The sample's pass criterion is reserve >1 ([host, L426–442, L479–486][host]).

Data: none to download; inputs are generated with `srand(123)`: S in [5,50], X in [10,25], T in [1,5], R=0.06, V=0.10 ([host, L316–327][host]).
GPU RNG uses `curand_init(blockIdx.x + gridDim.x * device_id, threadIdx.x, 0, ...)`; there is no seed CLI. Record GPU model/count, grid size, toolkit and libc: GPU geometry changes random streams, and host inputs use libc `rand()` ([kernel, L131–138][kernel], [host, L57–59, L81–85][host]).

Timing: report the streamed `Total time (ms.)`. Its host timer spans option preprocessing, H2D input transfer, GPU pricing and D2H result transfer, waiting on completion events. Allocation/RNG initialization precedes this interval; CPU result finalization and Black–Scholes validation follow it. Exclude compilation ([host, L147–194][host], [kernel, L190–223][kernel]).
Scale: first time the published 8,192-option case above. If <10 s, change host `nOptions` to `1024 * 1024`, rebuild with the same command, and run the same arguments: **1,048,576 options, 262,144 paths, 1 GPU**. This is a proposed timing case, not an upstream published measurement; it reaches the kernel's per-GPU option limit ([host, L272–279][host], [kernel, L49, L193–195][kernel]).
If still <10 s, double host `PATH_N`, rebuild and repeat until the measured interval is >=10,000 ms; publish the final constants and recheck both anchors. No >=10 s runtime is verified. Upstream cautions that these samples are not intended for performance measurements and GPU Boost affects results ([host, L279, L482–484][host]).

Licence: NVIDIA cuda-samples licence, a BSD-3-Clause-style grant: local running and modification are permitted; redistribution must preserve notices/disclaimer, and NVIDIA/contributor names cannot endorse derived products without permission. The licence also links the CUDA EULA ([licence, L1–28][licence]).
Unverified: actual build/run on the Lambda image, exact driver patch/GPU, numeric L1/reserve outputs, and time to reach 10 s. This authoring environment has no `nvcc` or `cmake`; compatibility is source/documentation-checked, not execution-tested. Pinned top-level prerequisites say CUDA 12.8, while its introductory sentence says 12.6 and the sample README says 12.5 ([README][readme], [sample README][description]).

[readme]: https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/README.md#building-cuda-samples
[description]: https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/README.md
[cmake]: https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/CMakeLists.txt
[host]: https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp
[kernel]: https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarlo_kernel.cu
[gold]: https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarlo_gold.cpp#L43-L81
[precision]: https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/Samples/5_Domain_Specific/MonteCarloMultiGPU/realtype.h#L31-L37
[licence]: https://github.com/NVIDIA/cuda-samples/blob/db3eea23946bca2e90a75eca2b5b3e07158a9e11/LICENSE
