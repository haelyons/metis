One unit is one system/monomer-pairing docking job: distinct receptor and ligand inputs. Run9 executes 16 such jobs over eight systems, with 50 candidates generated within each job. Established reduction concerns input coverage. Repeating those same inputs concurrently would test throughput and output preservation; it would not expand coverage or establish improved docking recovery.

Assessment dated 2026-11-01. Earlier `run9_par/`, `run9_scale/`, and `run9_scale2/` reports and statuses read first. Requested `run9/A/` resolves here to `run9/agent/`. All paths below relative to current directory. Writes confined to `run9_units/`; no docking, profiling, evaluation workload, box contact, network access, or git command performed. Analysis consists of reading saved records, arithmetic, byte comparisons, and read-only SQLite queries. Directory sizes checked first: intake 928 KiB, harness 1.3 MiB, reproduce 2.1 GiB, profile 4.2 GiB. Each saved final decoy tree occupies 329 MiB. Large profiler database opened read-only with `mode=ro&immutable=1`; only schema, process/thread metadata, and selected thread event aggregates queried.

Evidence labels: **Measured** = saved execution observations or calculations/comparisons over saved outputs; **Read** = preserved code/configuration/documents; **Inferred** = consequences of those observations. Intake's descriptions of upstream source remain secondary evidence. Full installed PINDER/FroDock source trees and source archives were not found under saved run9; available source evidence comprises patch excerpts, harness, compilation output, and intake source descriptions. No missing source fetched. Published FroDock numerical performance, candidate default, and seed schedule remain unestablished. Mirror identity remains unresolved (`intake_mirror/BRIEF_run5.md:38–40`; `run9/agent/intake/baseline.json:68`).

1. **Unit kind: `distinct_inputs`.**

   **Read:** `run9/agent/intake/EXECUTION.json:3–7,11–19` defines eight selected PINDER-S systems, holo and apo monomers for each, 50 candidates/job, eight MPI ranks/job. One unit = one row `(id, kind, receptor, ligand)` in `run9/agent/results/reproduce/out/results/frodock_setup.csv:2–17`. Holo/apo use different coordinate inputs; they are not two random trials of identical input. `run9/agent/harness/pinder_frodock_fixes.patch:16–20` preserves manifest iteration and one `predict_method` call per row. Lines 24–30 allocate a fresh temporary working directory and stage that job's inputs; lines 43–48 copy its outputs into its own system/pairing directory.

   **Measured:** `run9/agent/results/profile/out/profile/baseline.log:7` reports 16 jobs and 50 solutions/job. First job starts at line 10, reaches copy marker at 703; next starts at 704. Last copy marker at 11117. All 16 intervals follow serial order. MPI stages inside each job run in parallel. Reproduce `out/anchors_details.json:18–436` records 16 jobs with 50 scored decoys each, no missing selected job.

   **Inferred:** Jobs are computationally separable from other jobs' docking outputs. Paired holo/apo cases can share biology; computational separability does not imply statistical independence. Fifty poses within a job are ranked search/clustering products, not 50 independent docking trials, chains, walkers, or parameter points. Intake records `frodockcluster ... --nc <n_solutions>` and ranked view/export stages (`baseline.json:26–36`).

2. **Reduced dimension: `inputs`.**

   **Read:** `EXECUTION.json:4–8` explicitly reduces case count to first eight lexicographically sorted eligible systems, retaining per-case protocol. Brief prioritizes 93 paired-unbound systems within 250 PINDER-S systems (`intake_mirror/BRIEF_run5.md:3–7`). Runtime confirms those release counts (`baseline.log:4–5`). Saved resolved configuration is `n_solutions: 50`, `mpi_np: 8`, `force: false` (`run9/agent/results/reproduce/out/run_command/frodock_config.yaml:1–3`).

   **Measured arithmetic:** 93/8 = 11.625; 250/8 = 31.25. First ratio compares matched paired-apo system coverage. Second compares system counts only: all 250 do not have paired apo. Expanding current holo+apo design to 93 systems gives 186 jobs and 9,300 retained poses, versus 16 jobs and 800 poses now.

   **Unknown:** No established reduction in trials/input, candidates/input, parameter points, or unit length. Published adapter requires `n_solutions` without a published default (`baseline.json:46`); 50 cannot be called a reduction from an unknown published value. Each job run once in planned scale (`EXECUTION.json:37`). Predicted monomers and separate AAV challenge omitted (`EXECUTION.json:8,16`; `baseline.json:43`); these concern additional inputs/conditions, not evidence of shortened individual searches. Brief's seed instruction does not establish a published repeat count.

