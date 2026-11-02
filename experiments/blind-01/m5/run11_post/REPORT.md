Run11 post-check — 2026-11-02

Concurrent gain survives repeat and nearby-serial comparisons: about 1.56× at width two, 2.30× at width four. Both width-four repeats add semaphore cleanup warnings absent from serial logs. Compared paths cover final docking PDBs, but omit scores and intermediates. Every arm reports one changed shared entry; retained records do not identify that entry or establish whether another invocation reads it. CPU occupancy best explains gain; no observed reduction in docking computation.

Scope: local record/source inspection and standard-library arithmetic/log checks only. No workloads, box contact, network, git commands, credentials, `.keys`, or `~/.codex/` reads. Authored files only in `run11_post/`; existing launcher files untouched.

References relative to experiment directory unless absolute. `C` = `run11/agent/results/reproduce/out/concurrency/concurrency.json`; `L/<name>` = `run11/agent/results/reproduce/out/concurrency/logs/<name>.log`; `U` = `run11/agent/harness/run_units.sh`; `M` = `run11/agent/harness/units.json`; `P` = `/home/hal/dev/interp/metis/dut/pipeline/m5/concurrency_probe.py`; `S` = same directory's `SCHEMAS.md`. Log line numbers count LF bytes, preserving embedded CR progress updates. Earlier source evidence is identified explicitly below.

Contract read: `S:81–86,120–144`. `C:5,25–26` records `measured`, `baseline_match=true`, `outputs_match=true`; all eight arms counted, none skipped. Independently checked reference digest keys equal exactly 200 sample manifest paths. Run11 retained collection contains logs and summary, not each invocation's result tree; this audit therefore verifies comparison implementation and recorded verdict, without independently rehashing remote run11 PDBs. `P:325–334` hashes a-1 against reference and byte-compares later invocations against a-1; missing/unreadable files fail comparison.

**A. Logs: new warnings in concurrent runs.** Read all 26 invocation logs, including broad case-insensitive error/warning/failure/abort/traceback/cache/download/reuse/skip searches.

`L/c4-1-2:5745–5748` and `L/c4-2-2:5745–5748` each contain two new Python multiprocessing warnings:

- `resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown`.
- Cleanup of `/mp-dfegt5fy` (first repeat) or `/mp-cir2ntbx` (second): `[Errno 2] No such file or directory`.

Neither warning appears in a-1, a-2, any b invocation, or any c2 invocation. Both affected invocations still end `EVAL_EXIT=0` at line 5749, and their compared PDBs matched. This establishes association with these width-four invocations, not cause or numerical harmlessness of semaphore behavior. Semaphore names alone do not identify any counted shared-run-directory file.

Other diagnostic classes recur in serial and concurrent runs:

| Diagnostic | Each a invocation, four units | Each single-unit invocation |
| --- | ---: | ---: |
| Logging formatting TypeError | 4 | 1 |
| MPI nonzero/abort diagnostic | 8 | 2 |
| Ligand-size warning | 24 | 8 for 1aua/1ax2/1nr5, 0 for 1dv1 |
| Biotite guessed-element warning | 4 | 1 |
| Missing-system evaluator ERROR | 18 | 18 |

Counts include warning text merged onto other native output lines. In a-1, logging failures start at lines 9,703,1397,2075; first MPI aborts at 47,64; element warnings at 699,1393,2071,2765; evaluator errors at 2771–7658 and 7811–7819. Same classes occur in a-2. Example concurrent single-unit log `L/c2-1-1` has logging failure at 9, aborts at 47,64, element warning at 699, evaluator errors starting 705. Single-unit invocations report 341 missing XL apo systems and 92 missing S apo systems, versus 338 and 89 in a arms: each scorer sees one rather than four computed systems. Four scorers per b/c arm yield 72 evaluator ERROR records per arm, versus 18 per a arm. This also occurs in b, so is not a new concurrency failure class.

Earlier source diagnosis remains applicable: `log.info("OUT", output_dir)` has no formatting placeholder (`run10_post2/evidence/predict_patched.py.txt:54–60`); native successful grid branch writes maps, finalizes MPI, then calls `exit(1)` (`run10_post2/evidence/frodockgrid.cpp.txt:253–269,287–320`); adapter does not check subprocess return codes (`predict_patched.py.txt:129–140`). `U:208–216` deliberately accepts missing-system penalties. Run11/run10 `run_units.sh`, `run_command.sh`, and `units.json` are byte-identical; setup source hashes/commit and applied fixes also match. Provenance recorded in each run's `out/setup/setup_record.json:2–6` and `out/setup/pinder_frodock_fixes.applied.patch`. These inherited diagnostics do not erase new semaphore warnings. Status: `new_in_concurrent`.

