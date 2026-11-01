Saved evidence establishes a CPU baseline with multiple MPI processes, 16 serial docking jobs over eight benchmark systems, and saved per-job timing. More distinct benchmark systems would bring coverage closer to published PINDER-S scale. Saved evidence does not establish a published GPU implementation, a published precision target, or a scientific gain from repeating this unchanged command concurrently.

Scope: read-only inspection on 2026-11-01; no workloads, network, box access, or git commands. Only this report and status file written. Requested `run9/A/` is stored here as `run9/agent/`; all paths below are relative to current working directory. Schema is `../../../dut/pipeline/m5/SCHEMAS.md` (repository-relative `dut/pipeline/m5/SCHEMAS.md`). Directory sizes checked before selective reads: run9 approximately 6.2 GiB; reproduce approximately 2.1 GiB; profile approximately 4.2 GiB. Large profiler database and report were not opened.

Evidence classes: **measured** means saved runtime output or telemetry; **inferred** means preserved code, configuration, or documents; **unknown** means those records do not settle claim. Intake estimates are not measurements. Installed source trees and original software/source archives were not found among saved run9 files; preserved evidence includes setup recipe, source patch excerpts, compilation logs, resolved configuration, and intake source descriptions. No upstream source was fetched to fill that gap.

1. **CPU execution: `multi`, basis `measured`.**

   Measured: `run9/agent/results/profile/out/profile/baseline.log:7` prints `n_jobs=16 n_solutions=50 mpi_np=8 ... host_nproc=26`. More decisively, lines 41 and 58 print rank IDs 0–7 and `MPI processes (8) awake!`; line 46 reports atom partitioning, `num_atom=719 natom=89 natomr=7`. Reproduce independently records eight awake MPI processes, e.g. `run9/agent/results/reproduce/0116-anchors.log:88`. This establishes multiple CPU execution processes under question's inclusion of multiprocessing; it does not measure an exact total of eight OS threads or eight fully occupied cores throughout command.

   Inferred/configured: `run9/agent/harness/run_command.sh:25` sets `MPI_NP=8`; line 27 sets `EVAL_MAX_WORKERS=8`, passed to `pinder_eval` at line 180. Resolved `run9/agent/results/profile/out/run_command/frodock_config.yaml:1–3` contains `n_solutions: 50`, `mpi_np: 8`, `force: false`. Preserved adapter excerpt `run9/agent/harness/pinder_frodock_fixes.patch:35` launches `mpirun -np {mpi_np} --use-hwthread-cpus`; published default is documented in `run9/agent/intake/baseline.json:44–45`. Setup record identifies Open MPI 4.1.2 and Xeon Platinum 8480+ with 26 available CPUs (`run9/agent/results/reproduce/out/setup/setup_record.json:31–33`).

   Unknown: exact per-rank thread counts, inherited BLAS/OpenMP thread settings, peak live process/thread count, CPU utilisation, affinity, and parallel efficiency. Command harness sets no explicit OMP/MKL/OpenBLAS thread cap. GNU MPI docking link line uses `-lfftw3f` (`run9/agent/results/reproduce/out/setup/compile_frodock.log:6851`); this alone cannot establish runtime library thread count. Setup's `ThreadPoolExecutor(16)` at `run9/agent/harness/setup.sh:3944` handles acquisition, outside measured command. Evaluation's eight workers are configuration evidence; no worker census was inspected.