3. **Expansion effect: `coverage`; basis `inferred`.**

   More distinct systems/input conditions yield more observed benchmark coverage. This inference follows documented selection and per-input execution. It is not a measured expansion experiment or a quoted published claim about parallelism. Holding existing inputs/configuration fixed gives no code-level reason that adding other systems should improve each existing system's poses. Actual invariance under isolation/concurrency still untested.

   No probability-sampling design, uncertainty target, or published FroDock performance estimate establishes a precision gain. Eight sorted IDs are not repeated measurements of one input. Adding candidates within one job would be a different intervention, potentially changing its best-of-N outcome; no larger published N established. Brief explicitly separates search coverage from ranking (`BRIEF_run5.md:11–19`).

   Global anchor can increase when new inputs add a larger maximum, even though existing per-input outcomes stay fixed. For a nested set preserving old poses, maximum cannot decrease. This is a change in aggregation opportunities, not evidence of better recovery on the same input. Status `coverage` describes expanded input dimension; it does not assert invariant global maximum.

4. **Combination: `best_or_max` for gated scalar.**

   **Read:** `run9/agent/harness/run_anchors.sh:119–139,148–158` computes top-ranked and best DockQ per system/pairing, then `max(best_all)` across jobs for `dockq_acceptable_threshold`. Threshold 0.23 is pose acceptability criterion (`BRIEF_run5.md:15`), not expected benchmark maximum or error tolerance.

   **Measured:** Reproduce `out/anchors_details.json:437–447` reports 10/16 top-1 acceptable jobs, 15/16 best-of-50 acceptable jobs, and gated maximum 0.9775788581560528. These results are not an average over independent trials. Per-unit metrics also retained. Separate `out/results/frodock_leaderboard.csv:1–10` contains medians and percentages for rank/oracle selections, with missing-system penalties; it is a different aggregation and includes unrun cases. Single enum describes gated scalar, not every CSV column.

5. **Unit wall: `1_to_10min`; unit-cost CV: `over_50pct`.**

   **Measured:** Reproduce's 16 saved `docking_wall_s` values yield mean **283.511438 s**, median **238.192500 s**, minimum **40.500 s**, maximum **582.405 s**, total **4536.183001 s**. Population SD **174.984831 s**; population CV = SD/mean = **0.61720555 = 61.7206%**. Sample SD gives CV **63.7447%**; either convention exceeds 50%. CV describes differences among these heterogeneous jobs, not repeat-to-repeat timing noise.

   Profile's independently logged intervals yield mean **342.425063 s**, median **287.100500 s**, range **51.228–686.233 s**, total **5478.801 s**, population CV **60.7150%** (sample CV **62.7061%**). Both typical values fall in 1–10 min; some profiled units exceed 10 min.

   | System prefix | Reproduce holo s | Reproduce apo s | Profile holo s | Profile apo s | Profile holo start/copy lines | Profile apo start/copy lines |
   | --- | ---: | ---: | ---: | ---: | --- | --- |
   | 1a19 | 42.387 | 40.500 | 59.241 | 51.228 | 10 / 703 | 704 / 1440 |
   | 1aua | 198.066 | 207.376 | 234.916 | 258.537 | 1441 / 2134 | 2135 / 2828 |
   | 1ax2 | 150.616 | 235.191 | 198.956 | 269.235 | 2829 / 3522 | 3523 / 4216 |
   | 1dtd | 77.674 | 156.016 | 96.512 | 203.131 | 4217 / 4894 | 4895 / 5572 |
   | 1dv1 | 559.922 | 241.194 | 683.149 | 304.966 | 5573 / 6266 | 6267 / 6944 |
   | 1glj | 442.639 | 401.635 | 533.660 | 477.966 | 6945 / 7638 | 7639 / 8332 |
   | 1ht8 | 549.309 | 582.405 | 673.131 | 686.233 | 8333 / 9026 | 9027 / 9729 |
   | 1nr5 | 326.071 | 325.182 | 364.454 | 383.486 | 9730 / 10423 | 10424 / 11117 |

   Source: reproduce `out/anchors_details.json`, each job's `docking_wall_s`; profile `out/profile/baseline.log`, timestamp subtraction at listed lines. Log line references count LF separators as `rg -n`; carriage-return progress updates are not extra lines. Timing definition is “Running FroDock” to “Copying the results” (`run_anchors.sh:109–116,128–134,151`). Interval ends before copy-out completes and excludes later chain-label repair and evaluation. It is not complete unit lifecycle timing. Reported stage/rank times must not be summed as independent wall intervals. Exact stage breakdown and time to first acceptable pose remain unknown.

