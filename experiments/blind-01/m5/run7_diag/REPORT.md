# Run7 setup diagnosis

Run6's OpenMPI installation blocker was cleared. Run7 then exposed three setup-script defects: an assumed uploaded source archive, rejection of valid archive symlinks, and an assumed uploaded inventory JSON. Both repairs received and changed their decisive failure. Second repair made progress; shorter third attempt reflects reuse of verified downloads, with exact time breakdown unknown. A further self-contained setup repair could plausibly clear the current blocker.

Diagnosis used saved local records only. No box contact, network fetch, package installation, build, or workload execution. Writes confined to `run7_diag/`; original scripts unchanged. Local archives were read as data, without extraction or binary execution.

## 1. Failure point of each attempt

| Attempt | Receipt | Failure | Classification |
| --- | --- | --- | --- |
| 1 | `0004-setup`: rc 1, 56 s | Reads `harness/pinder-source.tar.gz`, absent from remote upload | `script_error` |
| 2 | `0006-setup`: rc 1, 376 s | Archive validator rejects required internal FroDock symlink | `script_error` |
| 3 | `0008-setup`: rc 1, 35 s | Reads `harness/data.json`, absent from remote upload | `script_error` |

All receipts have `timed_out:false`, `overrun:false`, `fetched:true`, budget 1,200 s: [attempt 1](../run7/control/receipts/0004-setup.json), [attempt 2](../run7/control/receipts/0006-setup.json), [attempt 3](../run7/control/receipts/0008-setup.json). Every numbered setup log starts with successful checks of `/usr/bin/nvcc`, `/usr/include/cuda_runtime.h`, and `/usr/lib/x86_64-linux-gnu/libcudart.so`.

Attempt 1, [log](../run7/agent/results/reproduce/0004-setup.log), lines 393–399:

```text
  File "<stdin>", line 5, in <module>
...
FileNotFoundError: [Errno 2] No such file or directory: 'harness/pinder-source.tar.gz'
```

Failing expression: [reconstructed setup](evidence/setup-0004.sh), line 49, calls `read_bytes()` before computing the source archive hash. No hash mismatch occurred; file was unavailable.

Attempt 2, [log](../run7/agent/results/reproduce/0006-setup.log), lines 8–10:

```text
Traceback (most recent call last):
  File "<stdin>", line 51, in <module>
RuntimeError: Unsafe FroDock archive
```

Failing predicate: [reconstructed setup](evidence/setup-0006.sh), line 95, rejects **every** symbolic link and hard link. Cached archive, whose SHA-256 matches the box's verified download, contains two symbolic links: `frodock3_linux64/includes/tclap -> ../src/tclap` and `frodock3_linux64/includes/cmdl -> ../src/cmdl`. First offending member is `includes/tclap`; both targets remain inside FroDock's tree. Archive metadata has 445 files, 95 directories, two symlinks, and no other member types. Evidence: [record checks](evidence/record-checks.json), plus second-repair workflow record `codex-1.jsonl:45`. This was a validator defect, not an observed download, checksum, or build failure.

Attempt 3, [log](../run7/agent/results/reproduce/0008-setup.log), lines 4–6:

```text
Traceback (most recent call last):
  File "<stdin>", line 68, in <module>
FileNotFoundError: [Errno 2] No such file or directory: 'harness/data.json'
```

Failing expression: [final setup copy](evidence/setup-0008.sh), line 112, `json.load(open('harness/data.json'))['inventory']`. This inventory drives subsequent release downloads and individual-file hashes.

Underlying upload contract explains attempts 1 and 3. [pipeline.js](../../../../dut/pipeline/m5/pipeline.js), lines 195–216 and 336–337, uploads only `setup.sh`, `run_anchors.sh`, `run_command.sh`, and optional `run_evaluation.sh`. Repairs upload only permitted rewritten scripts, lines 263 and 291. Locally copied archives, `data.json`, `EXECUTION.json`, and `anchors.json` are not included. All three script uploads succeeded; this is not a failed upload batch. [SCHEMAS.md](../../../../dut/pipeline/m5/SCHEMAS.md), lines 46–62, describes the same script upload/repair contract.

