**Run7 second setup diagnosis — owner record**

Two failures share one cause: setup assumes auxiliary files in local `harness/` were uploaded. Intervening failure rejects valid archive symlinks. None is a shell syntax error. Existing download cache already avoids repeated network acquisition. Smallest recovery change for run7: permit one additional setup repair. That can clear the observed blocker; records cannot establish that it will complete every remaining setup stage.

Read-only investigation used saved local records. No setup, build, scientific workload, package installation, network fetch, box contact, commit, or push. Writes confined to `run7_diag2/`. Archived content inspected as data, without extraction or execution. Only script parsing ran: `bash -n` and Python AST parsing. No credentials or `.keys` files read.

**1. Error stopping each attempt.**

| Attempt | Decisive logged line | Kind | Cause |
| --- | --- | --- | --- |
| 1, `0004-setup`, 56 s | `FileNotFoundError: [Errno 2] No such file or directory: 'harness/pinder-source.tar.gz'` | `wrong_path` | Script assumes local source bundle exists remotely. |
| 2, `0006-setup`, 376 s | `RuntimeError: Unsafe FroDock archive` | `control_flow` | Incorrect validation predicate rejects all symbolic links, including required links contained within archive tree. |
| 3, `0008-setup`, 35 s | `FileNotFoundError: [Errno 2] No such file or directory: 'harness/data.json'` | `wrong_path` | Script assumes local inventory sidecar exists remotely. |

Sources: [attempt 1 log](../run7/agent/results/reproduce/0004-setup.log), line 399; [attempt 2 log](../run7/agent/results/reproduce/0006-setup.log), lines 9–10; [attempt 3 log](../run7/agent/results/reproduce/0008-setup.log), lines 5–6. Durations also appear in repair prompts for first two attempts and prior [diagnosis](../run7_diag/REPORT.md) for all three.

Attempt 1 fails at [reconstructed setup](evidence/setup-0004.sh), line 49:

```python
if hashlib.sha256(pathlib.Path('harness/pinder-source.tar.gz').read_bytes()).hexdigest()!='5b2e0227f14cd54fa8462e44c5d8c1d857afb7f10071ad2b323e918fe3b2421a':
```

`read_bytes()` fails before hash comparison. First repair replaces local bundle assumptions with pinned, hash-checked downloads; see [repair 1 diff](evidence/repair-1.diff).

Attempt 2 fails at [reconstructed setup](evidence/setup-0006.sh), line 95:

```python
if '..' in pathlib.PurePosixPath(m.name).parts or m.name.startswith('/') or m.issym() or m.islnk(): raise RuntimeError('Unsafe FroDock archive')
```

Pinned archive contains `frodock3_linux64/includes/tclap -> ../src/tclap` and `frodock3_linux64/includes/cmdl -> ../src/cmdl`. Both links remain inside FroDock tree. First offending member is `includes/tclap`. Local archive SHA-256 equals logged verified digest. Thus `control_flow` means erroneous **test logic**, as allowed by requested vocabulary; neither tar command misuse nor syntax failure. Second repair permits contained symlinks while retaining traversal, member-type, and link-target restrictions; see [repair 2 diff](evidence/repair-2.diff) and [archive checks](evidence/checks.json).

Attempt 3 fails at [final setup](evidence/setup-0008.sh), line 112:

```python
items=json.load(open('harness/data.json'))['inventory']
```

[pipeline.js](../../../../dut/pipeline/m5/pipeline.js), lines 336–337, uploads only `setup.sh`, `run_anchors.sh`, `run_command.sh`, and optional `run_evaluation.sh`. Repair uploads only permitted scripts, lines 259 and 281. Local archives and JSON sidecars never enter that transfer set. `wrong_path` covers these assumed paths; files need not have misspelled names to qualify.

**2. Distinctness: `some_repeat`.**

Attempts 1 and 3 repeat same missing-auxiliary-upload assumption, with different filenames. Attempt 2 has different cause: false-positive archive rejection. All three defects already existed in initial setup: missing source read at line 49, blanket link rejection at line 69, missing inventory read at line 73. Repairs exposed latent defects; neither introduced the next failure. Initial harness record explicitly copies source and JSON sidecars into local `harness/` (`0002-harness/codex-1.jsonl:357`), but pipeline transfers scripts only.