6. **Subset selectable: `published_option`, through published preprocessing interface.**

   **Read:** `baseline.json:21–25` records published `--ids`/`--pairs` selection. More directly, preserved setup invokes `pinder_methods preprocess ... --ids "$IDS_LITERAL" --pairs "$kind"` (`harness/setup.sh:3973–3984`), then builds 16-row manifest (`3991–4004`). Saved `harness/run_evaluation.sh:98–128` similarly accepts chosen ID/pairing, invokes published preprocess selection, and constructs a manifest containing only requested input. Predict reads manifest and iterates its rows (`pinder_frodock_fixes.patch:16–20`), with manifest copied into chosen results directory (`run_evaluation.sh:144–150`). These establish a route without further changes to published program code, using installed recorded fixes.

   Important boundary: `run_command.sh` is a fixed experiment wrapper, with explicit eight-system/16-job validation (`99–107`), not a general subset launcher. Running that wrapper unchanged cannot select a smaller set. For an existing prepared set, supplying a filtered setup CSV is a configuration/input-manifest edit. Intake says predict accepts `--ids`; preserved predict-loop excerpt does not show filtering, so direct filtering by predict's flags alone is **not established**. Supported route selects during preprocess or supplies selected manifest, then predicts. No subset run executed during this assessment.

7. **Unit scientific output repeatability: `bitwise`, observed for two saved serial invocations.**

   **Measured here:** Compared corresponding `model_1.pdb` through `model_50.pdb` in all 16 job directories under `run9/agent/results/{reproduce,profile}/out/results/frodock/`. Both path sets contain exactly **800 files**. All **800/800 match byte for byte**, **342,779,850 bytes per run**. This includes coordinates, order/rank, chain labels and other PDB text. Comparison covered final repaired scientific pose files, not timestamps/logs or all temporary intermediates.

   Resolved configuration files match bytewise (SHA-256 `5052c03131dc546c8b3cf7d818174b29893991c18fda95157067530e61cdc251`), as do setup manifests (`9e29837be20fb33f8cd891dea4ee36cf3bbaa62c3d9339cab6beb7d7b4fd6f56`), chain-label change manifests and leaderboard CSVs. Metrics CSVs differ in row order. After keying each row by `(id, monomer_name, model_name, pinder_set)`, both contain **6,542 unique keys**, identical key sets, and **zero differing row values in any field**. Selected PINDER-S rows represent 800 generated poses; remaining rows include other subsets and penalties.

   **Limit:** This strengthens earlier reports' untested repeatability assessment for these saved serial runs. It does not prove bitwise results across hardware/library changes, different MPI counts, reordered units, independent invocations, or concurrent copies. Both observed executions preserve same serial order and per-unit configuration; input/source trees themselves were not retained for comprehensive hash comparison. Run wrapper regenerates results rather than reusing `force=false` outputs (`run_command.sh:59–82`). No tolerance invented or required for observed byte equality.

8. **Random state and serial position: `unknown`.**

   **Read:** `intake/data.json:136–139` records no published seed values and no seed-parameterized FroDock adapter stage. `run_evaluation.sh:13–16,137–150` exports `BASELINE_EVAL_SEED` but says FroDock does not consume it. Selection uses sorted IDs. Preserved stage command list launches native tools anew per job (`baseline.json:26–38`), and patch shows fresh temporary directories.

   These facts do not establish absence of randomness inside native tools, all random-state initialization, or absence of cross-unit state. Full native source unavailable. No observed reorder/isolation/concurrency comparison. Two identical same-order runs cannot distinguish deterministic per-unit state from reproducibly initialized sequence-dependent state. Therefore neither `no_randomness`, `per_unit_independent`, nor `sequence_dependent` established. No evidence supports treating different exported seeds as independent search trials.

