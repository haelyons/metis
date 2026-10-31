run_anchors.sh failed (rc 124, output gate: timeout). Repair run_anchors.sh, run_command.sh, or both under "/home/hal/dev/interp/metis/experiments/blind-01/m5/run8/agent/harness", and nothing else. A rewritten run_command.sh must still obey every run_command.sh rule using intake evidence. Preserve the published pin, configuration and stock image; sudo only for apt. Scope: setup.sh builds and checks only the baseline. The pipeline owns profiling and profiler installation; do not write profile.sh or install profiling tools. A setup repair may change only setup.sh; an anchors repair may change run_anchors.sh, run_command.sh, or both, and nothing else. Stay within each script's scope. Run the published build and binary and read measurements from its OUTPUT. run_command.sh contains only the exact measured baseline command and complete environment at the representative scale. run_command.sh is the canonical measured command and complete environment, including working directory, arguments, CUDA_VISIBLE_DEVICES and GPU count. run_command.sh must use paths relative to its working directory, never absolute paths into the run directory, and write only under out/ or temporary files. Concurrency and evaluation run it from sibling work directories linking the same trees. The pipeline owns CUDA MPS. No harness script (setup.sh, run_anchors.sh, run_command.sh, run_evaluation.sh) may set, unset or override any CUDA_MPS_* environment variable, or start or stop an MPS daemon; inherit these variables unchanged. run_anchors.sh must invoke bash harness/run_command.sh without overriding its environment or duplicating the workload command; parse its saved output for every intake item ID, anchors and references. With an empty anchors.json, still run the published command and write out/anchors_measured.json as {}. The fixed profiler invokes that identical file with bash from the same working directory. Keep output paths stable and preserve logs. Every later run script must preserve the published configuration. Validate printed configuration against the actual command and environment. Preserve consistency in repairs; read the other harness scripts while editing only the permitted scripts. Never parse or assert on source text. Measurement checks must fail only on missing or invalid output; the pipeline scores measured values against anchors. Never read experiments/, operator/, or control/. Do not run workloads locally or access the box. This is repair attempt 2 of 2 for this step.
Budget: 1200s; measured elapsed: 1751s; measured overrun: 551s. Script budgets in seconds: setup.sh=7200, run_anchors.sh=1200, fixed profiler=3600, run_evaluation.sh=172800 per invocation (also run_anchors.sh when used as the evaluation adapter); complete evaluation scorer=7200. Use one fixed scale from EXECUTION.json, no scale search or doubling loops, and finish well within the budget.
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
  "disk_home_avail_bytes": 2903642275840,
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
  "memory_kb": 231924756,
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
      "NVIDIA H100 80GB HBM3"
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
	83 	147.31  108.03  183.99   	 22.39  -18.77  -38.57     2241.393
	84 	246.01  133.69  327.95   	 58.39   25.23  -28.57     2235.358
	85 	260.18   46.68   29.04   	 28.39  -32.77   13.43     2234.769
	86 	337.67   99.73   73.17   	 10.39   -6.77  -32.57     2232.583
	87 	151.37   64.49  263.72   	 76.39   17.23  -16.57     2227.099
	88 	191.92  133.46  269.69   	 68.39   17.23  -28.57     2224.342
	89 	351.57  138.24  167.69   	 56.39    9.23  -44.57     2220.519
	90 	207.62   58.60  307.55   	 54.39  -18.77   25.43     2218.257
	91 	204.75   57.66  292.92   	 48.39  -18.77   29.43     2216.691
	92 	152.45   73.82  202.86   	 14.39  -20.77  -26.57     2212.441
	93 	165.84   78.12  146.04   	 38.39   17.23   27.43     2212.280
	94 	303.98  137.32  247.52   	 44.39  -38.77  -10.57     2211.469
	95 	262.80   93.69  276.40   	 76.39  -16.77   23.43     2209.702
	96 	248.34  146.92  258.32   	 62.39  -40.77  -26.57     2207.113
	97 	  0.16  101.85  162.64   	 56.39   19.23  -40.57     2206.435
	98 	 11.39   38.39   72.86   	 40.39   39.23    5.43     2204.978
	99 	174.07  118.50  220.46   	 24.39  -30.77  -26.57     2204.924
	100 	275.21  169.03   11.71   	 42.39  -24.77  -46.57     2203.638