**3. Static catch: `none`.**

`bash -n` passes on all three reconstructed scripts. All nine embedded Python blocks also parse with `ast.parse`, without execution. [Check results](evidence/checks.json) record exact script hashes and parsing outcomes. Historical workflow independently records successful shell checks after generation (`0002-harness/codex-1.jsonl:475`), repair 1 (`0003-harness-repair/codex-1.jsonl:102`), and repair 2 (`0004-harness-repair/codex-1.jsonl:117`).

ShellCheck at error severity would not diagnose these three causes: decisive paths and predicate are inside quoted Python heredocs. ShellCheck does not evaluate Python filesystem accesses, remote upload membership, or tar member semantics. ShellCheck unavailable locally; none fetched. This conclusion concerns catchability of observed defects, not an invented ShellCheck execution result. A custom transfer-manifest audit or archive fixture check could catch them, but neither is `bash -n` or ordinary ShellCheck.

**4. Rule-induced: `no`.**

No read pipeline rule or brief instruction requires unuploaded sidecars or blanket symlink rejection. Relevant actual harness instruction says:

> Write three self-contained bash scripts, invoked from a shared remote working directory with bash harness/&lt;name&gt;:

Source: [harness prompt](../run7/agent/wf/agents/0002-harness/prompt.md), line 144; pipeline line 311. Initial scripts violate self-containment. Prompt does not enumerate transferred files, which leaves a useful contract clarification opportunity; omission differs from a rule directing the erroneous implementation.

Other relevant requirements remain compatible with correcting these errors:

> A setup repair may change only setup.sh;

> Make setup safe to retry once in this directory.

Sources: harness prompt lines 4 and 145; `harnessRules` at pipeline line 224 and generation prompt at line 312. Setup-only repair can embed exact inventory and materialize it at runtime; no expanded edit authority needed. Retry requirement explains caching, not either missing path. Blanket symlink ban is author-written guard, absent from prompts and brief.

Brief requires:

> Keep all scientific checks unchanged.

Source: [intake brief](../run7/agent/intake/brief.md), line 38. Hash checks do not require rejecting contained symlinks, and permission to use mirror does not establish original-study byte identity. Neither issue requires relaxing provenance, hashes, protocol, anchors, or tolerances. `boxProbePrompt` at pipeline line 230 permits needed apt installation from reported enabled sources; that rule did not cause these three Python failures.

**5. Re-run refetching: `no` for previously verified cached downloads; hash checks repeat.**

Pipeline re-invokes whole `setup.sh` in same remote directory (`remoteDirectory`, line 153; `runHarness`, lines 246–284). Setup begins with `mkdir -p`, not cache removal. Repair 1 adds cache under `baseline-published/downloads/`. Both repaired versions use:

```python
if p.is_file() and digest(p)==expected: return p
```

Source: final setup line 58. Existing archive bytes are rehashed, then reused; missing or mismatching archive is downloaded and checked. Download paths do not blindly trust prior verification. Attempt 2 logs two `Downloading` and two `Verified` lines; attempt 3 logs neither and reaches inventory read after both acquisition calls, extraction, and `soap.bin` hash. Thus attempt 3 reused cached archives after digest checks. Attempt 2's fetches were first acquisition of these archives on box, not repeated successful fetches from attempt 1.

Release-file downloader similarly uses `if p.exists() and digest(p)==x['sha256']: return` (final setup line 119), so future retries reuse matching release files and rehash them. No attempt reached release downloads; their actual box acquisition remains unestablished. Apt skips already-installed packages. Extraction and later build loop still rerun. Enum `no` describes **refetching verified bytes**, not skipping hashes or skipping entire setup.

**6. Third-fix outlook: `unknown`.**

Supplying exact missing inventory clears observed exception. Remaining script then does:

