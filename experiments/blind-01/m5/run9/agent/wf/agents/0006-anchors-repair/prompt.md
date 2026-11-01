run_anchors.sh failed (rc 1). Repair run_anchors.sh, run_command.sh, or both under "/home/hal/dev/interp/metis/experiments/blind-01/m5/run9/agent/harness", and nothing else. A rewritten run_command.sh must still obey every run_command.sh rule using intake evidence. Preserve the published pin, configuration and stock image; sudo only for apt. Scope: setup.sh builds and checks only the baseline. The pipeline owns profiling and profiler installation; do not write profile.sh or install profiling tools. A setup repair may change only setup.sh; an anchors repair may change run_anchors.sh, run_command.sh, or both, and nothing else. Stay within each script's scope. Run the published build and binary and read measurements from its OUTPUT. run_command.sh contains only the exact measured baseline command and complete environment at the representative scale. run_command.sh is the canonical measured command and complete environment, including working directory, arguments, CUDA_VISIBLE_DEVICES and GPU count. run_command.sh must use paths relative to its working directory, never absolute paths into the run directory, and write only under out/ or temporary files. Concurrency and evaluation run it from sibling work directories linking the same trees. The pipeline owns CUDA MPS. No harness script (setup.sh, run_anchors.sh, run_command.sh, run_evaluation.sh) may set, unset or override any CUDA_MPS_* environment variable, or start or stop an MPS daemon; inherit these variables unchanged. run_anchors.sh must invoke bash harness/run_command.sh without overriding its environment or duplicating the workload command; parse its saved output for every intake item ID, anchors and references. With an empty anchors.json, still run the published command and write out/anchors_measured.json as {}. The fixed profiler invokes that identical file with bash from the same working directory. Keep output paths stable and preserve logs. Every later run script must preserve the published configuration. Validate printed configuration against the actual command and environment. Preserve consistency in repairs; read the other harness scripts while editing only the permitted scripts. Never parse or assert on source text. Measurement checks must fail only on missing or invalid output; the pipeline scores measured values against anchors. Never read experiments/, operator/, or control/. Do not run workloads locally or access the box. This is repair attempt 1 of 2 for this step.
Budget: 34355s resolved now, the time left before the run ceiling, not a target (explicit args budget overrides); failed attempt budget: 39446s; measured elapsed: 5091s; measured overrun: 0s. Script budgets in seconds: setup.sh=34355, run_anchors.sh=34355, fixed profiler=34355 (resolved now: time left before the run ceiling, not a target; explicit args budgets override); run_evaluation.sh=14400 per invocation (also run_anchors.sh when used as the evaluation adapter); complete evaluation scorer=2400. Use one fixed scale from EXECUTION.json, no scale search or doubling loops, and finish well within the budget.
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
frodock>   Number of points to explore: 64866  saving all best solutions
frodock>
frodock>   Map  shift: 4.000000 1.000000 2.000000 size
frodock>
frodock>  Time:  00h. 00' 11''
frodock>
frodock> Determination of translational points to explore
frodock>  Mask created
frodock>   Mask  origin: -33.974995 -4.747807 -24.176903
frodock>   Mask  center: 55.000000 58.000000 50.000000
frodock>   Number of points to explore: 64866  saving all best solutions
frodock>
frodock>   Map  shift: 4.000000 1.000000 2.000000 size
frodock>
frodock>  Time:  00h. 00' 12''
frodock>
frodock> Determination of translational points to explore
frodock>
frodock> Determination of translational points to explore
frodock>  Time:  00h. 00' 12''
frodock>  Time:  00h. 00' 12''
frodock>
frodock> Determination of translational points to explore
frodock>  Mask created
frodock>   Mask  origin: -33.974995 -4.747807 -24.176903
frodock>   Mask  center: 55.000000 58.000000 50.000000
frodock>   Number of points to explore: 64866  saving all best solutions
frodock>
frodock>   Map  shift: 4.000000 1.000000 2.000000 size
frodock>
frodock>   Mask  origin: -33.974995 -4.747807 -24.176903
frodock>   Mask  center: 55.000000 58.000000 50.000000
frodock>  Mask created
frodock>   Number of points to explore: 64866  saving all best solutions
frodock>
frodock>   Map  shift: 4.000000 1.000000 2.000000 size
frodock>
frodock>   Mask  origin: -33.974995 -4.747807 -24.176903
frodock>   Mask  center: 55.000000 58.000000 50.000000
frodock>  Mask created
frodock>   Number of points to explore: 64866  saving all best solutions
frodock>
frodock>   Map  shift: 4.000000 1.000000 2.000000 size
frodock>

