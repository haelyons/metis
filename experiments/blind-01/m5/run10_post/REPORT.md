Run10 post-check — 2026-11-02

Equivalence is nonvacuous: all 200 compared files contain bytes and match run9. Prediction 6 falls in `0_7_to_1_3`. Subset log contains errors despite exit 0. Shared data has conditional write paths; actual outside-out writes during the measured invocation are not established. No concurrent execution or write trace exists here, so concurrency safety is not certified.

Scope: read retained records and selected source only. No workloads, harness execution, box contact, network, git commands, credentials, `.keys`, or `~/.codex/` reads. Authored files remain under `run10_post/`. `audit.py` uses standard library to compare recorded files, count log markers, verify source archive hashes, and preserve three selected source members. It imports no workload package. `audit.json` records every compared path, byte count, equality and hash. Existing launcher files in this directory were untouched.

References below are relative to experiment directory unless absolute. Log references count LF bytes; embedded CR progress updates do not introduce new lines. `U` means `run10/agent/harness/run_units.sh`; `L` means `run10/agent/results/reproduce/units-check/run.log`; `C` means `run10/agent/results/reproduce/units_check.json`. `SCHEMAS` means `/home/hal/dev/interp/metis/dut/pipeline/m5/SCHEMAS.md`.

**A. Files and log**

Independently read both sides of every manifest-listed output for sample indices 3, 5, 9, 15. Results: **200/200 byte-identical; 200/200 nonempty on each side; 83,417,850 bytes per side; minimum 303,507 bytes, maximum 511,758 bytes**. `audit.json:2–8` records totals; its `files` rows record individual paths and sizes. Selection comes from `C:2–19`; manifest entries begin at `run10/agent/harness/units.json:172,284,508,844`. Selected original CSV records survive in `run10/agent/results/reproduce/units-check/files/results/frodock_setup.csv:2–5`.

| Unit, apo | Files | Bytes per file | Bytes per side |
| --- | ---: | ---: | ---: |
| 1aua | 50 | 384,831 | 19,241,550 |
| 1ax2 | 50 | 303,507 | 15,175,350 |
| 1dv1 | 50 | 511,758 | 25,587,900 |
| 1nr5 | 50 | 468,261 | 23,413,050 |

Compared paths are final PDBs under `results/frodock/<system>/<kind>_decoys/model_<rank>.pdb`, beneath subset `files/` and run9 `results/reproduce/out/`. Nonempty/equal proves this comparison has content. It does not establish physical accuracy or absence of inherited execution defects.

`subset_log_problems=errors`. Evidence:

- Four Python logging failures: `L:9–38`, then :703, :1397, :2075. `TypeError: not all arguments converted during string formatting` comes from `log.info("OUT", output_dir)`; logging catches it and computation continues. Original adapter line 56 is preserved in `run10_review3/evidence/predict.py.txt`.
- Eight MPI job abort diagnostics with nonzero status: first two at `L:45–55,62–72`; remaining markers :741,758,1435,1452,2113,2130. First reported exit code is 1. Files were emitted before these diagnostics (:44,61). Cause and numerical consequences of these native return statuses are not established by this audit.
- Twenty-four native warnings, “Ligand should be smaller than Receptor”, starting `L:228`; four Biotite element-guess warnings at :699,1393,2071,2765.
- Eighteen evaluator ERROR records about missing systems: first :2771, last group :7811–7819. These reflect evaluating a restricted result set against benchmark populations. Wrapper deliberately answers `yes y` to missing-system confirmations (`U:208–216`); this is inherited behavior.

Nevertheless `PREDICT_EXIT=0` at `L:2769`, `EVAL_EXIT=0` at :7820, and `subset_rc=0` at `C:20`. Adapter calls `subprocess.run(cmd, shell=True)` without `check=True` or inspecting return code (`run10_review3/evidence/predict.py.txt:126–137`, unchanged by applied patch). Thus published prediction success is not a successful-native-stage check. Byte equivalence reproduces measured baseline's existing limits; it does not clear these diagnostics.

**B. Prediction 6**

`C:21–23`: `subset_wall_s=1080.9474446559998`, `cost_sum_s=1008.9430003166199`, `cost_ratio=1.0713662162449058`. Independently recomputed same ratio. Subset took about 72.0044 seconds, or 7.1366%, above recorded cost sum. Bucket: **`0_7_to_1_3`**. Recorded unit costs end at “Copying the results” and exclude subsequent work, so ratio is not a pure docking-speed comparison (`run10_harness3/REPORT.md:51`).

**C. What writes where**

The question's background overstates what earlier reports established. They prove an inherited **absolute-path spelling conflict**, and explicitly leave exhaustive dependency writes unknown: `run10_harness3/REPORT.md:53–66`, `run10_review3/REPORT.md:75–90`, `run10_diff/REPORT.md:85–93`. They do not demonstrate that measured invocation wrote outside out/temp. This audit likewise cannot identify an observed outside-out write from retained files/logs alone. No filesystem write trace was retained.