STAGE_STATUS {"stage": "view", "returncode": 0}
COMMAND ["../../../../baseline-published/frodock3_linux64/bin/frodockview_gcc", "clust_dock.dat", "-r", "1-100", "-p", "ligand.pdb"]
frodockview>  Ligand center: 2.450717 -0.366635 51.022671
	1 	  9.65  108.36  167.12   	 60.39   17.23  -36.57     3997.909 => ligand_1.pdb
	2 	  1.47  134.65  173.68   	 58.39   13.23  -42.57     3839.915 => ligand_2.pdb
	3 	  3.64  125.11  172.06   	 58.39   17.23  -40.57     3484.216 => ligand_3.pdb
	4 	 11.67   99.20  176.22   	 62.39   19.23  -32.57     3265.809 => ligand_4.pdb
	5 	 15.19  124.84  185.50   	 62.39   17.23  -36.57     3162.043 => ligand_5.pdb
	6 	 16.27  134.05  190.62   	 62.39   13.23  -40.57     2963.441 => ligand_6.pdb
	7 	 51.92   69.32   17.13   	 66.39  -28.77  -26.57     2871.168 => ligand_7.pdb
	8 	348.85  130.53  158.59   	 54.39   13.23  -44.57     2857.156 => ligand_8.pdb
	9 	196.93   94.60  270.80   	 64.39   -0.77  -38.57     2769.034 => ligand_9.pdb
	10 	 45.24   47.79   86.94   	 46.39   35.23  -24.57     2757.606 => ligand_10.pdb
	11 	 31.76  140.61  213.88   	 64.39   23.23  -36.57     2722.659 => ligand_11.pdb
	12 	357.70  139.60  186.95   	 62.39   13.23  -40.57     2714.546 => ligand_12.pdb
	13 	 10.37   65.20  168.45   	 62.39   29.23  -22.57     2684.042 => ligand_13.pdb
	14 	195.94   56.44  317.18   	 58.39  -18.77   25.43     2641.844 => ligand_14.pdb
	15 	338.49   75.16  359.60   	 52.39    7.23  -48.57     2635.695 => ligand_15.pdb
	16 	325.58  108.98  248.70   	 28.39  -32.77  -16.57     2633.214 => ligand_16.pdb
	17 	243.82   73.12   54.59   	 22.39  -32.77  -20.57     2626.354 => ligand_17.pdb
	18 	189.62   68.10  299.64   	 52.39  -20.77   25.43     2578.931 => ligand_18.pdb
	19 	359.91  101.66  167.23   	 58.39   21.23  -34.57     2576.924 => ligand_19.pdb
	20 	236.06   58.61  102.69   	 14.39  -28.77   -6.57     2548.354 => ligand_20.pdb
	21 	 14.83   61.81  167.98   	 62.39   23.23  -30.57     2542.736 => ligand_21.pdb
	22 	 37.93  104.96  358.58   	 52.39  -32.77  -28.57     2519.059 => ligand_22.pdb
	23 	354.42  103.05  156.44   	 52.39   15.23  -44.57     2463.314 => ligand_23.pdb
	24 	 77.92   74.11   50.23   	 48.39  -36.77  -12.57     2456.285 => ligand_24.pdb
	25 	 66.94  134.41  231.38   	 72.39   21.23  -32.57     2445.072 => ligand_25.pdb
	26 	 89.31    5.45  269.43   	 56.39   31.23  -24.57     2442.060 => ligand_26.pdb
	27 	  5.14  144.60  185.05   	 60.39   17.23  -40.57     2430.612 => ligand_27.pdb
	28 	243.86  158.52  155.58   	 70.39    3.23  -38.57     2424.015 => ligand_28.pdb
	29 	 13.40   79.81  164.59   	 60.39   21.23  -34.57     2412.281 => ligand_29.pdb
	30 	 21.43  109.55  174.86   	 64.39   15.23  -36.57     2408.248 => ligand_30.pdb
	31 	275.03  107.55  232.01   	 56.39  -38.77   -6.57     2403.344 => ligand_31.pdb
	32 	 11.37   71.77   19.70   	 14.39   29.23    3.43     2400.051 => ligand_32.pdb
	33 	100.22   44.11   66.22   	 38.39  -38.77  -16.57     2398.621 => ligand_33.pdb
	34 	352.83  108.30   32.12   	 72.39   27.23  -22.57     2392.658 => ligand_34.pdb
	35 	355.47  150.62  308.23   	 46.39  -36.77  -22.57     2392.445 => ligand_35.pdb
	36 	293.85  107.79  319.69   	 56.39  -12.77  -42.57     2391.555 => ligand_36.pdb
	37 	 43.21  112.64  200.83   	 70.39   17.23  -34.57     2389.995 => ligand_37.pdb
	38 	123.71  124.06  298.28   	 56.39   25.23  -46.57     2388.688 => ligand_38.pdb
	39 	 16.70   80.85  172.20   	 64.39   25.23  -26.57     2377.403 => ligand_39.pdb
	40 	 39.37  117.59  358.07   	 50.39  -34.77  -24.57     2368.159 => ligand_40.pdb
	41 	297.29   48.60  171.26   	 28.39   37.23   -6.57     2367.607 => ligand_41.pdb
	42 	331.35  123.39  131.53   	 46.39   11.23  -48.57     2359.940 => ligand_42.pdb
	43 	 18.15  161.49  324.99   	 44.39  -38.77  -18.57     2354.703 => ligand_43.pdb
	44 	358.02  149.88  199.25   	 64.39   13.23  -38.57     2348.687 => ligand_44.pdb
	45 	 12.76   85.40   23.53   	 66.39    7.23  -44.57     2344.896 => ligand_45.pdb
	46 	 61.41  108.75   18.56   	 42.39   39.23    3.43     2341.700 => ligand_46.pdb
	47 	224.10   56.18  349.81   	 70.39    3.23  -40.57     2335.962 => ligand_47.pdb
	48 	 68.82  144.70  342.05   	 14.39  -18.77  -24.57     2335.133 => ligand_48.pdb
	49 	  0.40  129.47  325.76   	 48.39  -32.77  -34.57     2334.659 => ligand_49.pdb
	50 	102.10  134.61  342.03   	  0.39   -8.77   -4.57     2334.595 => ligand_50.pdb
	51 	 15.24  157.84  294.29   	 48.39   35.23  -28.57     2331.690 => ligand_51.pdb
	52 	225.00   93.53  160.17   	  0.39   -4.77  -18.57     2322.079 => ligand_52.pdb
	53 	336.58  139.54  169.73   	 58.39   15.23  -42.57     2321.368 => ligand_53.pdb
	54 	314.67  106.32  242.27   	 32.39  -34.77  -14.57     2319.095 => ligand_54.pdb
	55 	 78.49  143.48  246.24   	 70.39   17.23  -36.57     2313.892 => ligand_55.pdb
	56 	 31.78  118.75  196.49   	 66.39   17.23  -36.57     2313.885 => ligand_56.pdb
	57 	  7.84  118.16  156.86   	 60.39   15.23  -40.57     2312.056 => ligand_57.pdb
	58 	 96.62   51.68  136.94   	 76.39   21.23  -18.57     2311.211 => ligand_58.pdb
	59 	110.68  148.17    2.48   	 74.39   15.23  -24.57     2307.501 => ligand_59.pdb
	60 	 68.85  165.73  302.21   	 74.39   15.23  -20.57     2305.024 => ligand_60.pdb
	61 	 10.32   91.45  173.98   	 62.39   23.23  -30.57     2304.574 => ligand_61.pdb
	62 	226.59  102.27  149.35   	 78.39   15.23  -24.57     2301.064 => ligand_62.pdb
	63 	232.42  127.73   51.93   	 46.39  -22.77  -44.57     2300.122 => ligand_63.pdb
	64 	276.32   77.31  296.52   	  6.39  -24.77  -14.57     2292.741 => ligand_64.pdb
	65 	288.21  140.53   99.10   	 46.39  -12.77  -48.57     2292.138 => ligand_65.pdb
	66 	 10.69  134.88  205.16   	 66.39   13.23  -38.57     2284.856 => ligand_66.pdb
	67 	118.78   48.96   29.60   	 26.39  -36.77   -6.57     2279.899 => ligand_67.pdb
	68 	 85.89   83.76   56.16   	 60.39   31.23  -24.57     2277.215 => ligand_68.pdb
	69 	245.78   96.95   72.25   	 52.39  -40.77  -24.57     2273.781 => ligand_69.pdb
	70 	357.43  128.28  187.51   	 62.39   15.23  -36.57     2272.812 => ligand_70.pdb
	71 	 43.52   61.61   22.50   	 70.39  -26.77  -26.57     2269.975 => ligand_71.pdb
	72 	100.66  103.42   16.38   	 26.39  -22.77  -36.57     2264.507 => ligand_72.pdb
	73 	359.77   73.65   16.41   	 62.39   13.23  -42.57     2259.736 => ligand_73.pdb
	74 	303.22  102.43  344.97   	 60.39   -2.77  -42.57     2259.675 => ligand_74.pdb
	75 	353.29  145.58  173.34   	 58.39    5.23  -44.57     2259.169 => ligand_75.pdb
	76 	323.61  139.42  145.41   	 50.39   -0.77  -48.57     2258.298 => ligand_76.pdb
	77 	215.76   47.35  300.12   	 54.39  -14.77   29.43     2257.810 => ligand_77.pdb
	78 	163.23   82.58  255.21   	 76.39    7.23  -18.57     2253.870 => ligand_78.pdb
	79 	328.00  135.82  262.38   	 40.39  -38.77   -8.57     2246.531 => ligand_79.pdb
	80 	 65.55  101.14   10.82   	 62.39  -32.77  -34.57     2245.732 => ligand_80.pdb
	81 	179.75   67.04  308.55   	 56.39  -20.77   25.43     2244.533 => ligand_81.pdb
	82 	342.00  118.27  149.38   	 50.39   15.23  -44.57     2242.326 => ligand_82.pdb
	83 	147.31  108.03  183.99   	 22.39  -18.77  -38.57     2241.393 => ligand_83.pdb
	84 	246.01  133.69  327.95   	 58.39   25.23  -28.57     2235.358 => ligand_84.pdb
	85 	260.18   46.68   29.04   	 28.39  -32.77   13.43     2234.769 => ligand_85.pdb
	86 	337.67   99.73   73.17   	 10.39   -6.77  -32.57     2232.583 => ligand_86.pdb
	87 	151.37   64.49  263.72   	 76.39   17.23  -16.57     2227.099 => ligand_87.pdb
	88 	191.92  133.46  269.69   	 68.39   17.23  -28.57     2224.342 => ligand_88.pdb
	89 	351.57  138.24  167.69   	 56.39    9.23  -44.57     2220.519 => ligand_89.pdb
	90 	207.62   58.60  307.55   	 54.39  -18.77   25.43     2218.257 => ligand_90.pdb
	91 	204.75   57.66  292.92   	 48.39  -18.77   29.43     2216.691 => ligand_91.pdb
	92 	152.45   73.82  202.86   	 14.39  -20.77  -26.57     2212.441 => ligand_92.pdb
	93 	165.84   78.12  146.04   	 38.39   17.23   27.43     2212.280 => ligand_93.pdb
	94 	303.98  137.32  247.52   	 44.39  -38.77  -10.57     2211.469 => ligand_94.pdb
	95 	262.80   93.69  276.40   	 76.39  -16.77   23.43     2209.702 => ligand_95.pdb
	96 	248.34  146.92  258.32   	 62.39  -40.77  -26.57     2207.113 => ligand_96.pdb
	97 	  0.16  101.85  162.64   	 56.39   19.23  -40.57     2206.435 => ligand_97.pdb
	98 	 11.39   38.39   72.86   	 40.39   39.23    5.43     2204.978 => ligand_98.pdb
	99 	174.07  118.50  220.46   	 24.39  -30.77  -26.57     2204.924 => ligand_99.pdb
	100 	275.21  169.03   11.71   	 42.39  -24.77  -46.57     2203.638 => ligand_100.pdb
