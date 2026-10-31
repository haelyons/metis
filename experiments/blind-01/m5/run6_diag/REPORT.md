# Run6 setup diagnosis

All three attempts stop while provisioning OpenMPI, before material acquisition. Both repairs received the complete decisive log. First repair changed dependency checks; second changed nothing. Primary next step: correct the pipeline's package-source evidence and installation constraint. Mirror reachability from the box remains untested.

Diagnosis used existing local records only. No workload, build, network fetch, or box contact occurred. Writes are confined to `run6_diag/`.

**1. Where each attempt fails**

| Attempt | Receipt | Failing operation | Decisive log |
| --- | --- | --- | --- |
| `0021-setup` | rc 1; 9 s; no timeout; fetched true | `sudo apt-get ... install` for missing OpenMPI, then explicit `exit 1` | `0021-setup.log:19–21` |
| `0039-setup` | rc 1; 10 s; no timeout; fetched true | New `apt-cache ... policy` candidate checks reject both OpenMPI packages, then explicit `exit 1`; install is never reached | `0039-setup.log:7–8` |
| `0057-setup` | rc 1; 10 s; no timeout; fetched true | Same candidate-check failure, unchanged script | `0057-setup.log:7–8` |

Attempt 1, [numbered log](../run6/agent/results/reproduce/0021-setup.log), lines 19–21:

```text
E: Package 'openmpi-bin' has no installation candidate
E: Package 'libopenmpi3' has no installation candidate
Required baseline dependencies unavailable from probe-authorized apt source.
```

Attempt 2, [numbered log](../run6/agent/results/reproduce/0039-setup.log), lines 7–8:

```text
Required baseline dependencies have no candidate in the probe-authorized apt source: openmpi-bin libopenmpi3
Cannot provision the published eight-rank OpenMPI baseline on this stock image under the supplied source restrictions. No alternate repository, installer, or baseline substitution is permitted.
```

Attempt 3, [numbered log](../run6/agent/results/reproduce/0057-setup.log), lines 7–8, repeats those two lines exactly.

All three logs first show successful `ls` checks for `/usr/bin/nvcc`, `/usr/include/cuda_runtime.h`, and `/usr/lib/x86_64-linux-gnu/libcudart.so`. CUDA path checks passed. They then show successful apt index retrieval from NVIDIA's container repository, followed by dependency failure. This is neither a material download failure nor a compiler/build failure.

In [attempt 1 setup](evidence/setup-0021.sh), line 33 adds `openmpi-bin libopenmpi3` when `command -v mpirun` fails; lines 38–42 restrict apt to the listed NVIDIA source and attempt installation. In [attempt 2 setup](evidence/setup-0039.sh), lines 38 and 44–59 perform the same missing-tool/source selection followed by candidate rejection. [Attempt 3 setup](evidence/setup-0057.sh) is byte-identical to attempt 2.

Receipts: [0021](../run6/control/receipts/0021-setup.json), [0039](../run6/control/receipts/0039-setup.json), [0057](../run6/control/receipts/0057-setup.json). Each budget was 1,200 seconds. [Reproduce stage](../run6/control/stages/reproduce.json) reports `FAIL`, `error_class: install`, consistent with the bounded setup failures.

**2. Same cause across attempts**

Yes. `mpirun` is unavailable on the script's executable search path, and the source permitted by the prompt supplies no candidate for either requested OpenMPI package. All scripts use a temporary source list containing only:

```text
deb [signed-by=/etc/apt/cloud-init.gpg.d/nvidia-docker-container.gpg] https://nvidia.github.io/libnvidia-container/stable/deb/amd64 /
```

Their apt options set `Dir::Etc::sourcelist` to that file and `Dir::Etc::sourceparts=-`, excluding the box's normal source configuration. First failure is installation failure; later failures detect the same unavailable dependencies before installation.

Published/intake baseline requires GNU MPI FroDock with eight ranks: [baseline.json](../run6/agent/intake/baseline.json), `build_commands.dockerfile_RUN_commands`, `run_commands.template_bindings.run`, and `published_configuration.mpi_np_default`; [EXECUTION.json](../run6/agent/intake/EXECUTION.json), `representative_scale.mpi_ranks_per_case`. Intake already recorded stock-image feasibility as unknown in [benchmark.json](../run6/agent/intake/benchmark.json), `stock_cuda_image.feasible: null`; intake passing did not establish dependency installability.

**3. What repairs saw and changed**

| Repair | Decisive error in supplied tail? | Changed failing part? |
| --- | --- | --- |
| `0003-harness-repair` | Yes. Prompt lines 77–97 contain all 21 lines of attempt 1; decisive lines at 95–97. | Yes. Added OpenMPI package-candidate checks and explicit policy failure before apt install; retained the same source restriction and dependencies. Also changed PATH, CUDA environment, venv detection, and added post-install `mpirun` verification. Did not make OpenMPI available. |
| `0004-harness-repair` | Yes. Prompt lines 77–84 contain all 8 lines of attempt 2; decisive lines at 83–84. | No. Reported no compliant repair and left `setup.sh` unchanged. |