All four relevant run10 files (`run_units.sh`, `run_command.sh`, `setup.sh`, `units.json`) match harness3 bytes; `audit.json` records checks. Direct wrapper writes are under invocation's out/: log/history/results moves (`U:53–68`), YAML/list (`:77–84,145`), prediction outputs (`:151–152`), raw archive/chain repair/manifest (`:164–205`), and scoring (`:212`). Bytecode disabled at :50. `U:49` builds absolute binary-search paths, and :68 builds absolute TMPDIR. These exports are inherited spelling violations of `SCHEMAS:55`; PATH is a read/search location, TMPDIR remains private out/tmp. Neither export proves an outside-out write.

Resolve work-directory links explicitly. Let `S` be shared run directory and `W_i=S/concurrency-work/<label>` an invocation directory. Under `SCHEMAS:102,115`, `W_i/data -> S/data`, `W_i/baseline-published -> S/baseline-published`, `W_i/harness -> S/harness`; `W_i/out` is a real private directory. Actual U51 root shown in `L:5,21,38` was `S=/tmp/m5-a3e31127-1e00-48ca-9d4a-e4514bd0cf96`, with `W=S/units-check`. Remote directories themselves were not inspected here; resolutions follow stipulated link construction, not a claimed remote `readlink` observation. Being underneath `/tmp` does not make persistent shared `S/data` an invocation-private temporary area.

Known write mechanisms and naming:

| Mechanism and source | Logical target in invocation | Resolved target | Naming; occurrence |
| --- | --- | --- | --- |
| Output/log/config/list/archive/metrics, U references above | `W_i/out/...` | `W_i/out/...` | Fixed basenames, per-unit PDB names, timestamp history names; invocation-private parent. |
| Adapter stage, `run10_review3/evidence/predict.py.txt:54–57,91–172`; applied fixes `run10_harness3/pinder_frodock_fixes.patch:24–30,43–48` | `$TMPDIR/tmp<random>/...`, `$TMPDIR=W_i/out/tmp` | `W_i/out/tmp/tmp<random>/...` | Fresh per-job directory; native `dock.dat`, `clust_dock.dat`, `solutions.pdb`, grids/ASA/model files stay within it. Receptor/ligand staged there before chdir. Example actual path at L:38. |
| Core dataset location, `run10_review3/evidence/core_index_utils.py.txt:42–55` | `W_i/data/pinder/2024-02/` | `S/data/pinder/2024-02/` | Fixed release directory; mkdir only if absent. |
| `get_index()`, same source :90–134; called by U:93 and evaluator source :78,243 | `W_i/data/pinder/2024-02/index.parquet` | `S/data/pinder/2024-02/index.parquet` | Fixed path, shared by every invocation; read existing file by default, download/write only if missing. No custom-index/update argument in measured calls. |
| Missing-native evaluator branch, `run10_review3/evidence/eval_method.py.txt:231–251` | `W_i/data/pinder/2024-02/pdbs/<system>.pdb` | `S/data/pinder/2024-02/pdbs/<system>.pdb` | Per system, shared across apo/holo units for that system. Only invokes downloader when native absent. |
| Entry downloader, `evidence/core_index_system.py.txt:133–145,613–647` | Same release's `pdbs/<entry filenames>`, `test_set_pdbs/<entry filenames>`, `mappings/<entry filenames>` | Same paths under `S/data/pinder/2024-02/` | Entry-derived names, potentially shared across systems; downloads only missing files. |
| Downloader staging/finalization, `evidence/core_utils_dataset.py.txt:151–167,199–211,230` | Random `.part` sibling of each missing dataset destination, then destination | Same shared dataset parent | Per-transfer random staging filename, atomic replacement of per-entry destination. Staging files are temporary; final dataset destinations are outside invocation out/temp. |

Here `evidence/...` means `run10_post/evidence/...`. Preserved source copies retain archive line numbers. Source archive SHA-256 values verified against run10 setup record (`run10/agent/results/reproduce/out/setup/setup_record.json:2–6`); archive/member identities appear in `audit.json`. These are published source plus separately interpreted recorded adapter patch, not a fresh copy of remote installed packages.

For four sampled natives, exact final conditional targets under `S/data/pinder/2024-02/pdbs/` are:

- `1aua__A1_P24280--1aua__A2_P24280.pdb`
- `1ax2__A1_P16404--1ax2__A2_P16404.pdb`
- `1dv1__A1_P24182--1dv1__B1_P24182.pdb`
- `1nr5__A1_P07547--1nr5__A2_P07547.pdb`

All four already belong to setup's input inventory (`run10_harness3/pinder_inputs.tsv:1622,1625,1674,1769`). Run10 setup reports 3,590 inventoried inputs, zero failed, and completion (`run10/agent/results/reproduce/out/setup/setup.log:688,794`). Setup fetches/verifies index and metadata, then all inventoried structural inputs (`run10/agent/harness/setup.sh:3907–3949`). This supports the known missing-file branches staying dormant after successful setup; it does not supply a runtime write trace.

