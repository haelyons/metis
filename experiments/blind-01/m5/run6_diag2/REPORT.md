# Run6: missing dependency and repair authority

Run6 setup cannot find OpenMPI's `mpirun` launcher. Requested runtime packages have no candidate in the only apt source exposed by the probe. Written rules prohibit other apt sources and permit pip fallback only for cmake. Repair therefore lacks **permission to use another dependency source**. Actual availability through an omitted source or compatible pip distribution remains **unknown**.

Diagnosis uses existing local records only. No workload, box contact, network fetch, installation, or pipeline change occurred. Writes confined to `run6_diag2/`.

## 1. What kind of tool is missing?

**MPI launcher/runtime; `tool_kind: other`.** Missing executable is `mpirun`; setup requests `openmpi-bin` and `libopenmpi3` when its executable lookup fails. See [original setup snapshot](../run6_diag/evidence/setup-0021.sh), lines 31–42, and [final setup](../run6/agent/harness/setup.sh), lines 36–66. Original snapshot matches the pre-edit setup recorded in [repair 1 transcript](../run6/agent/wf/agents/0003-harness-repair/codex-1.jsonl), line 37.

This is a baseline execution dependency. [Intake baseline](../run6/agent/intake/baseline.json), line 14, records the published OpenMPI package installation; lines 66–76 specify `mpirun -np {mpi_np} --use-hwthread-cpus`, GNU MPI FroDock, and eight ranks. No evidence identifies an archive, downloader, hash, build, CUDA, or Python-package tool as this blocker. CUDA path checks pass before the failure.

## 2. Could the box install it?

**From the listed source: no candidate for either requested package. By pip or another source: unknown. Overall `installable: unknown`.**

[Saved probe](../run6/agent/results/probe/probe.json), lines 2–9, lists only NVIDIA's `libnvidia-container/stable/deb/amd64` source. [First setup log](../run6/agent/results/reproduce/0021-setup.log), lines 19–21, reports:

```text
E: Package 'openmpi-bin' has no installation candidate
E: Package 'libopenmpi3' has no installation candidate
Required baseline dependencies unavailable from probe-authorized apt source.
```

[Second](../run6/agent/results/reproduce/0039-setup.log) and [third](../run6/agent/results/reproduce/0057-setup.log) logs, lines 7–8, repeat candidate rejection. Setup isolates apt using `Dir::Etc::sourcelist` plus `Dir::Etc::sourceparts=-`; final setup lines 44–59 show the restriction and candidate checks.

The probe reports pip's presence (lines 62–65), not any compatible OpenMPI distribution. Neither a successful pip route nor its impossibility is established. Likewise, no complete box apt-source inventory or candidate check against omitted distribution sources exists in these records. `apt_unlisted_source` would assert unverified availability; `not_installable` would overstate the observed failure.

## 3. Do the written rules allow the fix?

**No: `rules_allow_fix: no`.** [Pipeline `boxProbePrompt`](../../../../dut/pipeline/m5/pipeline.js), line 230, contains the blocking rule verbatim:

> If a required tool is missing, install it with apt only from sources the probe lists; do not add repositories or assume a package exists. Commented source lines are not enabled repositories. If apt cannot supply it, use pip for cmake only; otherwise fail with a clear message.

This exact rule reached the [initial harness prompt](../run6/agent/wf/agents/0002-harness/prompt.md), line 78, and both repair prompts ([repair 1](../run6/agent/wf/agents/0003-harness-repair/prompt.md), line 75; [repair 2](../run6/agent/wf/agents/0004-harness-repair/prompt.md), line 75). Even an already-enabled distribution source is unusable under this wording if absent from the probe. OpenMPI also falls outside the pip exception.

`harnessRules` at pipeline line 224 preserves baseline execution and measurement requirements. Initial harness generation includes those rules and `boxProbePrompt` at lines 305–312; repair generation includes both at lines 265–268. The installation restriction is explicit, not an ambiguous scientific requirement.

## 4. What did repair lack?

**`repair_lacked: permission`.** Repairs already knew the failing packages and received decisive logs. Repair 1 prompt lines 77–97 contain all 21 lines of attempt 1; repair 2 prompt lines 77–84 contain all eight lines of attempt 2. Pipeline lines 251–268 supply the latest 200-line tail and full probe. Log context was sufficient.

[Repair 1 reply](../run6/agent/wf/agents/0003-harness-repair/reply.txt), lines 2–5, identifies the source restriction and adds candidate checks. [Repair 2 reply](../run6/agent/wf/agents/0004-harness-repair/reply.txt), lines 2–5, identifies the same restriction and leaves setup unchanged. Neither demonstrates a permitted working installation that repair simply overlooked.

Probe evidence is incomplete too: [box_probe.sh](../../../../dut/pipeline/m5/box_probe.sh), lines 121–131, does not probe `mpirun`; lines 133–160 filter apt lines using `cuda|nvidia`. Thus the source array is not a complete inventory. Adding only `mpirun: null` would supply no new actionable fact after these logs. The operative missing input is installation authority beyond that filtered array; missing source facts prevent identifying a proven successful route.

## 5. Smallest pipeline change

**`smallest_fix: rules_permit_install`.** Change the installation clause in `boxProbePrompt` at `pipeline.js:230`, shared by harness generation and repairs. Permit setup to inspect and use already-enabled box apt sources for required baseline dependencies, after checking package candidates and origins. Keep the prohibition on adding or enabling repositories. Suggested replacement for the apt clause:

> For a missing baseline dependency, inspect the box's already-enabled apt sources, including distribution sources omitted from this CUDA/NVIDIA-focused probe. Verify package candidates and their origins before installing with apt from those sources. Do not add or enable repositories or assume package availability. If apt cannot supply it, use pip for cmake only; otherwise fail with a clear message.

Keep the existing cmake-only pip fallback. This single prompt change grants the missing permission and lets a repair collect the remaining source facts through setup. Merely naming another package in the probe cannot overcome the current restriction.

Preserve published pins, eight-rank configuration, stock image and torch, material hash checks, actual-output measurements, anchor scoring, timing, and evaluation checks. Dependency installation authority changes no scientific acceptance criterion.

This is the smallest change that removes the demonstrated policy blocker, **not proof that installation would succeed**. Whether suitable distribution sources are already enabled, and whether their packages satisfy the binary's runtime requirements, remain unknown. If none exists, further provisioning authority or a box-image change would be needed; these records do not establish which. A complete enabled-source probe is another possible improvement, but its success also depends on sources actually present.