| Remaining step | Static evidence | Execution evidence |
| --- | --- | --- |
| Release downloads and per-file SHA-256 checks | Filter selects 3,596 inventory entries; cached matches reused | Never reached |
| Fourteen GNU make targets | Every target directory/makefile exists in local pinned archive; all explicit source paths inspected in selected `subdir.mk` files exist | Never reached |
| Executable and shared-library checks | Expected output names agree with makefiles; missing libraries cause failure | Never reached |
| Venv, stock-torch constraint, pip install | Source root has installable project metadata and matching package layout | Never reached |
| Paired-apo preparation | Pinned `prepare_inference_inputs` accepts `ids` and `pairs` and returns dictionaries containing `id` | Never reached |

Evidence: final setup lines 113–179, [checks](evidence/checks.json), [project metadata](evidence/pinder-pyproject.toml), [preparation API](evidence/pinder-preprocess.py.txt). Odd spellings `libfrodockcluster/Relase_gcc` and `frodockgrid/Release_MPI_GCC` are actual archive directories, not further demonstrated wrong-path errors.

No additional definite setup defect found by this audit. Conversely, archive presence and parseability do not establish compiler compatibility, native link success, dependency resolution, successful preparation, or completion within 1,200 s. Intake itself records unresolved dependency environment in `baseline.json`. Evidence supports neither a confident likely-pass forecast nor a specific likely-next-error forecast. Therefore `unknown`, rather than treating absence of executed failure as successful setup. No scientific success follows from a future setup pass.

Unuploaded `harness/EXECUTION.json` and `harness/anchors.json` are **known later-run blockers** if left absent: `run_command.sh:31`, `run_anchors.sh:24,62`. They are outside remaining setup path and do not establish another setup failure. Setup can materialize exact copies together with inventory while editing only `setup.sh`.

**7. Smallest recovery unit: `more_repairs`; full sufficiency remains unproven.**

Permit one additional **setup-only** repair: three repairs/four possible attempts, retaining two anchors repairs. `runHarness` currently caps both operations at two (pipeline line 249); repair prompt also names that bound (line 265). Changing setup bound and matching count text is small pipeline recovery change. It leaves every pass criterion intact.

Additional repair can embed exact intake inventory in `setup.sh`, materialize `harness/data.json`, and preserve existing URL selection, every digest, source pin, build, and input preparation. Chunked uploader already handles large script bodies (pipeline lines 202–222); inventory is 1,691,796 bytes, so embedding requires no new auxiliary-upload mechanism. Materializing unchanged execution/anchor sidecars also prevents known later missing-file failures.

Reasons for selecting this unit over alternatives:

- **Static check before upload:** all observed failures survive shell syntax checks; these checks already ran.
- **Harness prompt rule:** explicit transfer manifest would help prevent recurrence in new harnesses, but existing instruction already requires self-containment. New generation guidance alone does not provide an additional repair invocation after exhausted bound.
- **Other repair context:** both earlier tails contain decisive failure exactly. Local comparison confirms supplied last 200 lines for repair 1 and all ten lines for repair 2. Replies diagnose correct causes and diffs target them. Third failure likewise fits six-line log; truncation is no blocker. Existing repair instructions permit using intake evidence and reading other scripts.
- **Split fetch-and-verify from setup:** larger change; current verified cache already avoids repeat downloads. Splitting cannot itself supply missing inventory or correct archive predicate. Removing repeated digest checks would weaken existing integrity behavior and is unnecessary.

Among listed units, extra setup repair is smallest change most directly supported for trying to complete run7 setup: both previous repairs worked, current cause fits existing repair scope and context, and no specific further setup defect was found. This is a comparative recommendation, not proof that one extra repair will get setup fully through. If decision requires established sufficiency for full setup completion, answer remains **unknown** until remaining stages execute. This report changes neither pipeline nor retry allowance.

**Evidence provenance.** [inspect.py](inspect.py) independently reconstructs earlier setup versions by reversing completed setup changes from repair workflow records (`0003-harness-repair/codex-1.jsonl:99`, `0004-harness-repair/codex-1.jsonl:114`). Full reconstructed pre-repair versions exactly match script snapshots printed at respective records' lines 37 and 38. Attempt 1 also matches original harness creation at record line 357 after applying recorded final edit at line 472. All three copies match previous diagnosis evidence; final copy matches current harness. [checks.json](evidence/checks.json) preserves hashes, reconstruction references, exact repair-tail comparisons, and static archive-path checks. Original records and scripts unchanged.