2. **Independent computational units: `yes`; count `8_to_63`; docking order `serial`.**

   Measured scale: eight systems × holo/apo pairings = 16 docking jobs, 50 retained/scored decoys each = 800 decoys. Profile header records configuration (`baseline.log:4–7`); reproduce result has 16 job records, each with `n_decoys_scored: 50` and no penalised missing selected jobs (`run9/agent/results/reproduce/out/anchors_details.json:18–436`). Actual input manifest lists all 16 rows in `run9/agent/results/reproduce/out/results/frodock_setup.csv:2–17`.

   Inferred independence: each manifest row supplies its own receptor, ligand and pairing; adapter allocates a fresh temporary directory and writes per-system/per-pairing outputs (preserved source at `pinder_frodock_fixes.patch:24–30,42–48,53–64`). Preserved `pinder/methods/main.py` loop calls `predict_method(complex_config, config_dict)` once per row (`pinder_frodock_fixes.patch:19–20`). Jobs need no other job's docking output; evaluation combines their metrics afterward (`run_command.sh:119–120,176–180`). Holo/apo jobs from same system are computationally separable, not independent statistical samples.

   Measured serial order: first holo starts at 10:47:05.978 (`baseline.log:10`), reaches result-copy marker at 10:48:05.219 (line 703), then apo starts at 10:48:05.224 (line 704). Same pattern continues through final apo copy marker at 12:18:25.014 (line 11117). Serial classification describes these 16 docking jobs; MPI work inside each job is parallel, and subsequent scoring requests eight workers.

   Count excludes 800 decoys as independent search replicates. They emerge from shared search/clustering, with `--nc <n_solutions>` selecting output count (`run9/agent/intake/baseline.json:29–36`). No executed independent seed ensemble established: evaluation harness says FroDock exposes no seed, recording/exporting `BASELINE_EVAL_SEED` only (`run_evaluation.sh:13–16`).

3. **Per-unit timing saved: `yes`.**

   Reproduce already saves per-job `docking_wall_s` and `poses_per_s` in `run9/agent/results/reproduce/out/anchors_details.json`. Definition at line 6: logger's `Running FroDock` timestamp to `Copying the results` timestamp. Examples: first holo 42.387 s (line 42), first apo 40.500 s (line 68). Sixteen intervals sum to 4536.183 s (line 441). These belong to earlier reproduce/anchor invocation, not profiled invocation.

   Profile also saves both timestamps for every job. Following table subtracts those observed timestamps; labels abbreviate system IDs listed in full in manifest. Line pairs use LF-based log numbering (`rg -n`).

   | System | Holo seconds | Log start/copy lines | Apo seconds | Log start/copy lines |
   | --- | ---: | --- | ---: | --- |
   | 1a19 | 59.241 | 10 / 703 | 51.228 | 704 / 1440 |
   | 1aua | 234.916 | 1441 / 2134 | 258.537 | 2135 / 2828 |
   | 1ax2 | 198.956 | 2829 / 3522 | 269.235 | 3523 / 4216 |
   | 1dtd | 96.512 | 4217 / 4894 | 203.131 | 4895 / 5572 |
   | 1dv1 | 683.149 | 5573 / 6266 | 304.966 | 6267 / 6944 |
   | 1glj | 533.660 | 6945 / 7638 | 477.966 | 7639 / 8332 |
   | 1ht8 | 673.131 | 8333 / 9026 | 686.233 | 9027 / 9729 |
   | 1nr5 | 364.454 | 9730 / 10423 | 383.486 | 10424 / 11117 |

   Profile intervals sum to 5478.801 s. Whole measured command wall is 5621.4601993279975 s (`run9/agent/results/profile/out/profile/raw_wall_s.json:1`). Scope differs: logger interval ends before result copying completes and excludes later chain-label restoration/scoring; whole-command timer includes these. Logger clocks are calendar timestamps, not dedicated monotonic per-job timers. FroDock also prints stage/rank `Time` and `Total time` values (e.g. `baseline.log:483–516,564–592`); eight rank totals must not be added as job wall time. Saved records do not establish complete exclusive timings for all eight stages, per-pose generation timestamps, or time to first acceptable pose.

4. **Published GPU path: `unknown`.**

   Measured local execution used CPU: `run_command.sh:22` hides GPUs; profile header reports GPU count zero (line 8). `stats.log:4,8,12` reports no CUDA kernel, GPU memory or CUDA trace data. All 39,680 saved `gpu_util_raw.jsonl` rows record utilisation 0.0 across profiler envelope. Box nevertheless had one NVIDIA H100 PCIe and 26 available CPUs (`run9/agent/results/probe/probe.json`, fields `nvidia.gpus`, `nproc`). GPU presence and toolkit installation do not imply use.

   Documents describe this FroDock adapter/build as CPU/MPI only (`EXECUTION.json:36`; `setup.sh:86`; stage commands in `baseline.json:29–36`), with compiled GNU binaries recorded at `setup_record.json:8–12`. No published GPU path for this computation is established in supplied records. Conversely, local CPU execution and absence of such a path in these records do not establish that published study or upstream software offers none. Full upstream implementation/publication coverage is unavailable here; status therefore remains unknown.