Sources: repair 1 [prompt](../run6/agent/wf/agents/0003-harness-repair/prompt.md), [reply](../run6/agent/wf/agents/0003-harness-repair/reply.txt), and `codex-1.jsonl:107` recording its edit command; repair 2 [prompt](../run6/agent/wf/agents/0004-harness-repair/prompt.md), [reply](../run6/agent/wf/agents/0004-harness-repair/reply.txt), and its workflow commands. Both supplied tails were compared against their numbered logs and match in full, after trailing whitespace removal.

The [first-repair diff](evidence/repair-1.diff) shows actual changes. Status `repairs_targeted_cause: some` means one repair changed the failing dependency block; neither repaired dependency availability. It does not mean a repair succeeded.

Pipeline `runHarness` (`dut/pipeline/m5/pipeline.js:246–284`) takes the last 200 lines of the latest numbered operation log and includes the box probe in each prompt. It uploads and reruns after any non-null repair reply, even if setup is unchanged. That explains attempt 3. This record provides no evidence of log-tail loss.

Script reconstruction: attempt 1 recovered from repair 1's pre-edit concatenated `cat` output (`0003-harness-repair/codex-1.jsonl:37`); attempt 2 recovered from repair 2's pre-edit output (`0004-harness-repair/codex-1.jsonl:35`). In each, the complete setup script precedes the next script's shebang. Attempt 3 copied from final harness. Attempt 2 and final harness compare equal. [Provenance and SHA-256](evidence/setup-provenance.json) identify all three snapshots. Initial harness creation and subsequent pre-upload edits are also recorded at `0002-harness/codex-1.jsonl:123,136,184`.

**4. Mirror access from the box**

No attempt reached mirror acquisition. In attempt 1, `PYFETCH` starts at setup line 45, after the unconditional dependency-error exit on the observed path. In attempts 2/3, it starts at line 68, after the candidate-error exit at line 59. Fetching, archive extraction, material hash validation, Python installation, and docking were never reached. NVIDIA apt traffic in these logs is unrelated to the FroDock mirror.

The embedded manifests do name `https://storage.googleapis.com/gke-dja-demo_static_assets/frodock3_linux64.tgz`, size 26,637,000, SHA-256 `91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4`. These match [HASHES.tsv](../intake_mirror/HASHES.tsv) and [brief](../intake_mirror/BRIEF_run5.md), line 72. The fetch code would use a staged local archive if present, otherwise the inventory URL. Pipeline `uploadHarness` uploads scripts, not those archives.

Earlier successful reader-machine retrievals and intake availability claims establish no box-to-mirror result. Mirror response, reachability, and hash outcome **from the box are unknown**; observed execution status is `not_reached`.

**5. What can fix it**

Another harness repair with the same inputs and rules has no demonstrated compliant way to provision OpenMPI. Both prompts explicitly require apt only from listed sources, prohibit adding repositories, allow pip fallback only for cmake, and otherwise require clear failure. First repair exposed that blocker more clearly; second obeyed it.

The upstream issue is the package-source input/constraint combination. `dut/pipeline/m5/SCHEMAS.md:40` defines `apt_sources` as source files and lines **mentioning cuda or nvidia**. It is not a complete apt-source inventory. Yet `SCHEMAS.md:43` and `pipeline.js:230` restrict all missing-tool installation to those listed sources. The saved [probe](../run6/agent/results/probe/probe.json) and both repair prompts list only NVIDIA's container repository. Absence of Ubuntu repositories from that filtered record does **not** establish their absence from the actual box.

Recommended first remediation is outside this harness: correct pipeline probe/prompt inputs to inventory and authorize appropriate already-enabled distribution sources, including their actual enabled state. Then let setup check/install dependencies from that evidence without changing the baseline. This motivates `fix_needs: pipeline_repair_inputs`; the missing input is package-source evidence/authority, not the error tail.

Whether usable Ubuntu sources exist on this box is **unknown**. If corrected evidence shows none, source provisioning/policy or an image with the required runtime must change outside the current harness contract. A box-image change is an alternative, not an established necessity. These records do not implicate mirror bytes, material hashes, or brief authorization in the observed failure. The brief explicitly permits mirror use and leaves dependency resolution as later build work (lines 34–49, 63); run6's intake brief is byte-identical to it. Material changes or scientific-check changes are unsupported as remedies for this blocker. Successful dependency provisioning would only clear this early failure; later compatibility and workload behavior remain unknown.