STAGE_STATUS {"stage": "poses", "returncode": 0}
CASE_WALL {"id": "1dv1__A1_P24182--1dv1__B1_P24182", "wall_s": 286.79252167799996}
COMMAND ["/usr/bin/mpirun", "-np", "8", "--use-hwthread-cpus", "../../../../baseline-published/frodock3_linux64/bin/frodockgrid_mpi_gcc", "receptor.pdb", "-o", "receptor_W.mrc"]
0 3 1 4 5 2 7 6 MPI processes (8) awake!
With hydrogens: no
Grid voxel: 1.0
Option: VdW potential. Probe radius: 2.0
parallelization:  num_atom= 3878  natom= 484  natomr= 6
Written output potential (VdW or Electrostatic) map: receptor_W.mrc
--------------------------------------------------------------------------
Primary job  terminated normally, but 1 process returned
a non-zero exit code. Per user-direction, the job has been aborted.
--------------------------------------------------------------------------
--------------------------------------------------------------------------
mpirun detected that one or more processes exited with non-zero status, thus causing
the job to be terminated. The first process to do so was:

  Process name: [[50466,1],2]
  Exit code:    1
--------------------------------------------------------------------------
STAGE_STATUS {"stage": "grid-W", "returncode": 1}
COMMAND ["/usr/bin/mpirun", "-np", "8", "--use-hwthread-cpus", "../../../../baseline-published/frodock3_linux64/bin/frodockgrid_mpi_gcc", "receptor.pdb", "-o", "receptor_E.mrc", "-m", "1", "-t", "A"]
4 6 7 0 2 3 1 5 MPI processes (8) awake!
With hydrogens: no
Grid voxel: 1.0
Option: Electrostatic potential.
parallelization:  num_atom= 3878  natom= 484  natomr= 6
Written output potential (VdW or Electrostatic) map: receptor_E.mrc
--------------------------------------------------------------------------
Primary job  terminated normally, but 1 process returned
a non-zero exit code. Per user-direction, the job has been aborted.
--------------------------------------------------------------------------
--------------------------------------------------------------------------
mpirun detected that one or more processes exited with non-zero status, thus causing
the job to be terminated. The first process to do so was:

  Process name: [[50627,1],1]
  Exit code:    1