frodock> Number of solutions: 31636 
frodock> Total time:  00h. 03' 03''
frodock>

frodock> Number of solutions: 31805 
frodock> Total time:  00h. 03' 38''
frodock>

frodock> Number of solutions: 30651 
frodock> Total time:  00h. 03' 52''
frodock>

frodock> Number of solutions: 27850 
frodock> Total time:  00h. 04' 12''
frodock>

frodock> Number of solutions: 28147 
frodock> Total time:  00h. 04' 16''
frodock>

frodock> Number of solutions: 25281 
frodock> Total time:  00h. 04' 26''
frodock>

frodock> Number of solutions: 11678 
frodock> Total time:  00h. 04' 39''
frodock>

frodock> Number of solutions: 19322 
frodock> Total time:  00h. 04' 46''
frodock>
Number of peaks 206370
Number of clusters 50
Center Lig 25.025005 54.252193 27.823097
Processing 0 1Processing 1 1Processing 2 2Processing 3 3Processing 4 3Processing 5 3Processing 6 3Processing 7 3Processing 8 4Processing 9 4Processing 10 4Processing 11 4Processing 12 5Processing 13 5Processing 14 6Processing 15 6Processing 16 7Processing 17 8Processing 18 9Processing 19 9Processing 20 9Processing 21 10Processing 22 10Processing 23 10Processing 24 11Processing 25 12Processing 26 12Processing 27 12Processing 28 13Processing 29 14Processing 30 14Processing 31 14Processing 32 14Processing 33 14Processing 34 14Processing 35 14Processing 36 14Processing 37 14Processing 38 15Processing 39 15Processing 40 15Processing 41 15Processing 42 15Processing 43 16Processing 44 16Processing 45 16Processing 46 16Processing 47 16Processing 48 16Processing 49 16Processing 50 16Processing 51 17Processing 52 17Processing 53 17Processing 54 17Processing 55 17Processing 56 18Processing 57 19Processing 58 20Processing 59 20Processing 60 20Processing 61 20Processing 62 21Processing 63 22Processing 64 22Processing 65 22Processing 66 22Processing 67 22Processing 68 23Processing 69 23Processing 70 23Processing 71 24Processing 72 25Processing 73 25Processing 74 25Processing 75 26Processing 76 26Processing 77 27Processing 78 28Processing 79 28Processing 80 28Processing 81 28Processing 82 28Processing 83 28Processing 84 28Processing 85 29Processing 86 30Processing 87 31Processing 88 32Processing 89 33Processing 90 33Processing 91 34Processing 92 34Processing 93 35Processing 94 35Processing 95 36Processing 96 37Processing 97 38Processing 98 38Processing 99 38Processing 100 39Processing 101 39Processing 102 40Processing 103 40Processing 104 40Processing 105 41Processing 106 41Processing 107 41Processing 108 41Processing 109 42Processing 110 42Processing 111 42Processing 112 42Processing 113 43Processing 114 44Processing 115 44Processing 116 44Processing 117 45Processing 118 46Processing 119 47Processing 120 47Processing 121 47Processing 122 48Processing 123 49Processing 124 50Sort process...
Maximum correlation: 4199.738281 
Clustering process...
	1 	191.25   56.09  348.75   	-16.97   47.25   19.82     4199.738
	2 	  4.69   43.37  174.77   	 -6.97   59.25   53.82     3955.022
	3 	  4.79   41.28  180.33   	 -6.97   43.25    5.82     3822.031
	4 	 59.30   33.09  138.73   	 -2.97   59.25   57.82     3568.491
	5 	 33.39   35.58  127.35   	-12.97   39.25   15.82     3383.283
	6 	 46.83   67.77  292.07   	 -6.97   35.25   25.82     3358.334
	7 	  0.41   40.54  174.95   	 -8.97   39.25    7.82     3321.657
	8 	  6.04   22.50   56.20   	 21.03   39.25   59.82     3264.318
	9 	 44.60   33.30  151.61   	 -6.97   59.25   55.82     3220.208
	10 	249.41   57.86  123.43   	 15.03   59.25   61.82     3218.676
	11 	240.89   70.76  297.08   	  5.03   31.25    7.82     3197.645
	12 	191.63  120.08  289.64   	 33.03   35.25  -10.18     3190.242
	13 	 53.94   56.25  280.77   	 11.03   37.25   -0.18     3165.800
	14 	196.88   61.50  337.50   	-14.97   47.25   15.82     3150.447
	15 	253.41   60.97  130.78   	 41.03   51.25   61.82     3060.532
	16 	 49.96   61.39  336.67   	 11.03   29.25    7.82     3033.594
	17 	354.69   44.26  185.92   	 -6.97   39.25    3.82     3010.486
	18 	 77.56  102.95  105.72   	 19.03   17.25   45.82     2990.259
	19 	141.14   44.79  105.82   	  1.03   71.25    7.82     2987.475
	20 	132.63   18.00  161.14   	  5.03   69.25    3.82     2982.482
	21 	 52.86   46.98  264.89   	 11.03   41.25   -0.18     2965.617
	22 	251.69  124.39  347.43   	  7.03   35.25   -6.18     2962.996
	23 	 34.44   28.58  129.87   	-10.97   41.25   11.82     2939.472
	24 	331.70  117.79  338.50   	 41.03   63.25   -2.18     2934.420
	25 	 83.70   92.02  100.31   	 15.03   15.25   43.82     2932.781
	26 	252.16  124.83  359.04   	  7.03   39.25   -8.18     2922.254
	27 	354.76   67.39  130.05   	  9.03   61.25   63.82     2906.751
	28 	198.56  129.91  287.02   	 35.03   39.25  -10.18     2906.015
	29 	224.19  139.52  130.17   	  3.03   21.25   35.82     2876.587
	30 	325.39  151.16  237.91   	 31.03   63.25   -8.18     2876.139
	31 	 43.65   71.81  188.05   	 -8.97   43.25    7.82     2875.866
	32 	257.36  118.70  353.91   	  3.03   37.25   -6.18     2873.768
	33 	213.79  148.01  146.58   	 15.03   59.25   63.82     2869.534
	34 	199.04   85.37  334.22   	 -6.97   47.25   11.82     2861.966
	35 	 72.96   44.75   39.86   	 23.03   45.25   61.82     2857.439
	36 	191.25   37.50  348.75   	-18.97   45.25   21.82     2855.615
	37 	309.66  146.95  218.81   	 19.03   71.25   -4.18     2853.870
	38 	196.70  118.25  205.86   	 -0.97   35.25   13.82     2853.221
	39 	279.24   41.12  118.29   	 19.03   59.25   61.82     2845.554
	40 	258.30   59.99  125.07   	 11.03   57.25   61.82     2835.223
	41 	 28.74  151.71  325.64   	 25.03   33.25   57.82     2831.799
	42 	232.33   60.24  107.53   	 11.03   71.25   61.82     2814.566
	43 	197.74  136.54  330.73   	 -2.97   37.25   11.82     2809.282
	44 	355.40   34.71  185.72   	 -8.97   55.25   51.82     2808.726
	45 	154.40  164.03   19.75   	  9.03   53.25   65.82     2804.259
	46 	349.10   61.15    1.83   	-10.97   37.25   19.82     2803.992
	47 	 61.94   44.48  276.26   	 11.03   41.25   -0.18     2801.891
	48 	241.74  152.58  331.53   	 43.03   65.25   -4.18     2792.576
	49 	255.27   55.39  114.41   	 13.03   63.25   61.82     2790.372
	50 	 33.75   41.60  119.37   	-14.97   35.25   21.82     2785.887
