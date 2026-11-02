Run11 second post-check — 2026-11-02

New concurrent-only messages concern Python semaphore cleanup at shutdown. No evidence identifies resource exhaustion, numerical failure, or a collision between scientific output paths. Cleanup messages themselves have no identified mechanism for changing completed scientific files; exact cause of stale semaphore registration remains unknown. Compared files establish identical final ranked poses, but omit scientific intermediates and evaluation results. Complete, useful byte-comparison coverage cannot be obtained by editing output lists alone.

Scope: local source and recorded-file inspection, standard-library parsing and byte comparisons only. No workload, harness/probe invocation, box contact, network access, git command, credential or `.keys` read, or `~/.codex/` access. Authored files only under `run11_post2/`. Existing launcher records untouched.

References relative to experiment directory unless absolute. Abbreviations:

- `L/<name>`: `run11/agent/results/reproduce/out/concurrency/logs/<name>.log`.
- `C`: `run11/agent/results/reproduce/out/concurrency/concurrency.json`.
- `U`, `M`: `run11/agent/harness/run_units.sh`, `units.json`.
- `R9`: `run9/agent/results/reproduce/out/`.
- `R10`: `run10/agent/results/reproduce/units-check/files/`.
- `E`: `run10_post2/evidence/`; `V`: `run10_review3/evidence/`.
- `P`, `S`: `/home/hal/dev/interp/metis/dut/pipeline/m5/concurrency_probe.py`, `SCHEMAS.md`.

Line references count LF separators; embedded CR progress updates stay on same line. Binary references use byte offsets or source writers instead of invented line numbers. Read requested contract at `S:81–86,120–144`. Independently verified run10/run11 unit wrapper, command wrapper, and manifest byte equality; setup source identifiers and applied repair patch also match (`run10/agent/results/reproduce/out/setup/setup_record.json:2–6`, run11 equivalent). Earlier saved source reconstructions are identified as such, not represented as newly inspected installed box files (`run10_post2/REPORT.md:9`).

**A. Concurrent messages, origin, consequences, prior occurrence**

Only additional diagnostic class found across 26 invocation logs: two `UserWarning` messages in each of `L/c4-1-2:5745–5748` and `L/c4-2-2:5745–5748`:

1. `resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown`.
2. `resource_tracker: '/mp-dfegt5fy': [Errno 2] No such file or directory`, with `/mp-cir2ntbx` in second repeat.

Both invocations run second sample unit, 1ax2 apo. Both finish `EVAL_EXIT=0` at line 5749; probe reports matched outputs (`C:25–26`). Names identify POSIX named semaphores, not missing PDB, map, or CSV paths. “Leaked” means tracker still has a registered name at shutdown; subsequent ENOENT means cleanup cannot find that semaphore name. It does not demonstrate a live leaked object, thread-limit exhaustion, or two docking invocations using same output pathname. Classify as `library_warning`, not `resource_or_thread_limits` or `shared_path_collision`.

Producer explicitly identified by logs: `/usr/lib/python3.10/multiprocessing/resource_tracker.py`, lines 224 and 237. Evaluator provides relevant multiprocessing path: `V/eval_run.py.txt:82–100` enables parallel evaluation and writes CSVs; `V/eval_method.py.txt:376–393` calls `process_starmap`; `E/core_process.py.txt:16–23` uses a spawn-context Pool, gathers `starmap` results, then leaves pool context. Thus Python evaluator's process synchronization is supported origin; exact semaphore owner, missing unregister event, and reason both warnings occur only at width four are not recorded. Timing association alone does not prove cross-invocation interaction or a name collision.

Local CPython source corroborates mechanism, with an explicit version limit: available source is Python 3.14, not box's 3.10. `/usr/lib/python3.14/multiprocessing/resource_tracker.py:5–9` describes EOF after clients exit and cleanup of remaining names; `:48–54` maps semaphore cleanup to `sem_unlink`; `:385–412` warns about registered leftovers, attempts unlink, and warns on exception. `/usr/lib/python3.14/multiprocessing/synchronize.py:74–87` registers named synchronization objects and normally unlinks/unregisters them. This is corroboration of standard mechanism, not verification of exact remote interpreter bytes.