[Reproduce receipt](../run7/control/stages/reproduce.json) reports `error_class:install` because pipeline lines 339–346 map any nonzero completed setup to that coarse class. It does not establish an apt failure.

## 2. Run6 library: installed through enabled Ubuntu apt sources

**Yes: `libopenmpi3` and `openmpi-bin`, version `4.1.2-2ubuntu1`, installed by apt in attempt 1.** Requested `libopenmpi-dev` pulled runtime and launcher dependencies; explicit `openmpi-bin` step subsequently found it installed.

Decisive [attempt-1 log](../run7/agent/results/reproduce/0004-setup.log) lines:

```text
57: libopenmpi-dev:
59:   Candidate: 4.1.2-2ubuntu1
62:         500 http://archive.ubuntu.com/ubuntu jammy/universe amd64 Packages
63: Installing libopenmpi-dev
109: Get:12 http://archive.ubuntu.com/ubuntu jammy/universe amd64 libopenmpi3 amd64 4.1.2-2ubuntu1 [2594 kB]
242: Setting up libopenmpi3:amd64 (4.1.2-2ubuntu1) ...
245: Setting up openmpi-bin (4.1.2-2ubuntu1) ...
246: update-alternatives: using /usr/bin/mpirun.openmpi to provide /usr/bin/mpirun (mpirun) in auto mode
266: libopenmpi-dev:amd64	4.1.2-2ubuntu1
289: openmpi-bin	4.1.2-2ubuntu1
```

Last two excerpts show tab-separated `dpkg-query -W` results; `\t` above denotes a tab. `libopenmpi3` was a transitive dependency, so no separate `dpkg-query -W libopenmpi3` line exists; its download and successful configuration are explicit.

[Probe](../run7/agent/results/probe/probe.json) lists `deb http://archive.ubuntu.com/ubuntu jammy universe` under `apt_enabled_sources`; older filtered `apt_sources` still contains only NVIDIA's container source. Setup lines 26–42 run normal `sudo apt-get update`, check candidates with `apt-cache policy`, install, and print queried versions. No added repository or pip OpenMPI route was needed. This follows revised `boxProbePrompt` at pipeline lines 228–230 and schema lines 40–44.

Installation does not prove every supplied executable can run. [Run6 diagnosis 3](../run6_diag3/REPORT.md) found prebuilt executables requesting MPI `.20` libraries while Jammy supplies `.40`. Run7 plans a source rebuild and subsequent `ldd` checks, but never reaches them. Full MPI ABI/build compatibility remains **unknown**. Apt also logged removal of `doca-ofed`, `hcoll`, `sharp`, and `ucx`; these removals did not terminate this transaction. Their later effects remain untested.

## 3. Furthest phase

**Hash checking and material unpacking, before release-inventory downloads or build.** Attempt 3 reached its inventory read after FroDock extraction and the individual `bin/soap.bin` hash check.

| Step | Attempt 1 | Attempt 2 | Attempt 3 |
| --- | --- | --- | --- |
| CUDA path checks | Passed | Passed | Passed |
| Required apt dependency stage | Completed installs | Passed with installed packages | Passed with installed packages |
| PINDER source acquisition/hash/extraction | Missing local path | Downloaded, verified, extracted | Verified cache reused, extracted |
| FroDock mirror archive hash | Not reached | Passed after box download | Verified cache reused |
| FroDock extraction | Not reached | Validator rejected symlink | Completed |
| `soap.bin` SHA-256 | Not reached | Not reached | Passed, inferred from reaching next statement |
| Load release inventory | Not reached | Not reached | Missing `harness/data.json` |
| Release-file downloads and per-file hashes | Not reached | Not reached | Not reached |
| GNU build, binary/ABI checks, Python install, input preparation | Not reached | Not reached | Not reached |
| Smoke or anchors | Not reached | Not reached | Not reached |