frodockview>  Ligand center: 25.025005 54.252193 27.823097
	1 	191.25   56.09  348.75   	-16.97   47.25   19.82     4199.738 => 1nr5_apo_L_1.pdb
	2 	  4.69   43.37  174.77   	 -6.97   59.25   53.82     3955.022 => 1nr5_apo_L_2.pdb
	3 	  4.79   41.28  180.33   	 -6.97   43.25    5.82     3822.031 => 1nr5_apo_L_3.pdb
	4 	 59.30   33.09  138.73   	 -2.97   59.25   57.82     3568.491 => 1nr5_apo_L_4.pdb
	5 	 33.39   35.58  127.35   	-12.97   39.25   15.82     3383.283 => 1nr5_apo_L_5.pdb
	6 	 46.83   67.77  292.07   	 -6.97   35.25   25.82     3358.334 => 1nr5_apo_L_6.pdb
	7 	  0.41   40.54  174.95   	 -8.97   39.25    7.82     3321.657 => 1nr5_apo_L_7.pdb
	8 	  6.04   22.50   56.20   	 21.03   39.25   59.82     3264.318 => 1nr5_apo_L_8.pdb
	9 	 44.60   33.30  151.61   	 -6.97   59.25   55.82     3220.208 => 1nr5_apo_L_9.pdb
	10 	249.41   57.86  123.43   	 15.03   59.25   61.82     3218.676 => 1nr5_apo_L_10.pdb
	11 	240.89   70.76  297.08   	  5.03   31.25    7.82     3197.645 => 1nr5_apo_L_11.pdb
	12 	191.63  120.08  289.64   	 33.03   35.25  -10.18     3190.242 => 1nr5_apo_L_12.pdb
	13 	 53.94   56.25  280.77   	 11.03   37.25   -0.18     3165.800 => 1nr5_apo_L_13.pdb
	14 	196.88   61.50  337.50   	-14.97   47.25   15.82     3150.447 => 1nr5_apo_L_14.pdb
	15 	253.41   60.97  130.78   	 41.03   51.25   61.82     3060.532 => 1nr5_apo_L_15.pdb
	16 	 49.96   61.39  336.67   	 11.03   29.25    7.82     3033.594 => 1nr5_apo_L_16.pdb
	17 	354.69   44.26  185.92   	 -6.97   39.25    3.82     3010.486 => 1nr5_apo_L_17.pdb
	18 	 77.56  102.95  105.72   	 19.03   17.25   45.82     2990.259 => 1nr5_apo_L_18.pdb
	19 	141.14   44.79  105.82   	  1.03   71.25    7.82     2987.475 => 1nr5_apo_L_19.pdb
	20 	132.63   18.00  161.14   	  5.03   69.25    3.82     2982.482 => 1nr5_apo_L_20.pdb
	21 	 52.86   46.98  264.89   	 11.03   41.25   -0.18     2965.617 => 1nr5_apo_L_21.pdb
	22 	251.69  124.39  347.43   	  7.03   35.25   -6.18     2962.996 => 1nr5_apo_L_22.pdb
	23 	 34.44   28.58  129.87   	-10.97   41.25   11.82     2939.472 => 1nr5_apo_L_23.pdb
	24 	331.70  117.79  338.50   	 41.03   63.25   -2.18     2934.420 => 1nr5_apo_L_24.pdb
	25 	 83.70   92.02  100.31   	 15.03   15.25   43.82     2932.781 => 1nr5_apo_L_25.pdb
	26 	252.16  124.83  359.04   	  7.03   39.25   -8.18     2922.254 => 1nr5_apo_L_26.pdb
	27 	354.76   67.39  130.05   	  9.03   61.25   63.82     2906.751 => 1nr5_apo_L_27.pdb
	28 	198.56  129.91  287.02   	 35.03   39.25  -10.18     2906.015 => 1nr5_apo_L_28.pdb
	29 	224.19  139.52  130.17   	  3.03   21.25   35.82     2876.587 => 1nr5_apo_L_29.pdb
	30 	325.39  151.16  237.91   	 31.03   63.25   -8.18     2876.139 => 1nr5_apo_L_30.pdb
	31 	 43.65   71.81  188.05   	 -8.97   43.25    7.82     2875.866 => 1nr5_apo_L_31.pdb
	32 	257.36  118.70  353.91   	  3.03   37.25   -6.18     2873.768 => 1nr5_apo_L_32.pdb
	33 	213.79  148.01  146.58   	 15.03   59.25   63.82     2869.534 => 1nr5_apo_L_33.pdb
	34 	199.04   85.37  334.22   	 -6.97   47.25   11.82     2861.966 => 1nr5_apo_L_34.pdb
	35 	 72.96   44.75   39.86   	 23.03   45.25   61.82     2857.439 => 1nr5_apo_L_35.pdb
	36 	191.25   37.50  348.75   	-18.97   45.25   21.82     2855.615 => 1nr5_apo_L_36.pdb
	37 	309.66  146.95  218.81   	 19.03   71.25   -4.18     2853.870 => 1nr5_apo_L_37.pdb
	38 	196.70  118.25  205.86   	 -0.97   35.25   13.82     2853.221 => 1nr5_apo_L_38.pdb
	39 	279.24   41.12  118.29   	 19.03   59.25   61.82     2845.554 => 1nr5_apo_L_39.pdb
	40 	258.30   59.99  125.07   	 11.03   57.25   61.82     2835.223 => 1nr5_apo_L_40.pdb
	41 	 28.74  151.71  325.64   	 25.03   33.25   57.82     2831.799 => 1nr5_apo_L_41.pdb
	42 	232.33   60.24  107.53   	 11.03   71.25   61.82     2814.566 => 1nr5_apo_L_42.pdb
	43 	197.74  136.54  330.73   	 -2.97   37.25   11.82     2809.282 => 1nr5_apo_L_43.pdb
	44 	355.40   34.71  185.72   	 -8.97   55.25   51.82     2808.726 => 1nr5_apo_L_44.pdb
	45 	154.40  164.03   19.75   	  9.03   53.25   65.82     2804.259 => 1nr5_apo_L_45.pdb
	46 	349.10   61.15    1.83   	-10.97   37.25   19.82     2803.992 => 1nr5_apo_L_46.pdb
	47 	 61.94   44.48  276.26   	 11.03   41.25   -0.18     2801.891 => 1nr5_apo_L_47.pdb
	48 	241.74  152.58  331.53   	 43.03   65.25   -4.18     2792.576 => 1nr5_apo_L_48.pdb
	49 	255.27   55.39  114.41   	 13.03   63.25   61.82     2790.372 => 1nr5_apo_L_49.pdb
	50 	 33.75   41.60  119.37   	-14.97   35.25   21.82     2785.887 => 1nr5_apo_L_50.pdb