`get_metadata()` can also write fixed `metadata.parquet` when missing (`run10_review3/evidence/core_index_utils.py.txt:151–193`), but no call requiring it was established in executed prediction/evaluation path. Do not count it as an observed write. Home fallback in dataset resolver is bypassed by `PINDER_BASE_DIR=data` and unset `PINDER_DATA_DIR` (`U:31–35`). No home/cache write was demonstrated. Third-party package/import/native-runtime caches were not exhaustively audited.

Therefore potential known dataset destinations mix fixed and per-entry names, all resolving to shared run directory. Whether measured invocation actually exercised any such write, or wrote elsewhere through dependencies, remains **unknown**. `outside_out_writes=unknown` records actual-write uncertainty; `outside_out_location=shared_run_directory` identifies resolved location of established conditional outside-write mechanisms, not an observed event.

**D. Concurrent paths, interference, and detection**

Two/four invocations definitely share reads: prepared source CSV, selection JSON, staged structural inputs via `S/data/frodock`, index and native datasets via `S/data/pinder/2024-02`, interpreter/package files and FroDock/SOAP binaries via `S/baseline-published`. The requested units' list copies, model files, repair archives, logs, summaries, and native temporary cwd are private. A fixed native basename such as `dock.dat` therefore does not by itself imply a collision.

Conditional shared writes make a collision **possible**, not demonstrated or likely for this prepared tree. If index is missing, separate processes can all observe absence, fetch it, and write same fixed `index.parquet` without shown lock/atomic replacement around dataframe serialization (`core_index_utils.py.txt:125–134`). A process can read a file another is creating. Different units also reference same index; different input IDs do not isolate it. Native downloads use random staging plus atomic replacement, reducing partial-read risk for those files; final names remain shared. Sample units have different native basenames, so their native destinations do not automatically collide. Entry-associated shared files could overlap if missing. With all prepared files present and unchanged, shown branches only read and create no such write race. Nothing here establishes another invocation deletes inputs.

No concurrent arm ran in run10, and no concurrency experiment was executed in this audit. Ordinary shared read/cache/resource contention may affect throughput without modifying outputs; that is distinct from file corruption. Native wall-clock RNG dependence also remains a separate inherited concern (`run10_review3/REPORT.md:71`), not proof of a filesystem collision.

Detection is **partly**. `SCHEMAS:122` compares every listed unit PDB with frozen baseline for a-1 and with a-1 for later invocations; missing files mismatch. Modified/missing compared PDBs would be caught, including deterministic corruption already affecting a-1 versus frozen baseline. Nonzero invocation status separately disqualifies an arm. But byte check covers no shared index/native/input/cache files, metrics CSV, log errors, scratch files, or other side effects. Corrupted evaluator inputs/metrics can escape when owned PDBs still match; native subprocess errors can escape wrapper exit status, as A demonstrates. A passing byte check certifies listed result bytes for measured arms, not shared-state isolation.

**E. Avoidance without changing computation**

Known conditional shared-data writes can be isolated with **per-invocation directory construction**, retaining measured script, configuration and input bytes. Give each invocation a real private `data/` tree containing a byte-preserving, independent copy of prepared dataset, selection and FroDock inputs; keep baseline-published/harness shared for reads and out/ private. Copies must not retain writable symlinks or hardlinks back to shared dataset. Copy preparation is outside measured command. Existing relative `PINDER_BASE_DIR=data`, data_dir, structural paths and validation then still work; no per-unit numerical parameter, input byte, program code or argument changes. This is a prospective orchestration change, not implemented or tested here. It differs from exact current rule that every non-out top-level entry is a shared symlink; preserving that rule preserves shared data targets.

No effective environment-only override through unchanged wrapper was established: U:31 overwrites PINDER_BASE_DIR, :35 unsets PINDER_DATA_DIR, :68 overwrites TMPDIR, and :103 validates fixed dataset environment. Existing `--results_dir` already isolates outputs; it does not relocate core dataset. Merely setting inherited PINDER_DATA_DIR or TMPDIR cannot fix these paths. A pre-existing private data tree is thus the concrete no-code route for known conditional dataset-write concern. Whether every transitive dependency cache would also need isolation remains unknown; no universal confinement claim follows.

Absolute PATH/TMPDIR spelling conflict remains separate: private directories do not remove absolute spelling, but current-cwd paths and private temp roots do not themselves collide. Prepared shared dataset appears sufficient for known read-only branches, yet declaring whole command harmless would exceed evidence. Status `avoidable_without_code_change=yes`, `avoidance_kind=per_invocation_directory` refers to established conditional shared-data mechanisms; exhaustive runtime-write absence and concurrent success remain unestablished.