Result consequence: warning emission changes diagnostic logs. Shutdown semaphore cleanup does not rewrite docking coordinates, maps, native solution arrays, or score tables; observed unlink attempt fails because object is already absent. Native docking and pose copy-out have already finished before evaluator starts (`U:149–212`; e.g. `L/c4-1-2:649–705`). Published evaluator computes metrics, writes metrics CSV, computes leaderboard, then writes leaderboard CSV (`V/eval_run.py.txt:94–100`); tracker shutdown is distinct from those computations. Mechanistic inference: these cleanup warnings themselves do not change completed scientific results, compared or uncompared. Status `concurrent_messages_affect_results=no` refers to diagnosed warning/cleanup operation. It does **not** certify equality of unavailable run11 score files, identify underlying bookkeeping defect, or prove absence of every other concurrency effect. Root-cause attribution beyond stale registration/absent cleanup target cannot be established from saved logs.

No tracker/semaphore messages in either a log, any of eight b logs, any of eight c2 logs, or six other c4 logs. Also absent from run10 subset outer `run10/agent/results/reproduce/units-check/run.log` and inner `R10/run_command/run_command.log`; these two logs are byte-identical. Absent from run9 final full log `R9/run_command/run_command.log`, three root `*-anchors.log` receipts (0112, 0114, 0116), three archived command logs in `R9/anchors_logs/`, two saved anchor logs below that directory, and two historical command logs in `R9/run_command/history/`. These are direct searches, including failed earlier full-run attempts; no prior occurrence found. Status `concurrent_messages_seen_before=no` concerns **new semaphore messages**.

Other errors/warnings recur without concurrency. Counts independently checked:

| Diagnostic | Each four-unit a log | Each single-unit b/c log |
| --- | ---: | ---: |
| Logging formatting error | 4 | 1 |
| MPI nonzero-exit diagnostic | 8 | 2 |
| Ligand-size advisory | 24 | 8 for 1aua/1ax2/1nr5; 0 for 1dv1 |
| Guessed-element warning | 4 | 1 |
| Missing-system evaluator ERROR | 18 | 18 |

Examples: `L/a-1:9–38,44–72,699–700,2771`; `L/b-1-1:9–38,44–72,699–705`; corresponding run9 1aua apo block `R9/run_command/run_command.log:2132–2825` and run10 block `units-check/run.log:8–701`. Causes: malformed `log.info("OUT", output_dir)` (`E/predict_patched.py.txt:54–60`); successful native grid branch calls `exit(1)` after map write/MPI finalization (`E/frodockgrid.cpp.txt:253–269,287–320`), and adapter ignores subprocess return codes (`E/predict_patched.py.txt:129–140`); ligand advisory only prints (`E/libfrodock.cpp.txt:853–856`); PDB element inference during assembly; deliberate missing-system penalties (`U:208–216`, `V/eval_method.py.txt:423–482`). Penalties affect CSVs and their population changes with selected unit set. These inherited messages must not be confused with new shutdown warnings.

**B. Uncompared files, scientific use, repeatability**

Four sample indices 3,5,9,15 identify 1aua, 1ax2, 1dv1, 1nr5 apo (`C:7–24`). Each unit lists only 50 final PDBs, ranks 1–50, under `results/frodock/<system>/apo_decoys/` (`M:172–225,284–337,508–561,844–897`). Exactly 200 paths; verified reference digest keys equal their union. Other files include several kinds:

| Uncompared files | Contents and analysis use | Run-specific content / raw byte comparison |
| --- | --- | --- |
| `results/frodock_metrics.csv` | Per-pose DockQ, iRMS, LRMS, Fnat, CAPRI, contact/shape counts, rank and benchmark membership, plus missing-system penalties. Scientific result table used by analysis. | No timestamp/path columns in retained tables. Whole table depends on invocation's unit set and penalty population; row order can vary independently of science. |
| `results/frodock_leaderboard.csv` | Scientific aggregates: medians, top-k/oracle quality and success rates by benchmark/pairing. Published evaluator's summary output. | No clock fields in retained table. Aggregates differ when unit coverage differs; not a unit-owned file. No demonstrated direct consumption of this CSV by inspected anchor/evaluation adapters. |
| `tmp/tmp<random>/*_W.mrc`, `*_E.mrc`, receptor/ligand `*_DS.mrc` | Four numerical potential grids per unit, consumed by docking. Computational scientific intermediates, not directly read by final analysis adapters. | Random directory name, not inherently random file payload. Sixteen sample grids byte-match run9/run10. MRC writer clears label space (`E/volume_fwr.cpp.txt:504–513`), rather than writing a clock label. Future universal determinism not established. |
| Same temporary directory's `dock.dat`, `clust_dock.dat` | Native numerical solution arrays, transformations/scores before and after clustering; contain information beyond rounded final coordinates. Clusters feed pose generation. | Eight sample files byte-match run9/run10. No timing fields in inspected cluster writer (`E/frodockcluster.cpp.txt:55–65`); native docking writes solution arrays (`E/frodock.cpp.txt:198–212`). Random ancestor path prevents fixed manifest addressing. |
| Same temporary directory's `model_1.pdb`…`model_50.pdb` | Stage copies of generated final poses before wrapper chain repair. | Sample repair count zero; duplicates of compared scientific content. Random ancestor names. Non-model PDBs are removed (`E/predict_patched.py.txt:163–176`). |
| `results/frodock_setup.csv`, `run_command/frodock_config.yaml` | Selected original input records and fixed parameter metadata. | YAML can compare directly; same 39 bytes in run9/run10. Setup CSV deliberately differs with invocation's requested units (`U:119–146`). |
| `run_command/chain_labels_restored.json`, `raw_decoys.tar.gz` | Repair provenance and originals for changed poses; originals contain scientific coordinates when present. | Manifest may contain invocation-dependent collection of relative file paths (`U:194–204`). Sample manifest is `[]` and archive empty. Gzip container still contains creation time; nonempty tar members also carry file metadata. |
| `run_command/run_command.log`, histories, probe logs and summary | Progress, diagnostics, timestamps, random temporary paths, MPI process identifiers, durations/throughput/resources. Logs also print native solution transforms/scores. Anchor adapter reads timestamps for timing. | Expected to differ between identical computations. Raw byte equality inappropriate for complete log/archive containers. |

Writers: `U:53–84,164–216`; `E/predict_patched.py.txt:94–176`; `V/eval_run.py.txt:94–100`. Example extra information: `R10/tmp/tmp5grg8h1w/dock.dat` begins with native int count 135121, has 3,783,404 bytes; `clust_dock.dat` has 50 records and 1,416 bytes. Final fifty coordinate files neither contain all original candidate solutions nor retain every full-precision native transformation/score. Reader prints seven floats including score from each native record (`E/frodockview.cpp.txt:149–175`).

Analysis use established directly, not inferred from filenames. `run11/agent/harness/run_anchors.sh:39–40,85–107,118–139` reads omitted metrics CSV, computes top1/best quality, acceptability, and timing from omitted log. `run9/agent/harness/run_evaluation.sh:162–194` likewise reads metrics CSV for DockQ/iRMS/LRMS/Fnat/top1/best/acceptability/decoy count and adds timing/throughput. This matches requested outcomes in `BRIEF.md:15–17`. Published scorer constructs leaderboard from scored metrics (`V/eval_method.py.txt:633–651`). No inspected final analysis reads `.mrc` or `.dat` directly; these feed pose computation instead. Run11 standalone probe does not run anchor analysis (`S:85–86`); these are baseline analysis consumers, not an invented run11 analysis execution.

Independent retained-file check: all 24 sample native intermediates (four maps plus two `.dat` files per unit) byte-match run9/run10, including full payloads, not just headers. Temporary directory pairs: 1aua `R9/tmp/tmpk_0hde5f` / `R10/tmp/tmp5grg8h1w`; 1ax2 `tmprq4inyd1` / `tmpnquwr2gq`; 1dv1 `tmp4avx3_iu` / `tmpjvuifm4j`; 1nr5 `tmpwojsti6g` / `tmp8qhahlpl`. Logged provenance also recorded at `run10_post2/REPORT.md:60–65`, with original comparison code at `run10_post2/audit.py:120–143`.

Metrics comparison supplies useful additional evidence beyond run11's probe: keyed by `(id, monomer_name, model_name, pinder_set)`, all 400 computed sample rows (200 poses represented in XL and S) have identical strings in **every column** between run9 and run10. Example model_1 rows: `R10/results/frodock_metrics.csv:1987,2007,2059,2130,4522,4542,4594,4665`; matching run9 rows `:2379,2499,2601,2672,5502,5622,5724,5795`. Whole CSVs differ: run9 has 6,542 data rows, subset 5,366. Both leaderboards have nine rows and 41 columns, but population context differs. These checks establish prior full/subset equality for sample scientific values, not run11 concurrent score equality.