**B. Coverage: partly.** Sample indices 3,5,9,15 identify apo units 1aua, 1ax2, 1dv1, 1nr5 (`C:7–24`). Each manifest lists exactly `model_1.pdb` through `model_50.pdb`, under `results/frodock/<system>/apo_decoys/`: 50 PDBs per unit, 200 total (`M:172–225,284–337,508–561,844–897`). These cover all configured final pose ranks for these units.

They do not cover all results of measured command. Wrapper also scores those poses and writes `out/results/frodock_metrics.csv` and `out/results/frodock_leaderboard.csv` (`U:16–18,212`; scorer writers in `run10_review3/evidence/eval_run.py.txt:85–100`). Those CSVs contain unit-dependent results/aggregates and are absent from every `outputs` list. Scores across four single-unit scorers versus one four-unit scorer have different aggregation/coverage contexts; no score equivalence follows from PDB equivalence. Also unchecked: four numerical maps per unit, `dock.dat`, `clust_dock.dat`, retained stage models, logs/configuration, raw-decoy archive, and chain-repair manifest (`U:164–205`; `run10_post2/evidence/predict_patched.py.txt:94–176`). Shared inputs/caches are not compared. Thus verdict validates listed PDB bytes, not every result or side effect.

**C. Shared writes: unidentified counted entry; cross-invocation reading unknown.** Each arm has `shared_changes=1` (`C:56,85,147,209,271,333,395,457`). That means one non-directory pathname differs in size/mtime/existence between that arm's two snapshots, not one write syscall, not necessarily same pathname across arms, and not necessarily a computation cache. Names and before/after values are discarded (`P:226–245,355,410,419–420`). No path-level snapshot or filesystem trace is retained. Receipt `run11/agent/results/reproduce/0044-concurrency.log` is empty (zero bytes).

Known writes and path resolution, with shared root `R=/tmp/m5-ce26ef9a-8a3a-4854-8190-4d94b3195b59` and invocation root `W=R/concurrency-work/<name>` from log tracebacks:

| Entries/mechanism | Purpose and sharing | Explains counted change? |
| --- | --- | --- |
| `R/out/concurrency/logs/<name>.log` | Outer stdout/stderr capture, unique per invocation; opened by probe, inherited by command (`P:353,384–386`; `U:66`). | No: snapshot excludes top-level `out`. |
| `W/out/run_command/**`, `W/out/results/**` | Logs, config, restricted original-record CSV, archive, repair manifest, final poses and scores (`U:53–84,121–146,164–216`). Private real `out`, not shared results. | No: snapshot excludes `concurrency-work`. |
| `W/out/tmp/tmp<random>/**` | Fresh per-unit native stage: copied inputs, four maps, two docking/cluster files, generated poses. Fixed basenames remain inside distinct private directories (`U:67–68`; adapter source cited above). | No: same exclusion. |
| `R/data/pinder/2024-02/index.parquet` | Shared prepared input cache; default `get_index()` reads existing file, downloads/serializes only if absent. | Conditional writer; no evidence branch ran. |
| `R/data/pinder/2024-02/{pdbs,test_set_pdbs,mappings}/<entry-derived-name>` and transient sibling `.part` files | Shared structural/mapping input downloads when missing; potentially reused by later consumers. | Conditional writers; no evidence branch ran. |

Probe links `W/data`, `W/baseline-published`, and `W/harness` to shared entries, while creating fresh private `W/out` (`P:343–354`). Therefore dataset targets really resolve into shared R. `U:31–35` fixes dataset base/release. Index source `run10_review3/evidence/core_index_utils.py.txt:42–55,89–147` shows cached read branch and write branch; evaluator native guard at `run10_review3/evidence/eval_method.py.txt:231–251`; entry downloader at `run10_post/evidence/core_index_system.py.txt:133–145,613–647`; staging/atomic replace at `run10_post/evidence/core_utils_dataset.py.txt:151–167,199–211,230`. Four native filenames are `<full sample system ID>.pdb` under shared `pdbs/`.