--------------------------------------------------------------------------
STAGE_STATUS {"stage": "grid-E", "returncode": 1}
COMMAND ["/usr/bin/mpirun", "-np", "8", "--use-hwthread-cpus", "../../../../baseline-published/frodock3_linux64/bin/frodockgrid_mpi_gcc", "receptor.pdb", "-o", "receptor_DS.mrc", "-m", "3"]
4 6 7 3 0 2 5 1 MPI processes (8) awake!
With hydrogens: no
Grid voxel: 1.0
Option: Desolvation potential.
        Radius -> Water: 1.400000 - Generic atom probe: 1.950000

Pre-stage for ASA computation (in_wradprobe= 1.400000)... Finished!
Computing the original ASA in all the 3878 atoms...
Minor bottleneck parallelization:  num_atom= 3878  natom= 484  natomr= 6
ASA pdb file receptor_ASA.pdb created (ASA introduced in Occupancy column)
Creating mask volume of invalid positions for the probe (where probe collides with atoms)... Finished!
Computing Solvation Map...
Main bottleneck parallelization:  cont_asa= 1846  nasa= 230  nasar= 6
Total ASA computations: 1148438  (skipped: 642667  out: 2436615)
Written ASA potential map: receptor_DS.mrc
STAGE_STATUS {"stage": "grid-receptor-DS", "returncode": 0}
COMMAND ["/usr/bin/mpirun", "-np", "8", "--use-hwthread-cpus", "../../../../baseline-published/frodock3_linux64/bin/frodockgrid_mpi_gcc", "ligand.pdb", "-o", "ligand_DS.mrc", "-m", "3"]
3 5 6 0 1 2 7 4 MPI processes (8) awake!
With hydrogens: no
Grid voxel: 1.0
Option: Desolvation potential.
        Radius -> Water: 1.400000 - Generic atom probe: 1.950000

