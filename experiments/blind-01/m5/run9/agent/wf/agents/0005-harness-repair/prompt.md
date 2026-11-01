setup.sh failed (rc 1). Repair only "/home/hal/dev/interp/metis/experiments/blind-01/m5/run9/agent/harness/setup.sh" using intake evidence. Preserve the published pin, configuration and stock image; sudo only for apt. Scope: setup.sh builds and checks only the baseline. The pipeline owns profiling and profiler installation; do not write profile.sh or install profiling tools. A setup repair may change only setup.sh; an anchors repair may change run_anchors.sh, run_command.sh, or both, and nothing else. Stay within each script's scope. Run the published build and binary and read measurements from its OUTPUT. run_command.sh contains only the exact measured baseline command and complete environment at the representative scale. run_command.sh is the canonical measured command and complete environment, including working directory, arguments, CUDA_VISIBLE_DEVICES and GPU count. run_command.sh must use paths relative to its working directory, never absolute paths into the run directory, and write only under out/ or temporary files. Concurrency and evaluation run it from sibling work directories linking the same trees. The pipeline owns CUDA MPS. No harness script (setup.sh, run_anchors.sh, run_command.sh, run_evaluation.sh) may set, unset or override any CUDA_MPS_* environment variable, or start or stop an MPS daemon; inherit these variables unchanged. run_anchors.sh must invoke bash harness/run_command.sh without overriding its environment or duplicating the workload command; parse its saved output for every intake item ID, anchors and references. With an empty anchors.json, still run the published command and write out/anchors_measured.json as {}. The fixed profiler invokes that identical file with bash from the same working directory. Keep output paths stable and preserve logs. Every later run script must preserve the published configuration. Validate printed configuration against the actual command and environment. Preserve consistency in repairs; read the other harness scripts while editing only the permitted scripts. Never parse or assert on source text. Measurement checks must fail only on missing or invalid output; the pipeline scores measured values against anchors. Never read experiments/, operator/, or control/. Do not run workloads locally or access the box. This is repair attempt 3 of 4 for this script.
Budget: 40478s resolved now, the time left before the run ceiling, not a target (explicit args budget overrides); failed attempt budget: 40673s; measured elapsed: 195s; measured overrun: 0s. Script budgets in seconds: setup.sh=40478, run_anchors.sh=40478, fixed profiler=40478 (resolved now: time left before the run ceiling, not a target; explicit args budgets override); run_evaluation.sh=14400 per invocation (also run_anchors.sh when used as the evaluation adapter); complete evaluation scorer=2400. Use one fixed scale from EXECUTION.json, no scale search or doubling loops, and finish well within the budget.
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
  "disk_home_avail_bytes": 1038620045312,
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
  "memory_kb": 231924764,
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
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 130.0/130.0 KB 228.3 MB/s eta 0:00:00
Requirement already satisfied: wheel in /usr/lib/python3/dist-packages (0.37.1)
Collecting wheel
  Downloading wheel-0.48.0-py3-none-any.whl (33 kB)
Requirement already satisfied: typing-extensions>=4.1 in /usr/lib/python3/dist-packages (from setuptools_scm>=8) (4.10.0)
Collecting tomli>=1
  Downloading tomli-2.5.0-py3-none-any.whl (14 kB)