Run11 setup fetched and verified index/metadata and reports 3,590 inventoried inputs, zero failed (`run11/agent/results/reproduce/out/setup/setup.log:678,682,688`). No invocation log shows a dataset download. This supports prepared-input read branches, but cannot identify the changed entry or prove all dependencies read-only. `@lru_cache` on `get_index` and evaluator's `_metrics` cache are process/object-local memory caches, not evidence of cross-invocation disk result reuse (`core_index_utils.py.txt:89`; `eval_method.py.txt:573–582`).

If conditional dataset writes ran, another invocation could read their destinations in same or later arm: all consumers share paths. Index serialization has no demonstrated atomic replacement/lock; entry downloader uses atomic replacement. However, no evidence identifies counted entry as one of these caches or demonstrates such a read. Known output/log/scratch flow does not read another invocation's output. **Actual changed shared entry, its purpose, and actual cross-invocation reads remain unknown.** Earlier reports explicitly retained that inventory limit (`run10_post/REPORT.md:35–78`; `run10_post2/REPORT.md:73–107`). New count supplies no missing pathname attribution. Status values for purpose and reads: `unknown`, `unknown`.

Snapshot limitations matter: directories/atime ignored; top-level out/work/profiler excluded; symlinks not followed; transient files created then removed or metadata restored between snapshots can escape; writes outside R unobserved. One count is neither exhaustive write inventory nor proof of isolation. In particular, calling it merely logs would wrongly use excluded outer captures to explain an included entry.

**D. Less work: no observed reduction in computation.** Every invocation logs all requested units, with no `Skipping ... because it already exists` marker. Across all 32 unit executions, independently compared these per-unit log records against a-1: four map-write messages, two identical ASA computation/skipped/out counts, ranked ligand generation 1–50, and result copy-out. All match for corresponding unit. Example `L/c2-1-1:44,61,87,102` writes four maps, `:86,101` records ASA work, `:649–698` generates fifty ligands, `:701` copies results. Other single-unit logs have same line positions except 1dv1: ligand generation 633–682 and copy 685. Serial a-1/a-2 copy markers occur at 701,1395,2073,2767; all prediction/evaluation exits are zero. Each a logs four completed systems; each other invocation logs one.

Fresh private outputs prevent normal `force=false` skip branch (`P:343–352`; `U:61–84`; `run10_post2/evidence/predict_patched.py.txt:228–243`). Adapter creates fresh stage per unit and always runs native stage list, then assembles/copies new poses (`:54–60,94–176`). There is no shown lookup of previous invocation's grids/solutions. Total measured CPU seconds also do not shrink: a-1 7840.626; a-2 7890.186; b about 8204–8211; c2 about 8397–8461; c4 about 8916–8928 (full table below). Single-unit invocations are compared by corresponding four-unit total, not mistaken for less work because each selects only one unit. Repeated imports/evaluations add work in b/c.

One real I/O difference: a-1 has `inblock=17584`, all later invocations zero (`C:70` and later invocation rows). This is consistent with warmed OS page cache for shared inputs/binaries; it does not establish reuse of computed docking results or fewer numerical operations. Output block totals stay similar (a-1 812712; a-2 815096; c arms 804400–823560). a-2 is slightly slower despite zero input blocks. Cache hits, instruction counts and all dependency internals were not measured; unidentified shared write prevents universal no-reuse proof. Status `no` answers whether evidence shows less computation, not whether every conceivable reuse mechanism has been excluded.

**E. Order: small slowdown in every repeat; gain holds locally.** Numbers from `C` arm rows (a-1 at 47–71, b-1 76–85, c2-1 138–147, c4-1 200–209, c4-2 262–271, c2-2 324–333, b-2 386–395, a-2 448–472):

| Arm | First wall s | Repeat wall s | Repeat minus first s | Change |
| --- | ---: | ---: | ---: | ---: |
| a | 1068.783468 | 1069.285329 | +0.501861 | +0.04696% |
| b | 1240.215038 | 1255.990045 | +15.775007 | +1.27196% |
| c2 | 685.287787 | 687.450971 | +2.163184 | +0.31566% |
| c4 | 460.121502 | 470.427257 | +10.305755 | +2.23979% |

All repeats are slightly slower, hence status `later_arms_slower`. This is descriptive; two repeats do not establish statistically significant or causal temporal drift. There is no pattern of every later arm beating a-1: b arms are slower and a-2 virtually identical. Differences between arm types dominate repeat differences.

