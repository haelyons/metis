# Run6 dependency install route

Missing dependency: OpenMPI launcher/runtime. Ubuntu 22.04 Jammy supplies `openmpi-bin` and `libopenmpi3` in **universe**. PyPI also supplies `openmpi`. Purpose: execute supplied MPI baseline, including its native shared-library dependencies. Targeted Ubuntu installation does not require changing baseline code, baseline configuration, or stock Python packages, including torch.

Important compatibility finding: supplied GNU MPI binaries request `libmpi.so.20` and `libmpi_cxx.so.20`; Jammy's `libopenmpi3` supplies `.40` libraries. Archive availability therefore establishes an install route for the missing launcher, **not a complete runtime fix for these prebuilt binaries**. Availability of compatible `.20` libraries on the box and a complete working installation remain **unknown**.

Read both prior [diagnosis 1](../run6_diag/REPORT.md) / [status](../run6_diag/status.json) and [diagnosis 2](../run6_diag2/REPORT.md) / [status](../run6_diag2/status.json). Existing [probe](../run6/agent/results/probe/probe.json), lines 55–60, identifies Ubuntu 22.04.5 LTS, Jammy. Missing-tool check appears in [setup.sh](../run6/agent/harness/setup.sh), line 38: absent `mpirun` adds `openmpi-bin libopenmpi3`. [First failure](../run6/agent/results/reproduce/0021-setup.log), lines 19–21, names both unavailable packages.

## 1. Ubuntu archive: `universe`

Checked package-index metadata on 2026-10-31; successful HTTP responses and retrieval times saved in [index-evidence.json](index-evidence.json).