Collecting vcs-versioning<3,>=2.5.0.dev0
  Downloading vcs_versioning-2.6.0-py3-none-any.whl (123 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 123.2/123.2 KB 244.6 MB/s eta 0:00:00
Installing collected packages: tomli, setuptools, packaging, wheel, vcs-versioning, setuptools_scm
  Attempting uninstall: setuptools
    Found existing installation: setuptools 59.6.0
    Uninstalling setuptools-59.6.0:
      Successfully uninstalled setuptools-59.6.0
  Attempting uninstall: packaging
    Found existing installation: packaging 21.3
    Not uninstalling packaging at /usr/lib/python3/dist-packages, outside environment /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv
    Can't uninstall 'packaging'. No files were found to uninstall.
  Attempting uninstall: wheel
    Found existing installation: wheel 0.37.1
    Not uninstalling wheel at /usr/lib/python3/dist-packages, outside environment /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv
    Can't uninstall 'wheel'. No files were found to uninstall.
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
pipx 1.0.0 requires argcomplete>=1.9.4, but you have argcomplete 1.8.1 which is incompatible.
Successfully installed packaging-26.3 setuptools-84.2.1 setuptools_scm-10.3.4 tomli-2.5.0 vcs-versioning-2.6.0 wheel-0.48.0
   build tool setuptools 84.2.1 @ /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/setuptools/__init__.py
   build tool setuptools_scm 10.3.4 @ /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/setuptools_scm/__init__.py
   build tool packaging 26.3 @ /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/packaging/__init__.py
   build tool wheel 0.48.0 @ /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/wheel/__init__.py
Processing ./baseline-published/pinder-src
  Preparing metadata (pyproject.toml): started
  Preparing metadata (pyproject.toml): finished with status 'done'
Collecting pyarrow>=12.0
  Downloading pyarrow-25.0.1-cp310-cp310-manylinux_2_28_x86_64.whl (50.1 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 50.1/50.1 MB 106.8 MB/s eta 0:00:00
Collecting torch_geometric
  Downloading torch_geometric-2.8.1-py3-none-any.whl (1.3 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.3/1.3 MB 37.4 MB/s eta 0:00:00
Collecting fastpdb
  Downloading fastpdb-1.3.3-cp310-cp310-manylinux_2_34_x86_64.whl (373 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 373.3/373.3 KB 191.2 MB/s eta 0:00:00
Requirement already satisfied: pandas in /usr/lib/python3/dist-packages (from pinder==0.0.0+gebeb28a2) (1.3.5)
Collecting pydantic>=2.0
  Downloading pydantic-2.14.2-py3-none-any.whl (490 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 490.4/490.4 KB 381.0 MB/s eta 0:00:00
Collecting tabulate
  Downloading tabulate-0.10.0-py3-none-any.whl (39 kB)
Requirement already satisfied: torch in /usr/lib/python3/dist-packages (from pinder==0.0.0+gebeb28a2) (2.7.0)
Collecting nbformat
  Downloading nbformat-5.11.1-py3-none-any.whl (79 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 79.8/79.8 KB 196.8 MB/s eta 0:00:00
Requirement already satisfied: numpy<2 in /usr/lib/python3/dist-packages (from pinder==0.0.0+gebeb28a2) (1.21.5)
Collecting torchtyping
  Downloading torchtyping-0.1.5-py3-none-any.whl (17 kB)
Requirement already satisfied: typing_extensions in /usr/lib/python3/dist-packages (from pinder==0.0.0+gebeb28a2) (4.10.0)
Requirement already satisfied: PyYAML in /usr/lib/python3/dist-packages (from pinder==0.0.0+gebeb28a2) (5.4.1)
Requirement already satisfied: scikit-learn in /usr/lib/python3/dist-packages (from pinder==0.0.0+gebeb28a2) (0.23.2)
Collecting typeguard==2.13.3
  Downloading typeguard-2.13.3-py3-none-any.whl (17 kB)
Collecting tqdm
  Downloading tqdm-4.70.1-py3-none-any.whl (80 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 80.2/80.2 KB 319.6 MB/s eta 0:00:00
Collecting plotly
  Downloading plotly-7.1.0-py3-none-any.whl (9.7 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 9.7/9.7 MB 99.4 MB/s eta 0:00:00
Collecting biotite<1.7,>=1.0
  Downloading biotite-1.2.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (52.8 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 52.8/52.8 MB 11.8 MB/s eta 0:00:00
Requirement already satisfied: requests>=2.12 in /usr/lib/python3/dist-packages (from biotite<1.7,>=1.0->pinder==0.0.0+gebeb28a2) (2.25.1)
Requirement already satisfied: networkx>=2.0 in /usr/lib/python3/dist-packages (from biotite<1.7,>=1.0->pinder==0.0.0+gebeb28a2) (2.4)
Collecting numpy<2
  Downloading numpy-1.26.4-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (18.2 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 18.2/18.2 MB 73.4 MB/s eta 0:00:00
Requirement already satisfied: packaging>=24.0 in ./baseline-published/venv/lib/python3.10/site-packages (from biotite<1.7,>=1.0->pinder==0.0.0+gebeb28a2) (26.3)
Collecting biotraj<2.0,>=1.0
  Downloading biotraj-1.2.2-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.1 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.1/2.1 MB 10.1 MB/s eta 0:00:00
Requirement already satisfied: msgpack>=0.5.6 in /usr/lib/python3/dist-packages (from biotite<1.7,>=1.0->pinder==0.0.0+gebeb28a2) (1.0.3)
Collecting pydantic-core==2.50.2
  Downloading pydantic_core-2.50.2-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (2.2 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.2/2.2 MB 85.8 MB/s eta 0:00:00
Collecting typing_extensions
  Downloading typing_extensions-4.16.0-py3-none-any.whl (45 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.6/45.6 KB 235.9 MB/s eta 0:00:00
Collecting annotated-types>=0.6.0
  Downloading annotated_types-0.8.0-py3-none-any.whl (13 kB)
Collecting typing-inspection>=0.4.4
  Downloading typing_inspection-0.4.4-py3-none-any.whl (14 kB)
Collecting fastjsonschema>=2.15
  Downloading fastjsonschema-2.22.2-py3-none-any.whl (27 kB)
Requirement already satisfied: traitlets>=5.1 in /usr/lib/python3/dist-packages (from nbformat->pinder==0.0.0+gebeb28a2) (5.1.1)
Requirement already satisfied: jsonschema>=2.6 in /usr/lib/python3/dist-packages (from nbformat->pinder==0.0.0+gebeb28a2) (3.2.0)
Collecting jupyter-core!=5.0.*,>=4.12
  Downloading jupyter_core-5.9.1-py3-none-any.whl (29 kB)
Collecting narwhals>=1.15.1
  Downloading narwhals-2.28.0-py3-none-any.whl (490 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 490.6/490.6 KB 152.0 MB/s eta 0:00:00
Collecting xxhash
  Downloading xxhash-4.0.2-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (249 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 249.5/249.5 KB 151.5 MB/s eta 0:00:00
Requirement already satisfied: pyparsing in /usr/lib/python3/dist-packages (from torch_geometric->pinder==0.0.0+gebeb28a2) (2.4.7)
Collecting aiohttp
  Downloading aiohttp-3.14.5-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (1.9 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.9/1.9 MB 64.5 MB/s eta 0:00:00
Requirement already satisfied: jinja2 in /usr/lib/python3/dist-packages (from torch_geometric->pinder==0.0.0+gebeb28a2) (3.0.3)
Requirement already satisfied: psutil>=5.8.0 in /usr/lib/python3/dist-packages (from torch_geometric->pinder==0.0.0+gebeb28a2) (5.9.0)
Requirement already satisfied: fsspec in /usr/lib/python3/dist-packages (from torch_geometric->pinder==0.0.0+gebeb28a2) (2024.3.1)
Collecting scipy>=1.13
  Downloading scipy-1.15.3-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (37.7 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 37.7/37.7 MB 80.1 MB/s eta 0:00:00
Collecting traitlets>=5.1
  Downloading traitlets-5.16.1-py3-none-any.whl (86 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 86.2/86.2 KB 306.7 MB/s eta 0:00:00
Requirement already satisfied: platformdirs>=2.5 in /usr/lib/python3/dist-packages (from jupyter-core!=5.0.*,>=4.12->nbformat->pinder==0.0.0+gebeb28a2) (2.5.1)
Collecting propcache>=0.2.0
  Downloading propcache-0.5.4-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (224 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 224.3/224.3 KB 266.7 MB/s eta 0:00:00
Collecting multidict<8.0,>=4.5
  Downloading multidict-7.1.0-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (464 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 464.4/464.4 KB 179.0 MB/s eta 0:00:00
Collecting frozenlist>=1.1.1
  Downloading frozenlist-1.8.0-cp310-cp310-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (219 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 219.5/219.5 KB 315.4 MB/s eta 0:00:00
Collecting aiosignal>=1.4.0
  Downloading aiosignal-1.4.0-py3-none-any.whl (7.5 kB)
Requirement already satisfied: attrs>=17.3.0 in /usr/lib/python3/dist-packages (from aiohttp->torch_geometric->pinder==0.0.0+gebeb28a2) (21.2.0)
Collecting aiohappyeyeballs>=2.5.0
  Downloading aiohappyeyeballs-2.7.1-py3-none-any.whl (15 kB)
Collecting async-timeout<6.0,>=4.0
  Downloading async_timeout-5.0.1-py3-none-any.whl (6.2 kB)
Collecting yarl<2.0,>=1.25.1
  Downloading yarl-1.25.1-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (118 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 118.1/118.1 KB 267.6 MB/s eta 0:00:00
Requirement already satisfied: idna>=2.0 in /usr/lib/python3/dist-packages (from yarl<2.0,>=1.25.1->aiohttp->torch_geometric->pinder==0.0.0+gebeb28a2) (3.3)
Building wheels for collected packages: pinder
  Building wheel for pinder (pyproject.toml): started
  Building wheel for pinder (pyproject.toml): finished with status 'done'
  Created wheel for pinder: filename=pinder-0.0.0+gebeb28a2-py3-none-any.whl size=344128 sha256=b036e46acfd49f882eb79ff907f5724cd0c66233112d04ed87743249fc95e5c6
  Stored in directory: /tmp/pip-ephem-wheel-cache-jsv0cg2m/wheels/1c/2c/6b/b737489a2226eeccc44b5acc31b4edfdaa4166f0dc7ea87df0
Successfully built pinder
Installing collected packages: xxhash, typing_extensions, typeguard, traitlets, tqdm, tabulate, pyarrow, propcache, numpy, narwhals, frozenlist, fastjsonschema, async-timeout, annotated-types, aiohappyeyeballs, typing-inspection, torchtyping, scipy, pydantic-core, plotly, multidict, jupyter-core, aiosignal, yarl, pydantic, nbformat, biotraj, biotite, aiohttp, torch_geometric, fastpdb, pinder
  Attempting uninstall: typing_extensions
    Found existing installation: typing_extensions 4.10.0
    Not uninstalling typing-extensions at /usr/lib/python3/dist-packages, outside environment /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv
    Can't uninstall 'typing_extensions'. No files were found to uninstall.
  Attempting uninstall: traitlets
    Found existing installation: traitlets 5.1.1
    Not uninstalling traitlets at /usr/lib/python3/dist-packages, outside environment /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv
    Can't uninstall 'traitlets'. No files were found to uninstall.
  Attempting uninstall: numpy
    Found existing installation: numpy 1.21.5
    Not uninstalling numpy at /usr/lib/python3/dist-packages, outside environment /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv
    Can't uninstall 'numpy'. No files were found to uninstall.
  Attempting uninstall: scipy
    Found existing installation: scipy 1.8.0
    Not uninstalling scipy at /usr/lib/python3/dist-packages, outside environment /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv
    Can't uninstall 'scipy'. No files were found to uninstall.
  Attempting uninstall: jupyter-core
    Found existing installation: jupyter-core 4.9.1
    Not uninstalling jupyter-core at /usr/lib/python3/dist-packages, outside environment /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv
    Can't uninstall 'jupyter-core'. No files were found to uninstall.
Successfully installed aiohappyeyeballs-2.7.1 aiohttp-3.14.5 aiosignal-1.4.0 annotated-types-0.8.0 async-timeout-5.0.1 biotite-1.2.0 biotraj-1.2.2 fastjsonschema-2.22.2 fastpdb-1.3.3 frozenlist-1.8.0 jupyter-core-5.9.1 multidict-7.1.0 narwhals-2.28.0 nbformat-5.11.1 numpy-1.26.4 pinder-0.0.0+gebeb28a2 plotly-7.1.0 propcache-0.5.4 pyarrow-25.0.1 pydantic-2.14.2 pydantic-core-2.50.2 scipy-1.15.3 tabulate-0.10.0 torch_geometric-2.8.1 torchtyping-0.1.5 tqdm-4.70.1 traitlets-5.16.1 typeguard-2.13.3 typing-inspection-0.4.4 typing_extensions-4.16.0 xxhash-4.0.2 yarl-1.25.1
Collecting fire
  Downloading fire-0.7.1-py3-none-any.whl (115 kB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 115.9/115.9 KB 2.6 MB/s eta 0:00:00
Requirement already satisfied: termcolor in /usr/lib/python3/dist-packages (from fire) (1.1.0)
Installing collected packages: fire
Successfully installed fire-0.7.1
   torch seen by the baseline venv: 2.7.0 @ /usr/lib/python3/dist-packages/torch/__init__.py
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/pinder/methods/main.py", line 8, in <module>
    from pinder.core.utils import setup_logger
  File "/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/pinder/core/__init__.py", line 17, in <module>
    from pinder.core.index.system import PinderSystem
  File "/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/pinder/core/index/system.py", line 8, in <module>
    from pinder.core.loader.structure import mask_common_uniprot, Structure
  File "/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/pinder/core/loader/structure.py", line 9, in <module>
    import biotite.structure as struc
  File "/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/biotite/structure/__init__.py", line 107, in <module>
    from .atoms import *
  File "/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/biotite/structure/atoms.py", line 29, in <module>
    from biotite.structure.bonds import BondList
  File "src/biotite/structure/bonds.pyx", line 24, in init biotite.structure.bonds
  File "/usr/lib/python3/dist-packages/networkx/__init__.py", line 115, in <module>
    import networkx.readwrite
  File "/usr/lib/python3/dist-packages/networkx/readwrite/__init__.py", line 15, in <module>
    from networkx.readwrite.graphml import *
  File "/usr/lib/python3/dist-packages/networkx/readwrite/graphml.py", line 314, in <module>
    class GraphML(object):
  File "/usr/lib/python3/dist-packages/networkx/readwrite/graphml.py", line 346, in GraphML
    (np.int, "int"), (np.int8, "int"),
  File "/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/numpy/__init__.py", line 324, in __getattr__
    raise AttributeError(__former_attrs__[attr])
AttributeError: module 'numpy' has no attribute 'int'.
`np.int` was a deprecated alias for the builtin `int`. To avoid this error in existing code, use `int` by itself. Doing this will not modify any behavior and is safe. When replacing `np.int`, you may wish to use e.g. `np.int64` or `np.int32` to specify the precision. If you wish to review your current use, check the release note link for additional information.
The aliases was originally deprecated in NumPy 1.20; for more details and guidance see the original release note at:
    https://numpy.org/devdocs/release/1.20.0-notes.html#deprecations. Did you mean: 'inf'?
ERROR: setup.sh failed at line 284 (exit 1)