Published formula uses mean a wall / mean c wall (`P:445–455`; `S:138–143`). Recomputed means: a 1069.034399 s, b 1248.102542 s, c2 686.369379 s, c4 465.274380 s. Factors 1.557520530 and 2.297642950; reported factor is maximum (`C:27–42,479`).

For each concurrent arm, use nearest baseline-own serial a arm in run order (a-1 for first-half c arms; a-2 for second-half). Also show nearest serial single-unit b arm, so interpretation of “serial” is explicit:

| Concurrent arm | Nearby a | a wall / c wall | Nearby b | b wall / c wall |
| --- | --- | ---: | --- | ---: |
| c2-1 | a-1 | 1.559613 | b-1 | 1.809773 |
| c4-1 | a-1 | 2.322829 | b-1 | 2.695408 |
| c4-2 | a-2 | 2.273009 | b-2 | 2.669892 |
| c2-2 | a-2 | 1.555435 | b-2 | 1.827025 |

Thus approximately 1.56×/2.30× holds against local baseline-own serial comparisons; exact repeated ratios vary. Against b, gain is larger, but that is a different denominator. Even conservative minimum a wall / maximum c wall gives about 1.555× for c2 and 2.272× for c4. Local comparison does not remove unknown shared-state effects, but rules out simple a-1-only timing anomaly. Status: `yes`.

**F. Gain source: idle CPU capacity in serial mode most plausible.** Recorded nproc 26, total memory 231924764 KiB (`C:477–478`).

| Arm | CPU s | Effective cores | Busy fraction | Max threads | Minimum available KiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| a-1 | 7840.626 | 7.3360 | 0.2856 | 625 | 215701892 |
| b-1 | 8210.899 | 6.6205 | 0.2571 | 535 | 222972216 |
| c2-1 | 8397.448 | 12.2539 | 0.4746 | 624 | 220406380 |
| c4-1 | 8927.920 | 19.4034 | 0.7518 | 802 | 215128336 |
| c4-2 | 8916.295 | 18.9536 | 0.7335 | 801 | 215027160 |
| c2-2 | 8461.150 | 12.3080 | 0.4754 | 624 | 220303088 |
| b-2 | 8203.875 | 6.5318 | 0.2547 | 535 | 222870988 |
| a-2 | 7890.186 | 7.3789 | 0.2867 | 625 | 215916756 |

Serial a occupies only about 7.3 of 26 logical CPUs on average, about 28–29% host busy. Two concurrent invocations reach about 12.3 effective cores/47.5% busy; four reach about 19/73–75%. Despite hundreds of live threads, average active CPU use remains much smaller: thread count is not CPU saturation. Eight MPI ranks per docking invocation (`U:27`; native log `L/a-1:39`) fit observed serial occupancy; serial native/assembly/scoring phases can reduce average use further. Parallel independent units fill idle capacity.

Memory remains plentiful: minimum across arms 215027160 KiB, about 205.1 GiB and 92.7% of total. Invocation max RSS values range 2387564–2542560 KiB (about 2.28–2.42 GiB); wait4 max RSS is not sum of simultaneous process memory. These data supply no memory-capacity-pressure explanation. Memory bandwidth/cache misses and separate I/O wait durations were not measured, so smaller overlap/cache contributions cannot be quantified or ruled out. Busy fraction is host-wide and can include unrelated work; effective cores is measured command CPU time divided by arm wall (`P:395–425`; `S:131`). Agreement between their trends strengthens occupancy explanation.

Four-unit separate invocation mean exceeds baseline-own serial mean by 179.068143 s, 16.75046%. This includes repeated startup, imports, scoring and other invocation overhead; it is not pure startup measurement. Such costs count against published gain, not a source of cheaper later computation. Concurrent CPU totals exceed a totals while wall drops, consistent with more work per second across idle CPUs. Width-four per-unit invocation walls (336–470 s) also exceed corresponding b walls (273–389 s), so throughput gain is from overlap, with contention, rather than each unit becoming intrinsically faster. Exact division among MPI efficiency, serial phases, OS scheduling, and memory/I/O overlap remains unmeasured. Best-supported status: `idle_cpu_in_serial_mode`.

Validation performed: parsed saved JSON; checked sample/reference path sets; recomputed means, factors, repeat deltas and nearby-arm ratios; scanned every invocation log and compared per-unit map/ASA/rank markers; checked run11/run10 harness/fix bytes and source identifiers. No numerical workload or probe executed. Remaining principal uncertainty is identity/use of counted shared entry; complete result equivalence and causal attribution beyond listed PDBs/resource trends are not established.