/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/biotite/structure/io/pdb/file.py:470: UserWarning: 2890 elements were guessed from atom name
  warnings.warn(
2026-11-01 04:41:48,095 | pinder.methods.run.frodock.predict:173 | INFO : Copying the results to /tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/out/results/frodock/1nr5__A1_P07547--1nr5__A2_P07547/apo_decoys
2026-11-01 04:41:48,107 | pinder.methods.main:137 | INFO : Success! Finished docking 16 systems
PREDICT_EXIT=0
Traceback (most recent call last):
  File "/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/bin/pinder_eval", line 8, in <module>
    sys.exit(main())
  File "/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/pinder/eval/run.py", line 85, in main
    summarize_valid_systems(eval_dir, custom_index=args.custom_index)
  File "/tmp/m5-9298701a-0ce9-4dbe-9cf1-fecd9cf1e79e/baseline-published/venv/lib/python3.10/site-packages/pinder/eval/dockq/method.py", line 191, in summarize_valid_systems
    raise ExpectedChainsNotFoundError(test_decoy, list(decoy_chains))
pinder.eval.dockq.method.ExpectedChainsNotFoundError: PDB model_47 is missing expected chains for running eval:_L_R != R_L.There should be two chains: R (receptor) and L (ligand).
EVAL_EXIT=1
ERROR: pinder_eval exited 1
== run_command.sh exit status 1
ERROR: harness/run_command.sh failed (1); see out/run_command/run_command.log