Final setup lines 110–112 hash `soap.bin` before opening the missing JSON; no branch bypasses that hash. Release-file pool starts at line 133, GNU build at line 138, venv/Python installation at line 155, and input preparation at line 165. `set -euo pipefail` stops after Python's exception. No `Verified release payloads:` line, build output, smoke receipt, anchor receipt, or measured anchor result exists.

`furthest_phase:hash_check` records completed archive/scoring-file checks, **not completion of the inventory's per-file checks**.

## 4. Second repair did not regress working behavior

**No regression established; code and execution show forward progress.** [Second-repair diff](evidence/repair-2.diff) changes only FroDock member validation, allowing contained symbolic links while retaining path/type restrictions. Downloader, cache checks, source extraction, hashes, and inventory read are unchanged. Third attempt passes previously failing validation and reaches a later statement.

Missing `harness/data.json` is latent in every version: attempt-1 line 73, attempt-2 line 99, attempt-3 line 112. Neither earlier attempt reached it.

Third attempt prints no `Downloading` or `Verified` messages. Final setup lines 56–58 silently return cached archives only after recomputing and matching their digests. Reaching line 112 therefore establishes successful cache reuse, accounting for avoided downloads. First attempt also left packages installed. Receipts provide aggregate elapsed times only; network/extraction/polling contributions to 376 s versus 35 s are **unknown**. Duration alone cannot diagnose a regression.

## 5. Repair inputs and targeting

| Repair | Decisive cause in supplied tail? | Changed failing part? | Result |
| --- | --- | --- | --- |
| `0003-harness-repair` | Yes: prompt line 341 has missing source archive; supplied tail exactly matches last 200 lines of attempt 1 | Yes: replaces local archive assumptions with pinned, SHA-verified downloads and reusable cache | Both archives downloaded and verified; next validator defect exposed |
| `0004-harness-repair` | Yes: prompt line 151 has unsafe-archive exception; supplied tail equals all ten lines of attempt 2 | Yes: replaces blanket symlink rejection with contained-link validation | Extraction and scoring-file hash pass; missing inventory exposed |

Sources: first repair [prompt](../run7/agent/wf/agents/0003-harness-repair/prompt.md), [reply](../run7/agent/wf/agents/0003-harness-repair/reply.txt), `codex-1.jsonl:99`; second repair [prompt](../run7/agent/wf/agents/0004-harness-repair/prompt.md), [reply](../run7/agent/wf/agents/0004-harness-repair/reply.txt), `codex-1.jsonl:114`. Both replies identify the correct immediate cause. First reply's phrase “Git fetch” describes an HTTPS source archive download; recorded code uses `urllib.request`, not `git clone`.

Tail truncation did not hide either decisive error. Neither repair was given attempt 3's missing-inventory exception: it arose after the final permitted repair. First repair fixed archives but left the analogous inventory-upload assumption. Second repair fixed its reported validator failure but did not anticipate the inventory failure.

## 6. Box mirror access and hashes

**Box reached mirror successfully in attempt 2.** [Numbered box setup log](../run7/agent/results/reproduce/0006-setup.log), lines 4–7:

```text
Downloading https://codeload.github.com/pinder-org/pinder/tar.gz/ebeb28a2f8411363cef722b7d293c978f7442672
Verified pinder-source.tar.gz sha256:b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd
Downloading https://storage.googleapis.com/gke-dja-demo_static_assets/frodock3_linux64.tgz
Verified frodock.tar.gz sha256:91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4
```

`Verified` prints only after streamed download completes, SHA-256 matches, and temporary file is renamed. This is box execution evidence, independent of the harness author's local mirror fetch. Attempt 1 never reaches mirror acquisition. Attempt 3 reuses the checked cache; it need not contact mirror again.

