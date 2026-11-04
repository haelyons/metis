setup.sh failed (rc 2). Repair only "/tmp/m5-harness-repair-XQnQpI/harness/setup.sh" using intake evidence. The intake files are under "/tmp/m5-harness-repair-XQnQpI/intake" and the compared arms and inputs are listed in "/tmp/m5-harness-repair-XQnQpI/comparison_view.json". Preserve the published pin, configuration and stock image; sudo only for apt. Scope: setup.sh builds and checks only the baseline. The pipeline owns profiling and profiler installation; do not write profile.sh or install profiling tools. A setup repair may change only setup.sh; an anchors repair may change run_anchors.sh, run_command.sh, or both, and nothing else. Stay within each script's scope. Run the published build and binary and read measurements from its OUTPUT. run_command.sh contains only the exact measured baseline command and complete environment at the representative scale. run_command.sh is the canonical measured command and complete environment, including working directory, arguments, CUDA_VISIBLE_DEVICES and GPU count. run_command.sh must use paths relative to its working directory, never absolute paths into the run directory, and write only under out/ or temporary files. Concurrency and evaluation run it from sibling work directories linking the same trees. The pipeline owns CUDA MPS. No harness script (setup.sh, run_anchors.sh, run_command.sh, run_evaluation.sh) may set, unset or override any CUDA_MPS_* environment variable, or start or stop an MPS daemon; inherit these variables unchanged. run_anchors.sh must invoke bash harness/run_command.sh without overriding its environment or duplicating the workload command; parse its saved output for every intake item ID, anchors and references. With an empty anchors.json, still run the published command and write out/anchors_measured.json as {}. The fixed profiler invokes that identical file with bash from the same working directory. Keep output paths stable and preserve logs. Every later run script must preserve the published configuration. Validate printed configuration against the actual command and environment. Preserve consistency in repairs; read the other harness scripts while editing only the permitted scripts. Never parse or assert on source text. Measurement checks must fail only on missing or invalid output; the pipeline scores measured values against anchors. Never read experiments/, operator/, or control/. Do not run workloads locally or access the box. This is repair attempt 1 of 4 for this script.
Budget: 19274s resolved now, the time left before the run ceiling, not a target (explicit args budget overrides); failed attempt budget: 19350s; measured elapsed: 77s; measured overrun: 0s. Script budgets in seconds: setup.sh=19274, run_anchors.sh=19274, fixed profiler=19274 (resolved now: time left before the run ceiling, not a target; explicit args budgets override); run_evaluation.sh=1200 per invocation (also run_anchors.sh when used as the evaluation adapter); complete evaluation scorer=2400. Use one fixed scale from EXECUTION.json, no scale search or doubling loops, and finish well within the budget.
Box probe (collected by the pipeline before harness generation):
{
  "apt_enabled_sources": [
    {
      "entries": [
        "deb http://archive.ubuntu.com/ubuntu jammy main restricted",
        "deb http://archive.ubuntu.com/ubuntu jammy-updates main restricted",
        "deb http://archive.ubuntu.com/ubuntu jammy universe",
        "deb http://archive.ubuntu.com/ubuntu jammy-updates universe",
        "deb http://archive.ubuntu.com/ubuntu jammy multiverse",
        "deb http://archive.ubuntu.com/ubuntu jammy-updates multiverse",
        "deb http://archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse",
        "deb http://security.ubuntu.com/ubuntu jammy-security main restricted",
        "deb http://security.ubuntu.com/ubuntu jammy-security universe",
        "deb http://security.ubuntu.com/ubuntu jammy-security multiverse"
      ],
      "file": "/etc/apt/sources.list"
    },
    {
      "entries": [
        "deb [arch=amd64 signed-by=/etc/apt/cloud-init.gpg.d/azure-cli.gpg] https://packages.microsoft.com/repos/azure-cli/ jammy main"
      ],
      "file": "/etc/apt/sources.list.d/azure-cli.list"
    },
    {
      "entries": [
        "deb [signed-by=/etc/apt/cloud-init.gpg.d/cloudflare.gpg] https://pkg.cloudflare.com/cloudflared jammy main"
      ],
      "file": "/etc/apt/sources.list.d/cloudflare.list"
    },
    {
      "entries": [
        "deb [signed-by=/etc/apt/cloud-init.gpg.d/deadsnakes.gpg] http://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy main"
      ],
      "file": "/etc/apt/sources.list.d/deadsnakes.list"
    },
    {
      "entries": [
        "deb [signed-by=/etc/apt/trusted.gpg.d/mellanox.gpg] http://linux.mellanox.com/public/repo/doca/2.9.2/ubuntu22.04/x86_64 ./"
      ],
      "file": "/etc/apt/sources.list.d/doca.list"
    },
    {
      "entries": [
        "deb [arch=amd64 signed-by=/etc/apt/cloud-init.gpg.d/docker.gpg] https://download.docker.com/linux/ubuntu jammy stable"
      ],
      "file": "/etc/apt/sources.list.d/docker.list"
    },
    {
      "entries": [
        "deb http://archive.lambdalabs.com/ubuntu jammy main"
      ],
      "file": "/etc/apt/sources.list.d/lambda-repository.list"
    },
    {
      "entries": [
        "deb [signed-by=/etc/apt/cloud-init.gpg.d/nvidia-docker-container.gpg] https://nvidia.github.io/libnvidia-container/stable/deb/amd64 /"
      ],
      "file": "/etc/apt/sources.list.d/nvidia-docker-container.list"
    },
    {
      "entries": [
        "deb [signed-by=/etc/apt/cloud-init.gpg.d/nvtop.gpg] https://ppa.launchpadcontent.net/flexiondotorg/nvtop/ubuntu jammy main"
      ],
      "file": "/etc/apt/sources.list.d/nvtop.list"
    }
  ],
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
  "disk_home_avail_bytes": 1038806618112,
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
  "memory_kb": 231924784,
  "nproc": 26,
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
      "NVIDIA H100 PCIe"
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
Use the probe's discovered paths and versions. Accept either a complete CUDA toolkit root containing bin/nvcc, include/cuda_runtime.h and lib64/libcudart.so, or the distro layout with /usr/bin/nvcc, /usr/include/cuda_runtime.h and libcudart.so under /usr/lib/x86_64-linux-gnu. Have the scripts check all three selected paths with ls on the box. Prefer a complete toolkit root when both layouts exist; otherwise accept the complete distro layout without requiring /usr/lib64/libcudart.so. Use the same selected compiler, include and library paths in every script, including repairs. For a complete root, pass it explicitly via CUDAToolkit_ROOT or -DCMAKE_CUDA_COMPILER=<root>/bin/nvcc and prepend <root>/bin to PATH. For the distro layout, use /usr/bin/nvcc with its distro include and library paths explicitly; do not treat /usr as a toolkit root requiring lib64. Never rely on /usr/bin/nvcc when a complete toolkit root exists. Never hard-code a toolkit path the probe did not find, even if the brief suggests one. A tool or system library the published baseline needs but the stock image lacks may be installed with sudo apt-get install -y from any source the probe reports in apt_enabled_sources (after sudo apt-get update), once apt-cache policy <package> shows an install candidate. Never add repositories, keys or source lines, and never enable a commented or disabled source. Setup prints each package it installs and its installed version (dpkg-query -W <package>). Otherwise only cmake may fall back to pip. If neither route applies, scripts must fail with a clear message.
Log tail (at most 200 lines):
The following NEW packages will be installed:
  libfftw3-bin libfftw3-dev libfftw3-double3 libfftw3-long3 libfftw3-quad3
  libfftw3-single3
0 upgraded, 6 newly installed, 0 to remove and 329 not upgraded.
Need to get 4654 kB of archives.
After this operation, 24.7 MB of additional disk space will be used.
Get:1 http://archive.ubuntu.com/ubuntu jammy/main amd64 libfftw3-double3 amd64 3.3.8-2ubuntu8 [770 kB]
Get:2 http://archive.ubuntu.com/ubuntu jammy/main amd64 libfftw3-long3 amd64 3.3.8-2ubuntu8 [335 kB]
Get:3 http://archive.ubuntu.com/ubuntu jammy/main amd64 libfftw3-quad3 amd64 3.3.8-2ubuntu8 [614 kB]
Get:4 http://archive.ubuntu.com/ubuntu jammy/main amd64 libfftw3-single3 amd64 3.3.8-2ubuntu8 [800 kB]
Get:5 http://archive.ubuntu.com/ubuntu jammy/main amd64 libfftw3-bin amd64 3.3.8-2ubuntu8 [35.5 kB]
Get:6 http://archive.ubuntu.com/ubuntu jammy/main amd64 libfftw3-dev amd64 3.3.8-2ubuntu8 [2101 kB]
debconf: unable to initialize frontend: Dialog
debconf: (Dialog frontend will not work on a dumb terminal, an emacs shell buffer, or without a controlling terminal.)
debconf: falling back to frontend: Readline
debconf: unable to initialize frontend: Readline
debconf: (This frontend requires a controlling tty.)
debconf: falling back to frontend: Teletype
dpkg-preconfigure: unable to re-open stdin: 
Fetched 4654 kB in 4s (1327 kB/s)
Selecting previously unselected package libfftw3-double3:amd64.
(Reading database ... (Reading database ... 5%(Reading database ... 10%(Reading database ... 15%(Reading database ... 20%(Reading database ... 25%(Reading database ... 30%(Reading database ... 35%(Reading database ... 40%(Reading database ... 45%(Reading database ... 50%(Reading database ... 55%(Reading database ... 60%(Reading database ... 65%(Reading database ... 70%(Reading database ... 75%(Reading database ... 80%(Reading database ... 85%(Reading database ... 90%(Reading database ... 95%(Reading database ... 100%(Reading database ... 214077 files and directories currently installed.)
Preparing to unpack .../0-libfftw3-double3_3.3.8-2ubuntu8_amd64.deb ...
Unpacking libfftw3-double3:amd64 (3.3.8-2ubuntu8) ...
Selecting previously unselected package libfftw3-long3:amd64.
Preparing to unpack .../1-libfftw3-long3_3.3.8-2ubuntu8_amd64.deb ...
Unpacking libfftw3-long3:amd64 (3.3.8-2ubuntu8) ...
Selecting previously unselected package libfftw3-quad3:amd64.
Preparing to unpack .../2-libfftw3-quad3_3.3.8-2ubuntu8_amd64.deb ...
Unpacking libfftw3-quad3:amd64 (3.3.8-2ubuntu8) ...
Selecting previously unselected package libfftw3-single3:amd64.
Preparing to unpack .../3-libfftw3-single3_3.3.8-2ubuntu8_amd64.deb ...
Unpacking libfftw3-single3:amd64 (3.3.8-2ubuntu8) ...
Selecting previously unselected package libfftw3-bin.
Preparing to unpack .../4-libfftw3-bin_3.3.8-2ubuntu8_amd64.deb ...
Unpacking libfftw3-bin (3.3.8-2ubuntu8) ...
Selecting previously unselected package libfftw3-dev:amd64.
Preparing to unpack .../5-libfftw3-dev_3.3.8-2ubuntu8_amd64.deb ...
Unpacking libfftw3-dev:amd64 (3.3.8-2ubuntu8) ...
Setting up libfftw3-single3:amd64 (3.3.8-2ubuntu8) ...
Setting up libfftw3-long3:amd64 (3.3.8-2ubuntu8) ...
Setting up libfftw3-quad3:amd64 (3.3.8-2ubuntu8) ...
Setting up libfftw3-double3:amd64 (3.3.8-2ubuntu8) ...
Setting up libfftw3-bin (3.3.8-2ubuntu8) ...
Setting up libfftw3-dev:amd64 (3.3.8-2ubuntu8) ...
Processing triggers for man-db (2.10.2-1) ...
Processing triggers for libc-bin (2.35-0ubuntu3.10) ...

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
libfftw3-dev:amd64	3.3.8-2ubuntu8
-rwxr-xr-x 1 root root    59 Mar 19  2025 /usr/bin/nvcc
-rw-r--r-- 1 root root 98574 Mar 20  2025 /usr/include/cuda_runtime.h
lrwxrwxrwx 1 root root    15 Mar 20  2025 /usr/lib/x86_64-linux-gnu/libcudart.so -> libcudart.so.12
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2025 NVIDIA Corporation
Built on Fri_Feb_21_20:23:50_PST_2025
Cuda compilation tools, release 12.8, V12.8.93
Build cuda_12.8.r12.8/compiler.35583870_0
Cloning into 'baseline-published/megadock'...
HEAD is now at 9575280 upgrade FFTW version
Cloning into 'baseline-published/cuda-samples'...
Note: switching to 'db3eea23946bca2e90a75eca2b5b3e07158a9e11'.

You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by switching back to a branch.

If you want to create a new branch to retain commits you create, you may
do so (now or later) by using -c with the switch command. Example:

  git switch -c <new-branch-name>

Or undo this operation with:

  git switch -

Turn off this advice by setting config variable advice.detachedHead to false

Updating files:  68% (1710/2498)Updating files:  69% (1724/2498)Updating files:  70% (1749/2498)Updating files:  71% (1774/2498)Updating files:  72% (1799/2498)Updating files:  73% (1824/2498)Updating files:  74% (1849/2498)Updating files:  75% (1874/2498)Updating files:  76% (1899/2498)Updating files:  77% (1924/2498)Updating files:  78% (1949/2498)Updating files:  79% (1974/2498)Updating files:  80% (1999/2498)Updating files:  81% (2024/2498)Updating files:  82% (2049/2498)Updating files:  83% (2074/2498)Updating files:  84% (2099/2498)Updating files:  85% (2124/2498)Updating files:  86% (2149/2498)Updating files:  87% (2174/2498)Updating files:  88% (2199/2498)Updating files:  89% (2224/2498)Updating files:  90% (2249/2498)Updating files:  91% (2274/2498)Updating files:  92% (2299/2498)Updating files:  93% (2324/2498)Updating files:  94% (2349/2498)Updating files:  95% (2374/2498)Updating files:  96% (2399/2498)Updating files:  97% (2424/2498)Updating files:  98% (2449/2498)Updating files:  99% (2474/2498)Updating files:  99% (2491/2498)Updating files: 100% (2498/2498)Updating files: 100% (2498/2498), done.
make: Entering directory '/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/megadock'
mkdir -p obj_cs
/usr/bin/g++ -fopenmp -static  -O3 -Isrc -I/usr/include -o obj_cs/control.cpp.o -c src/control.cpp
/usr/bin/g++ -fopenmp -static  -O3 -Isrc -I/usr/include -o obj_cs/cpu_time.cpp.o -c src/cpu_time.cpp
--------------------------
/usr/bin/g++ -fopenmp -static  -O3 -Isrc -I/usr/include -o obj_cs/docking.cpp.o -c src/docking.cpp
/usr/bin/g++ -fopenmp -static  -O3 -Isrc -I/usr/include -o obj_cs/parameter.cpp.o -c src/parameter.cpp
/usr/bin/g++ -fopenmp -static  -O3 -Isrc -I/usr/include -o obj_cs/pdb_entry.cpp.o -c src/pdb_entry.cpp
/usr/bin/g++ -fopenmp -static  -O3 -Isrc -I/usr/include -o obj_cs/protein.cpp.o -c src/protein.cpp
make megadock start
/usr/bin/g++ -fopenmp -static  -O3 -Isrc -I/usr/include -o obj_cs/receptor.cpp.o -c src/receptor.cpp
--------------------------
/usr/bin/g++ -fopenmp -static  -O3 -Isrc -I/usr/include -o obj_cs/ligand.cpp.o -c src/ligand.cpp
/usr/bin/g++ -fopenmp -static  -O3 -Isrc -I/usr/include -o obj_cs/fft_process.cpp.o -c src/fft_process.cpp
src/control.cpp: In member function ‘virtual void Control::initialize(int, char**)’:
src/control.cpp:43:23: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘size_t’ {aka ‘long unsigned int’} [-Wformat=]
   43 |     printf("# Using %3d CPU cores, %d GPUs\n", _parallel->nproc2(), _parallel->num_gpu());
      |                     ~~^                        ~~~~~~~~~~~~~~~~~~~
      |                       |                                         |
      |                       int                                       size_t {aka long unsigned int}
      |                     %3ld
src/docking.cpp: In member function ‘virtual void Docking::output_detail()’:
src/docking.cpp:557:12: warning: format not a string literal and no format arguments [-Wformat-security]
  557 |     sprintf(buff,column_list.c_str());
      |     ~~~~~~~^~~~~~~~~~~~~~~~~~~~~~~~~~
src/docking.cpp:706:12: warning: format not a string literal and no format arguments [-Wformat-security]
  706 |     sprintf(buff,column_list.c_str());
      |     ~~~~~~~^~~~~~~~~~~~~~~~~~~~~~~~~~
src/docking.cpp: In member function ‘virtual void Docking::output_calc_time_log()’:
src/docking.cpp:970:27: warning: format ‘%d’ expects argument of type ‘int’, but argument 4 has type ‘size_t’ {aka ‘long unsigned int’} [-Wformat=]
  970 |         sprintf(buff,"%s,%d,%d,%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f"
      |                          ~^
      |                           |
      |                           int
      |                          %ld
  971 |                 , calc_id.c_str()
  972 |                 , _parallel->nproc2(), _parallel->num_gpu()
      |                   ~~~~~~~~~~~~~~~~~~~
      |                                    |
      |                                    size_t {aka long unsigned int}
/usr/bin/g++ -fopenmp -static  -O3 -Isrc -I/usr/include -o obj_cs/main.cpp.o -c src/main.cpp
/usr/bin/g++ src/decoygen.cpp -lm -o decoygen
/usr/bin/g++ src/calcrg.cpp -o calcrg
/usr/bin/g++ -fPIC -fopenmp -o ./megadock obj_cs/control.cpp.o obj_cs/cpu_time.cpp.o obj_cs/docking.cpp.o obj_cs/parameter.cpp.o obj_cs/pdb_entry.cpp.o obj_cs/protein.cpp.o obj_cs/receptor.cpp.o obj_cs/ligand.cpp.o obj_cs/fft_process.cpp.o obj_cs/main.cpp.o -lm -L/usr/lib/x86_64-linux-gnu -lfftw3f
make: Leaving directory '/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/megadock'
make: Entering directory '/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/megadock'
mkdir -p obj_gs
--------------------------
/usr/bin/g++ -fopenmp -DCUFFT -static  -O3 -Isrc -I/usr/include -I/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/cuda-samples/Common -I/usr/include -o obj_gs/control.cpp.o -c src/control.cpp
/usr/bin/g++ -fopenmp -DCUFFT -static  -O3 -Isrc -I/usr/include -I/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/cuda-samples/Common -I/usr/include -o obj_gs/cpu_time.cpp.o -c src/cpu_time.cpp
/usr/bin/g++ -fopenmp -DCUFFT -static  -O3 -Isrc -I/usr/include -I/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/cuda-samples/Common -I/usr/include -o obj_gs/docking.cpp.o -c src/docking.cpp
make megadock-gpu start
/usr/bin/g++ -fopenmp -DCUFFT -static  -O3 -Isrc -I/usr/include -I/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/cuda-samples/Common -I/usr/include -o obj_gs/parameter.cpp.o -c src/parameter.cpp
/usr/bin/g++ -fopenmp -DCUFFT -static  -O3 -Isrc -I/usr/include -I/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/cuda-samples/Common -I/usr/include -o obj_gs/pdb_entry.cpp.o -c src/pdb_entry.cpp
/usr/bin/g++ -fopenmp -DCUFFT -static  -O3 -Isrc -I/usr/include -I/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/cuda-samples/Common -I/usr/include -o obj_gs/protein.cpp.o -c src/protein.cpp
--------------------------
/usr/bin/g++ -fopenmp -DCUFFT -static  -O3 -Isrc -I/usr/include -I/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/cuda-samples/Common -I/usr/include -o obj_gs/receptor.cpp.o -c src/receptor.cpp
/usr/bin/g++ -fopenmp -DCUFFT -static  -O3 -Isrc -I/usr/include -I/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/cuda-samples/Common -I/usr/include -o obj_gs/ligand.cpp.o -c src/ligand.cpp
/usr/bin/nvcc -Xcompiler -fopenmp -arch=sm_90 -use_fast_math -DCUFFT --compiler-options -fno-strict-aliasing  -O3 -Isrc -I/usr/include -I/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/cuda-samples/Common -I/usr/include  -o obj_gs/fft_process.cu.o -c src/fft_process.cu
src/control.cpp: In member function ‘virtual void Control::initialize(int, char**)’:
src/control.cpp:43:23: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘size_t’ {aka ‘long unsigned int’} [-Wformat=]
   43 |     printf("# Using %3d CPU cores, %d GPUs\n", _parallel->nproc2(), _parallel->num_gpu());
      |                     ~~^                        ~~~~~~~~~~~~~~~~~~~
      |                       |                                         |
      |                       int                                       size_t {aka long unsigned int}
      |                     %3ld
src/docking.cpp: In member function ‘virtual void Docking::output_detail()’:
src/docking.cpp:557:12: warning: format not a string literal and no format arguments [-Wformat-security]
  557 |     sprintf(buff,column_list.c_str());
      |     ~~~~~~~^~~~~~~~~~~~~~~~~~~~~~~~~~
src/docking.cpp:706:12: warning: format not a string literal and no format arguments [-Wformat-security]
  706 |     sprintf(buff,column_list.c_str());
      |     ~~~~~~~^~~~~~~~~~~~~~~~~~~~~~~~~~
src/docking.cpp: In member function ‘virtual void Docking::output_calc_time_log()’:
src/docking.cpp:970:27: warning: format ‘%d’ expects argument of type ‘int’, but argument 4 has type ‘size_t’ {aka ‘long unsigned int’} [-Wformat=]
  970 |         sprintf(buff,"%s,%d,%d,%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f"
      |                          ~^
      |                           |
      |                           int
      |                          %ld
  971 |                 , calc_id.c_str()
  972 |                 , _parallel->nproc2(), _parallel->num_gpu()
      |                   ~~~~~~~~~~~~~~~~~~~
      |                                    |
      |                                    size_t {aka long unsigned int}
/usr/bin/nvcc -Xcompiler -fopenmp -arch=sm_90 -use_fast_math -DCUFFT --compiler-options -fno-strict-aliasing  -O3 -Isrc -I/usr/include -I/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/cuda-samples/Common -I/usr/include  -o obj_gs/main.cu.o -c src/main.cu
src/fft_process.cu: In member function ‘virtual void FFTProcess::cuda_fft(float*, float*, float*, float*, float*, size_t)’:
src/fft_process.cu:522:8: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘long unsigned int’ [-Wformat=]
  522 |         printf(" nf3:%d, nBlocks_nf3:%d, nThreads:%d , nf3=nBlocks_nf3*nThreads\n",nf3,nBlocks_nf3,nThreads);
      |        ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ~~~
      |                                                                             |
      |                                                                             long unsigned int
src/fft_process.cu:523:17: warning: format ‘%d’ expects argument of type ‘int’, but argument 3 has type ‘long unsigned int’ [-Wformat=]
  523 |         fprintf(stderr, " [ERROR] too large FFT size. nf3:%d, nBlocks_nf3:%d\n", nf3, nBlocks_nf3);
      |                 ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ~~~
      |                                                                          |
      |                                                                          long unsigned int
src/fft_process.cu: In member function ‘virtual void FFTProcess::ligand_voxelization_on_gpu(float*, size_t)’:
src/fft_process.cu:685:8: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘long unsigned int’ [-Wformat=]
  685 |         printf(" nf3:%d, nBlocks_nf3:%d, nThreads:%d , nf3=nBlocks_nf3*nThreads\n",nf3,nBlocks_nf3,nThreads);
      |        ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ~~~
      |                                                                             |
      |                                                                             long unsigned int
src/fft_process.cu:686:17: warning: format ‘%d’ expects argument of type ‘int’, but argument 3 has type ‘long unsigned int’ [-Wformat=]
  686 |         fprintf(stderr, " [ERROR] too large FFT size. nf3:%d, nBlocks_nf3:%d\n", nf3, nBlocks_nf3);
      |                 ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ~~~
      |                                                                          |
      |                                                                          long unsigned int
/usr/bin/g++ -fPIC -fopenmp -o ./megadock-gpu obj_gs/control.cpp.o obj_gs/cpu_time.cpp.o obj_gs/docking.cpp.o obj_gs/parameter.cpp.o obj_gs/pdb_entry.cpp.o obj_gs/protein.cpp.o obj_gs/receptor.cpp.o obj_gs/ligand.cpp.o obj_gs/fft_process.cu.o obj_gs/main.cu.o -lm -L/usr/lib/x86_64-linux-gnu -lfftw3f -L/usr/lib/x86_64-linux-gnu -Wl,-rpath,/usr/lib/x86_64-linux-gnu -lcudart -lcufft
make: Leaving directory '/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/baseline-published/megadock'
ELF file    1: megadock-gpu.1.sm_90.cubin
ELF file    2: megadock-gpu.2.sm_90.cubin
python3: can't open file '/tmp/m5-0c18e078-250b-4ffb-9d85-d2b77b351266/harness/prepare_inputs.py': [Errno 2] No such file or directory