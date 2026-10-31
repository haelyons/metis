setup.sh failed (rc 1). Repair only "/home/hal/dev/interp/metis/experiments/blind-01/m5/run8/agent/harness/setup.sh" using intake evidence. Preserve the published pin, configuration and stock image; sudo only for apt. Scope: setup.sh builds and checks only the baseline. The pipeline owns profiling and profiler installation; do not write profile.sh or install profiling tools. A setup repair may change only setup.sh; an anchors repair may change run_anchors.sh, run_command.sh, or both, and nothing else. Stay within each script's scope. Run the published build and binary and read measurements from its OUTPUT. run_command.sh contains only the exact measured baseline command and complete environment at the representative scale. run_command.sh is the canonical measured command and complete environment, including working directory, arguments, CUDA_VISIBLE_DEVICES and GPU count. run_command.sh must use paths relative to its working directory, never absolute paths into the run directory, and write only under out/ or temporary files. Concurrency and evaluation run it from sibling work directories linking the same trees. The pipeline owns CUDA MPS. No harness script (setup.sh, run_anchors.sh, run_command.sh, run_evaluation.sh) may set, unset or override any CUDA_MPS_* environment variable, or start or stop an MPS daemon; inherit these variables unchanged. run_anchors.sh must invoke bash harness/run_command.sh without overriding its environment or duplicating the workload command; parse its saved output for every intake item ID, anchors and references. With an empty anchors.json, still run the published command and write out/anchors_measured.json as {}. The fixed profiler invokes that identical file with bash from the same working directory. Keep output paths stable and preserve logs. Every later run script must preserve the published configuration. Validate printed configuration against the actual command and environment. Preserve consistency in repairs; read the other harness scripts while editing only the permitted scripts. Never parse or assert on source text. Measurement checks must fail only on missing or invalid output; the pipeline scores measured values against anchors. Never read experiments/, operator/, or control/. Do not run workloads locally or access the box. This is repair attempt 1 of 4 for this script.
Budget: 7200s; measured elapsed: 53s; measured overrun: 0s. Script budgets in seconds: setup.sh=7200, run_anchors.sh=1200, fixed profiler=3600, run_evaluation.sh=172800 per invocation (also run_anchors.sh when used as the evaluation adapter); complete evaluation scorer=7200. Use one fixed scale from EXECUTION.json, no scale search or doubling loops, and finish well within the budget.
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
Selecting previously unselected package libhdf5-openmpi-cpp-103-1:amd64.
Preparing to unpack .../31-libhdf5-openmpi-cpp-103-1_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-openmpi-cpp-103-1:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libhdf5-openmpi-fortran-102:amd64.
Preparing to unpack .../32-libhdf5-openmpi-fortran-102_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-openmpi-fortran-102:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libhdf5-openmpi-hl-100:amd64.
Preparing to unpack .../33-libhdf5-openmpi-hl-100_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-openmpi-hl-100:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libhdf5-openmpi-hl-cpp-100:amd64.
Preparing to unpack .../34-libhdf5-openmpi-hl-cpp-100_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-openmpi-hl-cpp-100:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libhdf5-openmpi-hl-fortran-100:amd64.
Preparing to unpack .../35-libhdf5-openmpi-hl-fortran-100_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-openmpi-hl-fortran-100:amd64 (1.10.7+repack-4ubuntu2) ...
Selecting previously unselected package libjpeg-turbo8-dev:amd64.
Preparing to unpack .../36-libjpeg-turbo8-dev_2.1.2-0ubuntu1_amd64.deb ...
Unpacking libjpeg-turbo8-dev:amd64 (2.1.2-0ubuntu1) ...
Selecting previously unselected package libjpeg8-dev:amd64.
Preparing to unpack .../37-libjpeg8-dev_8c-2ubuntu10_amd64.deb ...
Unpacking libjpeg8-dev:amd64 (8c-2ubuntu10) ...
Selecting previously unselected package libjpeg-dev:amd64.
Preparing to unpack .../38-libjpeg-dev_8c-2ubuntu10_amd64.deb ...
Unpacking libjpeg-dev:amd64 (8c-2ubuntu10) ...
Selecting previously unselected package libltdl-dev:amd64.
Preparing to unpack .../39-libltdl-dev_2.4.6-15build2_amd64.deb ...
Unpacking libltdl-dev:amd64 (2.4.6-15build2) ...
Selecting previously unselected package libnuma-dev:amd64.
Preparing to unpack .../40-libnuma-dev_2.0.14-3ubuntu2_amd64.deb ...
Unpacking libnuma-dev:amd64 (2.0.14-3ubuntu2) ...
Selecting previously unselected package libhwloc-dev:amd64.
Preparing to unpack .../41-libhwloc-dev_2.7.0-2ubuntu1_amd64.deb ...
Unpacking libhwloc-dev:amd64 (2.7.0-2ubuntu1) ...
Selecting previously unselected package libpmix-dev:amd64.
Preparing to unpack .../42-libpmix-dev_4.1.2-2ubuntu1_amd64.deb ...
Unpacking libpmix-dev:amd64 (4.1.2-2ubuntu1) ...
Selecting previously unselected package libssl-dev:amd64.
Preparing to unpack .../43-libssl-dev_3.0.2-0ubuntu1.30_amd64.deb ...
Unpacking libssl-dev:amd64 (3.0.2-0ubuntu1.30) ...
Selecting previously unselected package libtool.
Preparing to unpack .../44-libtool_2.4.6-15build2_all.deb ...
Unpacking libtool (2.4.6-15build2) ...
Selecting previously unselected package libaec-dev:amd64.
Preparing to unpack .../45-libaec-dev_1.0.6-1_amd64.deb ...
Unpacking libaec-dev:amd64 (1.0.6-1) ...
Selecting previously unselected package libopenmpi-dev:amd64.
Preparing to unpack .../46-libopenmpi-dev_4.1.2-2ubuntu1_amd64.deb ...
Unpacking libopenmpi-dev:amd64 (4.1.2-2ubuntu1) ...
Selecting previously unselected package libhdf5-openmpi-dev.
Preparing to unpack .../47-libhdf5-openmpi-dev_1.10.7+repack-4ubuntu2_amd64.deb ...
Unpacking libhdf5-openmpi-dev (1.10.7+repack-4ubuntu2) ...
Setting up libjpeg-turbo8-dev:amd64 (2.1.2-0ubuntu1) ...
Setting up libucx0:amd64 (1.12.1~rc2-1) ...
Setting up libfftw3-single3:amd64 (3.3.8-2ubuntu8) ...
Setting up libcoarrays-dev:amd64 (2.9.2-3) ...
Setting up libaec-dev:amd64 (1.0.6-1) ...
Setting up libfftw3-long3:amd64 (3.3.8-2ubuntu8) ...
Setting up m4 (1.4.18-5ubuntu2) ...
Setting up libnuma-dev:amd64 (2.0.14-3ubuntu2) ...
Setting up libxnvctrl0:amd64 (570.207-0lambda1) ...
Setting up autotools-dev (20220109.1) ...
Setting up libfftw3-quad3:amd64 (3.3.8-2ubuntu8) ...
Setting up libssl-dev:amd64 (3.0.2-0ubuntu1.30) ...
Setting up libhwloc15:amd64 (2.7.0-2ubuntu1) ...
Setting up libevent-core-2.1-7:amd64 (2.1.12-stable-1ubuntu0.2) ...
Setting up libevent-2.1-7:amd64 (2.1.12-stable-1ubuntu0.2) ...
Setting up libfftw3-double3:amd64 (3.3.8-2ubuntu8) ...
Setting up autoconf (2.71-2) ...
Setting up openmpi-common (4.1.2-2ubuntu1) ...
Setting up libcurl4:amd64 (7.81.0-1ubuntu1.30) ...
Setting up curl (7.81.0-1ubuntu1.30) ...
Setting up libjpeg8-dev:amd64 (8c-2ubuntu10) ...
Setting up libevent-pthreads-2.1-7:amd64 (2.1.12-stable-1ubuntu0.2) ...
Setting up automake (1:1.16.5-1.3) ...
update-alternatives: using /usr/bin/automake-1.16 to provide /usr/bin/automake (automake) in auto mode
Setting up libevent-extra-2.1-7:amd64 (2.1.12-stable-1ubuntu0.2) ...
Setting up libtool (2.4.6-15build2) ...
Setting up libfftw3-bin (3.3.8-2ubuntu8) ...
Setting up libjpeg-dev:amd64 (8c-2ubuntu10) ...
Setting up libevent-openssl-2.1-7:amd64 (2.1.12-stable-1ubuntu0.2) ...
Setting up libhwloc-plugins:amd64 (2.7.0-2ubuntu1) ...
Setting up libltdl-dev:amd64 (2.4.6-15build2) ...
Setting up libcurl4-openssl-dev:amd64 (7.81.0-1ubuntu1.30) ...
Setting up libevent-dev (2.1.12-stable-1ubuntu0.2) ...
Setting up libhwloc-dev:amd64 (2.7.0-2ubuntu1) ...
Setting up libfftw3-dev:amd64 (3.3.8-2ubuntu8) ...
Setting up libpmix2:amd64 (4.1.2-2ubuntu1) ...
Setting up libopenmpi3:amd64 (4.1.2-2ubuntu1) ...
Setting up libcaf-openmpi-3:amd64 (2.9.2-3) ...
Setting up libpmix-dev:amd64 (4.1.2-2ubuntu1) ...
Setting up openmpi-bin (4.1.2-2ubuntu1) ...
update-alternatives: using /usr/bin/mpirun.openmpi to provide /usr/bin/mpirun (mpirun) in auto mode
update-alternatives: using /usr/bin/mpicc.openmpi to provide /usr/bin/mpicc (mpi) in auto mode
Setting up libhdf5-openmpi-103-1:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up libcoarrays-openmpi-dev:amd64 (2.9.2-3) ...
update-alternatives: using /usr/lib/x86_64-linux-gnu/open-coarrays/openmpi/bin/caf to provide /usr/bin/caf.openmpi (caf-openmpi) in auto mode
update-alternatives: using /usr/bin/caf.openmpi to provide /usr/bin/caf (caf) in auto mode
Setting up libhdf5-openmpi-fortran-102:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up libhdf5-openmpi-hl-100:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up libopenmpi-dev:amd64 (4.1.2-2ubuntu1) ...
update-alternatives: using /usr/lib/x86_64-linux-gnu/openmpi/include to provide /usr/include/x86_64-linux-gnu/mpi (mpi-x86_64-linux-gnu) in auto mode
Setting up libhdf5-openmpi-cpp-103-1:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up libhdf5-openmpi-hl-cpp-100:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up libhdf5-openmpi-hl-fortran-100:amd64 (1.10.7+repack-4ubuntu2) ...
Setting up libhdf5-openmpi-dev (1.10.7+repack-4ubuntu2) ...
update-alternatives: using /usr/bin/h5pcc.openmpi to provide /usr/bin/h5pcc (h5pcc) in auto mode
update-alternatives: using /usr/lib/x86_64-linux-gnu/pkgconfig/hdf5-openmpi.pc to provide /usr/lib/x86_64-linux-gnu/pkgconfig/hdf5.pc (hdf5.pc) in auto mode
update-alternatives: updating alternative /usr/bin/mpicc.openmpi because link group mpi has changed slave links
update-alternatives: using /usr/lib/x86_64-linux-gnu/pkgconfig/hdf5-mpi.pc to provide /usr/lib/x86_64-linux-gnu/pkgconfig/hdf5.pc (hdf5.pc) in auto mode
Processing triggers for man-db (2.10.2-1) ...
Processing triggers for install-info (6.8-4build1) ...
Processing triggers for libc-bin (2.35-0ubuntu3.10) ...