Pre-stage for ASA computation (in_wradprobe= 1.400000)... Finished!
Computing the original ASA in all the 3888 atoms...
Minor bottleneck parallelization:  num_atom= 3888  natom= 486  natomr= 0
ASA pdb file ligand_ASA.pdb created (ASA introduced in Occupancy column)
Creating mask volume of invalid positions for the probe (where probe collides with atoms)... Finished!
Computing Solvation Map...
Main bottleneck parallelization:  cont_asa= 1869  nasa= 233  nasar= 5
Total ASA computations: 1163404  (skipped: 656334  out: 2461827)
Written ASA potential map: ligand_DS.mrc
STAGE_STATUS {"stage": "grid-ligand-DS", "returncode": 0}
/tmp/m5-929bafad-0547-42d4-95e5-7844238cebb2/baseline-published/venv/lib/python3.10/site-packages/biotite/structure/io/pdb/file.py:470: UserWarning: 3878 elements were guessed from atom name
  warnings.warn(
/tmp/m5-929bafad-0547-42d4-95e5-7844238cebb2/baseline-published/venv/lib/python3.10/site-packages/biotite/structure/io/pdb/file.py:470: UserWarning: 3888 elements were guessed from atom name
  warnings.warn(
COMMAND ["/usr/bin/mpirun", "-np", "8", "--use-hwthread-cpus", "../../../../baseline-published/frodock3_linux64/bin/frodock_mpi_gcc", "receptor_ASA.pdb", "ligand_ASA.pdb", "-w", "receptor_W.mrc", "-e", "receptor_E.mrc", "--th", "10", "-d", "receptor_DS.mrc,ligand_DS.mrc", "-t", "A", "-o", "dock.dat", "-s", "../../../../baseline-published/frodock3_linux64/bin/soap.bin"]