9. **Thread-count setting: `unknown`; observed threads/CPUs: `half_or_more`. Fixed MPI rank count established separately.**

   **Read:** Explicit computational parallelism control is MPI rank count, not an OpenMP thread-count option. Installed configuration fixes `mpi_np: 8`; adapter default documented as 8 (`baseline.json:44–45`; patch:64). Launch uses `mpirun -np {mpi_np} --use-hwthread-cpus` (patch:35). Wrapper fixes `MPI_NP=8`, evaluation `EVAL_MAX_WORKERS=8` (`run_command.sh:25–27,180`). `--th 10` is recorded among docking stage parameters; it is not evidence of a ten-thread setting. No explicit OMP/MKL/OpenBLAS cap in wrapper.

   **Measured:** Probe reports **26 logical CPUs** (`results/probe/probe.json:98`); profile header agrees (`baseline.log:7`), and line 41 prints eight awake MPI processes. Eight ranks/26 CPUs = **30.77%**, below half, but ranks are not total OS threads.

   Targeted read-only queries of `results/profile/out/profile/baseline.sqlite` found **128 search-rank processes** named `frodock_mpi_gcc` (16 jobs × 8). Every such process has **three threads named `frodock_mpi_gcc`**, plus three separately named tracing/communication threads (`[NSys]`, `[NSys Comms]`, `*2CommsProcesso`). First search's rank PIDs: 68205, 68206, 68211, 68217, 68224, 68232, 68238, 68247. Thus that eight-rank stage has **24 program-named threads**, **92.31% of 26 CPUs**, before counting tracer threads, launcher, or Python parent. Their observed OSRT event spans share interval **32.603225915–68.453503739 s** from capture start. Not a sum across serial jobs. Status `half_or_more` refers to this literal observed thread population, not occupied cores.

   Query joins `PROCESSES` to `ThreadNames` on `(globalTid >> 24) = (globalPid >> 24)` and `StringIds.id = ThreadNames.nameId`; filters process/thread name `frodock_mpi_gcc`. Grouped names give same three program-named threads for all 128 processes. `OSRT_API` min(start)/max(end) grouped by first 24 program-named globalTids establishes overlapping event extents. Those threads include runtime/helper activity: many events are waits/sleeps. Context-switch tracing disabled (`baseline.log:1–2`); no CPU sampling table found in saved SQLite schema. Runnable demand, per-thread compute use, unprofiled exact thread census, inherited library settings, and useful CPU saturation remain **unknown**. Fixed eight-rank setting does not imply eight total threads, nor does 24 live threads imply 24 busy cores. Status `thread_setting=unknown` avoids substituting MPI rank control for an unestablished thread-count control: no evidence settles whether actual helper/library thread counts follow a fixed rule, environment setting, or core count. Configured MPI work parallelism itself is explicitly fixed at eight ranks.

10. **Writes outside private out/temp: `unknown`.**

   **Read:** Canonical measured wrapper places logs/config/history, results, raw-decoy archive, repair manifest and metrics under `out/` (`run_command.sh:50–82,132–180`), sets `TMPDIR=$PWD/out/tmp` (`65–66`), and disables Python bytecode (`48`). Patch stages copies of inputs into fresh temp directory before native stages (`24–30`); fixed `dock.dat`/`clust_dock.dat` filenames therefore live in job's own temp directory (`baseline.json:33–36`). These are positive isolation mechanisms.

   However, wrapper shares `data/` via `PINDER_BASE_DIR`, imports PINDER's `get_index`, and unsets `PINDER_DATA_DIR` (`run_command.sh:29–33,89–94`). Full installed dependency/cache code and filesystem-write tracing with resolved paths unavailable. OSRT API events do not provide a complete file-path/write audit. No evidence proves a shared cache/input/source write, and no evidence excludes one. Separate out directories alone therefore do not establish absence of all collisions. Setup explicitly writes source/data trees (`setup.sh:19–20,3975–4003`), but setup is excluded from timed docking; those writes are not silently counted as measured-run writes. Copies sharing the same `out/` would collide directly through wrapper archive/move/output operations; private working/output trees are prerequisite for claimed isolation.

11. **Earlier categories merged distinctions: `yes`.**

   `run9_scale/status.json` maps reduction to `replicates_or_samples`, factor `10_to_100x`; here actual reduced dimension is distinct benchmark inputs, not established replicate or candidate reduction. Earlier prose already recognizes much of this distinction. `run9_par/status.json` reports `independent_units=yes`, `units_at_run_scale=8_to_63`, `more_units_changes_result=closer_to_published_scale`; those coarse labels do not specify system vs pairing vs retained candidate, computational vs statistical independence, or coverage vs improved within-input search.

   Expanding eight systems toward 93 expands coverage; repeating same few jobs tests repeatability/throughput; retaining more candidates can alter best-of-N; additional independent trials would need actual independent stochastic state; changing MPI rank count changes internal execution. Those are different interventions. Main gate's global maximum further differs from per-input outcomes and benchmark-wide rates. Earlier labels do not settle causal scientific gain from serial/concurrent execution of fixed inputs. Earlier reports generally state these limitations in prose; finding concerns loss of distinctions in enum categories, not fabrication by earlier readers.