| Index page | Result |
| --- | --- |
| [Jammy openmpi-bin](https://packages.ubuntu.com/jammy/openmpi-bin) | `openmpi-bin`, version `4.1.2-2ubuntu1`, **universe**; binary package, available for amd64. Depends on `libopenmpi3` and `openmpi-common`, among other native dependencies. |
| [Jammy libopenmpi3](https://packages.ubuntu.com/jammy/libopenmpi3) | `libopenmpi3`, version `4.1.2-2ubuntu1`, **universe**; shared-library package, available for amd64. Source package: `openmpi`. |
| [openmpi-bin amd64 file list](https://packages.ubuntu.com/jammy/amd64/openmpi-bin/filelist) | Includes `/usr/bin/mpirun.openmpi`, `/usr/bin/mpiexec.openmpi`, `/usr/bin/orterun`, and MPI compiler wrappers. |
| [libopenmpi3 amd64 file list](https://packages.ubuntu.com/jammy/amd64/libopenmpi3/filelist) | Includes `libmpi.so.40`, `libmpi_cxx.so.40`, and their versioned implementations. Does not list requested `.20` libraries. |

Permission must cover Ubuntu Jammy **universe**, beyond the NVIDIA container repository currently authorized. Narrow initial route: permit setup to inspect actual enabled Ubuntu sources, verify package origins/candidates, then install `openmpi-bin libopenmpi3` with apt and their required dependencies. Example intended package transaction: `apt-get install --no-install-recommends openmpi-bin libopenmpi3`. No transaction was run.

Actual box source configuration, universe enablement, apt resolution, and repository reachability remain **unknown**. Index availability does not establish these box facts. Existing probe lists only CUDA/NVIDIA-related source evidence; it cannot establish whether enabling a source would be necessary. If universe is absent, permission limited to already-enabled sources would still be insufficient.

## 2. PyPI: `yes`

[PyPI openmpi project](https://pypi.org/project/openmpi/) and [JSON API](https://pypi.org/pypi/openmpi/json) establish package `openmpi`, latest observed version `5.0.11`. Metadata lists a non-yanked `openmpi-5.0.11-py3-none-manylinux_2_28_x86_64.whl`; `requires_dist` is null. Release history also lists `4.1.7` and `4.1.8`. Saved response: [pypi-openmpi.json](pypi-openmpi.json).

PyPI presence does not establish compatibility with the supplied binaries or existing harness PATH. No wheel was downloaded or inspected. A pip fallback would need separate permission beyond current cmake-only exception. Native Ubuntu route already answers the launcher-install question; PyPI is not established as a drop-in fix.

Also checked [mpi4py-openmpi project](https://pypi.org/project/mpi4py-openmpi/) and [JSON API](https://pypi.org/pypi/mpi4py-openmpi/json); JSON endpoint returned HTTP 404. This does not negate availability under `openmpi`.

## 3. Purpose: `runtime_library`

OpenMPI supplies runtime infrastructure: `mpirun` launches ranks; MPI shared libraries support the already-built baseline processes. Missing executable itself is a launcher, while the requested dependency pair includes its native runtime library. `runtime_library` records this execution role.

Evidence:

- [run_command.sh](../run6/agent/harness/run_command.sh), lines 35–64, fixes eight ranks, resolves `mpirun`, and launches `frodockgrid_mpi_gcc` and `frodock_mpi_gcc` with `-np 8 --use-hwthread-cpus`.
- [baseline.json](../run6/agent/intake/baseline.json), lines 66–76, records published MPI launcher binding and GNU MPI implementation. Line 14 records OpenMPI in the published image recipe.
- [setup.sh](../run6/agent/harness/setup.sh), lines 68–110, uses Python `urllib.request`, `hashlib`, and `tarfile` for material fetching/checking/unpacking. OpenMPI performs none of those tasks. Lines 122–129 select supplied binaries and check their runtime libraries; compilation script is explicitly not run.
- Read cached, already-acquired archive as data, without executing or extracting binaries. Archive SHA-256 matches baseline pin: `91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4`. ELF `DT_NEEDED` entries for both MPI binaries include `libmpi_cxx.so.20` and `libmpi.so.20`. Member hashes match [earlier inspection](../intake_mirror/mirror_inspection.json). Details: [elf-evidence.json](elf-evidence.json).

Thus current harness installs a runtime dependency during setup; its role is not input acquisition or baseline compilation. Published source-build recipe also uses MPI, but current observed blocker precedes material acquisition and current harness uses prebuilt programs.

Jammy `.40` files do not satisfy `.20` dynamic-loader names by themselves. Existing box libraries might supply `.20`; probe does not say. Correct ABI provisioning or a separately justified rebuild would require further work. This diagnosis neither changes binaries nor claims a rebuild is required or authorized. PyPI compatibility with these exact ELF dependencies remains **unknown**.

## 4. Baseline and stock Python impact: `no`

For the obvious native route—targeted apt installation of `openmpi-bin libopenmpi3`—no baseline source edit, binary replacement, experiment-configuration edit, Python dependency resolution, or torch replacement is required. Package pages identify native binaries/shared libraries; their listed direct dependencies do not include Python or torch. Installation supplies OS files and OpenMPI's own configuration under `/etc/openmpi/`; that is separate from published baseline code/configuration.

The full setup has a separate Python installation step at [setup.sh](../run6/agent/harness/setup.sh), lines 112–121: venv with system site packages, stock torch version constraint, and PINDER installation. Its behavior is outside this missing-tool transaction. `changes_stock_python: no` describes installing OpenMPI by the native route, not a verified outcome of the entire unexecuted setup. Exact future apt transaction remains **unknown** until box candidates are inspected; no broad system upgrade is needed for the identified permission change.

PyPI `openmpi` would add a Python-managed distribution at the chosen installation location. Its metadata declares no Python distribution dependencies; adding it in isolation need not replace stock torch. No pip installation was attempted, and PyPI existence alone does not justify changing stock Python.

## Scope and evidence

Writes confined to `run6_diag3/`. No workload, package install, package/material download, box contact, commit, or push occurred. Network requests limited to package pages/file lists on `packages.ubuntu.com` and project pages/JSON metadata on `pypi.org`. No credential files, `.keys` files, or `~/.codex/` content read.

Saved Ubuntu HTML snapshots: [openmpi-bin](ubuntu-openmpi-bin.html), [libopenmpi3](ubuntu-libopenmpi3.html), [launcher file list](ubuntu-openmpi-bin-filelist.html), [library file list](ubuntu-libopenmpi3-filelist.html). [index-evidence.json](index-evidence.json) records URLs, successful response hashes/times, selected metadata, and the negative supplemental PyPI lookup. [status.json](status.json) contains only required enum values; its positive archive/PyPI answers describe availability, not successful baseline execution.