Some differences occur even with unchanged science. Missing penalty rows iterate a Python set without sorting (`V/eval_method.py.txt:450–469`); raw row ordering is not a scientific invariant. Wrapper calls `tarfile.open(..., "w:gz")` without normalizing timestamp or archive metadata (`U:171,195`). Actual gzip MTIME bytes at offsets 4–7 are 1793521769 in `R9/run_command/raw_decoys.tar.gz` and 1793582439 in R10; archive member counts 100 and zero respectively reflect full/subset repair scope, not equivalent containers. Even two empty archives created at different seconds ordinarily differ in gzip header time. Sample repair JSON is `[]` (`R10/run_command/chain_labels_restored.json:1`), so not every metadata file must vary. Native SAS code also seeds from `time(0)` and conditionally rotates geometry (`V/sas.cpp.txt:683–690,747–759`): observed matching maps do not prove all future inputs/repeats deterministic.

Statuses: uncompared files are `multiple`; analysis use `yes`; run-specific content `partly`. Omitted scientific tables/grids/solutions cannot all be dismissed as timing or metadata.

**C. Does PDB identity cover every scientific result?**

No. It establishes same final ranked structural files for these four units: all fifty configured pose ranks, not merely a few selected poses. Probe hashes a-1 against reference and compares later listed paths against a-1 (`P:325–334,412–418`; `S:129`). PDB filenames preserve ranking. Coordinates plus fixed native structures and same scorer are sufficient inputs to recompute reference-based geometry metrics, so pose equality is strong scientific evidence about generated structures. It is not a byte-level check that evaluator actually produced identical score tables, nor that omitted native candidate arrays/grids/scores matched. Rounded PDB representation also cannot establish equality of all upstream floating-point values. Thus `compared_files_hold_all_scientific_results=no`.

Run11 work-directory result trees were not fetched. Only shared probe summary/logs survive. Cannot independently rehash run11 poses or compare its `.dat`, `.mrc`, metrics, leaderboard, repair archives or metadata across arms. Existing `baseline_match=true`, `outputs_match=true` therefore remain probe-recorded verdicts for manifest paths. Prior run9/run10 intermediate/score equality does not fill this run11 evidence gap.

**D. Can output-list edits alone close coverage with valid byte comparisons?**

Some additions are mechanically possible without changing measured command: fixed existing paths such as `run_command/frodock_config.yaml` or `results/frodock_metrics.csv` satisfy path syntax. But that does not provide complete, valid per-unit comparison coverage. Status `coverage_extendable_without_code_change=no` means **covering omitted results as useful comparisons across existing reference/a/b/c modes**, not inability to append any string to JSON.

Reasons:

1. Native scientific payloads have random `tmp/tmp<random>/` ancestors (`U:67–68`; `E/predict_patched.py.txt:54–60`). Manifest paths are literal relative names, with no wildcard, discovery or remapping (`P:180–189,325–334`). Existing run9 scratch names will not address new runs. Stable per-unit copies/exports or comparator discovery would require wrapper/probe changes. Payloads are byte-comparable once corresponding files are identified; 24/24 prior matches demonstrate this, without guaranteeing future equality.
2. Metrics, leaderboard, setup list and repair metadata are invocation-wide. Reference contains sixteen units, a contains four, b/c contain one each. Adding same combined CSV to each unit compares different populations even when that unit's own scientific rows match perfectly. Reference/a mismatch can stop probe before later arms (`S:129`; `P:434–437`). Per-unit filtering and canonical sorting, or separate scientific-value comparisons, require an export/comparison change. Raw CSV ordering also needs treatment even for same population. These tables are not timing-only and should be checked semantically, not ignored.
3. Logs contain clocks, performance, paths and IDs; tar/gzip containers contain metadata and timestamps. Merely listing them would intentionally detect normal run differences. Compare relevant scientific payloads separately from volatile metadata. Fixed config is already byte-comparable but does not close scientific coverage.

A follow-up could preserve measured numerical command, parameters and inputs while adding post-command exports/comparison logic. That would be an explicit harness/probe change, not a `units.json`-only extension, and no such change or workload was performed here. Full run11 scientific equivalence, exact semaphore bookkeeping root cause, and repeatability beyond inspected sample remain unestablished.