5. **More distinct units: `closer_to_published_scale` (inference, not measured gain).**

   Brief prioritises 93 paired-unbound systems within PINDER-S's 250 (`intake_mirror/BRIEF_run5.md:3–5`). Intake explicitly reduces only case count to eight, selecting first eight eligible IDs lexicographically (`EXECUTION.json:3–7`); runtime index counts confirm 250/93 (`baseline.log:4–5`). Completing additional distinct eligible systems at same per-system protocol would move coverage toward 93, then broader benchmark scope. Current eight cover 8/93 of priority set; running both pairings over all 93 would mean 186 jobs at current pairing convention. Neither completion within budget nor speedup is measured.

   Tighter uncertainty on same population quantity is unknown: selection is deterministic rather than random, paired results are dependent, and no sampling/uncertainty model is supplied. Improved docking quality on existing inputs is also unknown. More retained poses, independent random restarts, and additional benchmark inputs are different interventions. Repeating unchanged command on same selected inputs does not itself expand benchmark coverage or prove independent search diversity. Brief asks whether more search improves recovery and distinguishes top-ranked versus best-of-fixed-N (`BRIEF_run5.md:9–19`); that question remains open. Reproduce's 10/16 top-1 acceptable versus 15/16 best-of-50 acceptable jobs (`anchors_details.json:437–441`) demonstrates distinction, not an effect of increased parallelism. No AAV result follows; AAV redocking omitted at this scale (`EXECUTION.json:8`).

6. **Published uncertainty/precision target: `unknown`.**

   Saved intake found no numeric FroDock PINDER-S leaderboard result (`baseline.json:54–56`; `benchmark.json:34–36`). All three anchor/reference `uncertainty` fields are null (`anchors.json:9,20,31`): only DockQ acceptability threshold 0.23 and composition counts 250/93 recorded. Threshold is pose-quality criterion, not uncertainty or precision of main quantity. Primary publication was not fetched during intake (`anchors.json:5`; `benchmark.json:32`), so these absences do not establish absence from publication. No supported published equal-precision target can be extracted. Local anchor outcomes are not published precision estimates.

Interpretation of pipeline bounds: supplied schema profiles CUDA/NVTX/OSRT with CPU sampling disabled (lines 69–84); concurrency probe runs three sequential copies, then batches of two and four unchanged full commands, computing `factor_n = n * median(single_wall_s) / batch_wall_s` (lines 86–99). It measures throughput only, without checking scientific correctness. Bounds for data-parallel over inputs and ensembles use `min(8, factor)`; batching uses `min(4, factor)`; pipelining targets transfer share; multi-GPU targets compute share on equal GPU-second basis (lines 115–129).

No concurrency output, profile packet or bounds file is saved under run9/agent; profile operation log ends `invalid profiler output` (`run9/agent/results/profile/0119-profile.log`). Missing factor defaults to bound 1/infeasible by schema line 125; this is missing evidence, not a measured absence of useful parallelism. Concurrent copies would each already request eight MPI ranks: CPU contention, memory demand, useful throughput and costs remain unknown. A concurrency factor for repeated full commands would not measure restructuring individual jobs or a GPU port.

Evaluation schema requires matched scientific metrics, timed paired runs and equal cost (lines 235–242). Its declared per-arm GPU counts must be positive (line 241), whereas saved baseline adapter declares zero GPUs (`run_evaluation.sh:19–21`); current GPU-second protocol therefore cannot simply be treated as a validated cost model for this CPU workload. Observed GPU busy time zero does not mean allocated box cost zero. No cost-effective scientific improvement was measured here.

Material limits: source pin is PINDER `ebeb28a2f8411363cef722b7d293c978f7442672`; FroDock software/scoring material is owner-approved unverified mirror, identity with original distribution unresolved (`setup_record.json:2–7`; `BRIEF_run5.md:38–40`). Executed adapter includes recorded source fixes and chain-label repair (`pinder_frodock_fixes.patch`; `run_command.sh:126–174`), so exact unmodified upstream execution is not claimed. Profile logs include nonzero MPI child-status warnings (e.g. `baseline.log:48–62`) despite final `PREDICT_EXIT=0` and `EVAL_EXIT=0` (lines 11119,16204). Process completion and anchor checks do not certify all stage semantics or establish material identity. These limits do not erase observed MPI execution, serial job order, or saved timing evidence.