**Every executed hash check passed; full inventory verification did not run.** Attempt 2 verifies both archives. Attempt 3 rechecks both cached archive hashes and passes `soap.bin` digest `791f31ec8ef1ef1466092b425638e926755519c9626f5678ca675ef6c76234fc`. No log or control flow shows a checksum mismatch. `hash_checks:all_passed` in status refers to these executed checks; it does **not** assert all planned release-file checks passed. Those checks were never reached, and downloaded-release completeness remains unestablished.

[Intake brief](../run7/agent/intake/brief.md) exactly matches [named brief](../intake_mirror/BRIEF_run5.md). All 3,602 intake inventory URL/hash pairs match [HASHES.tsv](../intake_mirror/HASHES.tsv); setup selects 3,596 non-ZIP release entries. Historical matching refetch records in that TSV are reader-machine evidence, not run7 box release downloads. Local verification summary: [record-checks.json](evidence/record-checks.json).

Initial script expects locally repacked source archive hash `5b2e0227f14cd54fa8462e44c5d8c1d857afb7f10071ad2b323e918fe3b2421a`; repaired scripts fetch official commit archive with recorded hash `b5775328…b76dd`. This is an intentional acquisition-route change recorded in repair 1, not an observed checksum mismatch. Source commit remains `ebeb28a2f8411363cef722b7d293c978f7442672`.

Mirror hashes identify authorized mirror bytes only. Original-study identity remains unverified, as brief requires. No scientific validity, docking accuracy, or anchor outcome follows from these setup hashes.

## 7. Plausible fix and remaining limits

**`fix_needs:harness_repair`.** Current missing inventory can plausibly be fixed entirely within `setup.sh`: embed exact intake inventory as script data, materialize it at runtime, then run existing pinned downloads and hash checks. This needs no changed scientific protocol, material replacement, repository authorization, or box-image change. Chunked uploader can carry a larger self-contained script.

Repair should also account for unchanged runners' unuploaded sidecars: `run_command.sh:31` reads `harness/EXECUTION.json`; `run_anchors.sh:24` reads that file and line 62 reads `harness/anchors.json`. Setup can materialize exact copies from embedded intake data while its local repair still edits only `setup.sh`. Otherwise setup could succeed and a later runner fail on the same upload assumption.

Pipeline improvement would make upload manifest explicit in harness and repair prompts, or support declared auxiliary uploads. Existing prompts do not enumerate transferred files; authors can see local sidecars and wrongly assume remote availability. That is a useful contract improvement, **not missing decisive log context or a necessary rule change for the immediate fix**. Both repair tails were sufficient; current apt authority worked. No evidence requires new mirror, brief, or image to clear observed failures.

`runHarness` permits two repairs and has exhausted them. A further repair therefore needs a new authorized invocation/reuse or changed retry allowance; this diagnosis changes neither. Plausible harness fix is not proof of eventual success: release downloads, GNU compilation, MPI compatibility, Python dependency resolution, input preparation, smoke, and anchors remain untested. Any later independent blocker is **unknown**.

## Reconstruction and verification

[reconstruct.py](reconstruct.py) reverses completed workflow patches from final setup, saving all three versions and both diffs under [evidence/](evidence/). Reconstructed attempts 1 and 2 exactly match full pre-repair script text printed in respective repair records (`0003-harness-repair/codex-1.jsonl:37`, `0004-harness-repair/codex-1.jsonl:38`). Final copy equals current harness setup. [Provenance](evidence/provenance.json) records source lines, SHA-256 values, and exact supplied-tail comparisons, preserving CR characters for the pipeline's newline-based tail logic.

[inspect_records.py](inspect_records.py) compares intake inventory to saved TSV and reads cached FroDock member metadata/scoring bytes. It performs no extraction, build, execution of archived content, or network access. Enum status was checked for exactly the requested keys and allowed values.