Running kernel seems to be up-to-date.

Services to be restarted:
 systemctl restart glances.service
 systemctl restart lambda-jupyter.service
 systemctl restart packagekit.service
 systemctl restart ssh.service
 systemctl restart systemd-journald.service
 /etc/needrestart/restart.d/systemd-manager
 systemctl restart systemd-networkd.service
 systemctl restart systemd-resolved.service
 systemctl restart systemd-udevd.service

Service restarts being deferred:
 systemctl restart systemd-logind.service
 systemctl restart user@1000.service

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
Installed package: libopenmpi-dev
libopenmpi-dev:amd64	4.1.2-2ubuntu1
Installed package: openmpi-bin
openmpi-bin	4.1.2-2ubuntu1
Installed package: libfftw3-dev
libfftw3-dev:amd64	3.3.8-2ubuntu8
Installed package: libfftw3-single3
libfftw3-single3:amd64	3.3.8-2ubuntu8
Installed package: libhdf5-openmpi-dev
libhdf5-openmpi-dev	1.10.7+repack-4ubuntu2
Cloning into 'baseline-published/pinder'...
HEAD is now at ebeb28a Migrate dataset hosting to R2 (#48)
Processing ./baseline-published/pinder
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Getting requirements to build wheel: started
  Getting requirements to build wheel: finished with status 'error'
  error: subprocess-exited-with-error
  
  × Getting requirements to build wheel did not run successfully.
  │ exit code: 1
  ╰─> [33 lines of output]
      Traceback (most recent call last):
        File "/tmp/m5-929bafad-0547-42d4-95e5-7844238cebb2/baseline-published/venv/lib/python3.10/site-packages/pip/_vendor/pep517/in_process/_in_process.py", line 363, in <module>
          main()
        File "/tmp/m5-929bafad-0547-42d4-95e5-7844238cebb2/baseline-published/venv/lib/python3.10/site-packages/pip/_vendor/pep517/in_process/_in_process.py", line 345, in main
          json_out['return_val'] = hook(**hook_input['kwargs'])
        File "/tmp/m5-929bafad-0547-42d4-95e5-7844238cebb2/baseline-published/venv/lib/python3.10/site-packages/pip/_vendor/pep517/in_process/_in_process.py", line 130, in get_requires_for_build_wheel
          return hook(config_settings)
        File "/usr/lib/python3/dist-packages/setuptools/build_meta.py", line 162, in get_requires_for_build_wheel
          return self._get_build_requires(
        File "/usr/lib/python3/dist-packages/setuptools/build_meta.py", line 143, in _get_build_requires
          self.run_setup()
        File "/usr/lib/python3/dist-packages/setuptools/build_meta.py", line 158, in run_setup
          exec(compile(code, __file__, 'exec'), locals())
        File "setup.py", line 1, in <module>
        File "/usr/lib/python3/dist-packages/setuptools/__init__.py", line 153, in setup
          return distutils.core.setup(**attrs)
        File "/usr/lib/python3/dist-packages/setuptools/_distutils/core.py", line 109, in setup
          _setup_distribution = dist = klass(attrs)
        File "/usr/lib/python3/dist-packages/setuptools/dist.py", line 459, in __init__
          _Distribution.__init__(
        File "/usr/lib/python3/dist-packages/setuptools/_distutils/dist.py", line 293, in __init__
          self.finalize_options()
        File "/usr/lib/python3/dist-packages/setuptools/dist.py", line 836, in finalize_options
          for ep in sorted(loaded, key=by_order):
        File "/usr/lib/python3/dist-packages/setuptools/dist.py", line 835, in <lambda>
          loaded = map(lambda e: e.load(), filtered)
        File "/usr/lib/python3/dist-packages/pkg_resources/__init__.py", line 2464, in load
          self.require(*args, **kwargs)
        File "/usr/lib/python3/dist-packages/pkg_resources/__init__.py", line 2487, in require
          items = working_set.resolve(reqs, env, installer, extras=self.extras)
        File "/usr/lib/python3/dist-packages/pkg_resources/__init__.py", line 782, in resolve
          raise VersionConflict(dist, req).with_context(dependent_req)
      pkg_resources.ContextualVersionConflict: (packaging 21.3 (/usr/lib/python3/dist-packages), Requirement.parse('packaging>=26.2'), {'vcs-versioning'})
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
error: subprocess-exited-with-error

× Getting requirements to build wheel did not run successfully.
│ exit code: 1
╰─> See above for output.

note: This error originates from a subprocess, and is likely not a problem with pip.