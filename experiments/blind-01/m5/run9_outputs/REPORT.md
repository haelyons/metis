Run9 output and host-only assessment, 2026-11-01.

Read `run9_units/REPORT.md`, `run9_par/REPORT.md`, `run9_replay2/REPORT.md` and their statuses first. Requested `run9/A/` absent; saved records live under `run9/agent/`, matching prior reports. Paths below relative to current directory unless absolute. **Measured** means observations/calculations over saved files or this summariser replay; **Read** means preserved code/documents; **Inferred** means consequences of those records. No docking, scoring, profiling or concurrency workload run. No network, box contact, git command, credential or `.keys` read. Writes confined to `run9_outputs/`; existing launcher logs left untouched.

Measured directory sizes before selective reads: `run9/` 6.2 GiB; each final decoy tree 329 MiB; source profile directory 1.3 GiB, mostly large profiler artifacts. Neither `.sqlite` nor `.nsys-rep` opened or copied. Only six profile inputs copied, largest 1,424,183 bytes. Saved final PDBs read directly for byte comparison, without copying. Full installed PINDER/FroDock source trees unavailable in saved run9; source evidence consists of preserved patch excerpts, harness and intake source descriptions. Brief read at `intake_mirror/BRIEF_run5.md`, including scope and material-identity limits; no upstream source fetched.

1. **Output organization: `both`.**

   **Measured:** `run9/agent/results/reproduce/out/results/frodock/` contains exactly 800 files: 16 unit directories, each containing `model_1.pdb` through `model_50.pdb`. One unit is `(PINDER system ID, monomer kind)`, not one candidate pose. Combined outputs also exist: `out/results/frodock_metrics.csv` contains per-decoy score rows across jobs; `out/results/frodock_leaderboard.csv` aggregates scores; `out/anchors_details.json:18–436` contains all 16 job records and lines 437–447 contain overall summary/measured values.

   **Read:** `run9/agent/harness/run_command.sh:15–17,119–120,176–180` names final pose and combined score outputs. `run_anchors.sh:129–134,145–162` writes combined job/timing summary. Combined scoring also includes published missing-case penalties, so its rows are not limited to generated poses.

2. **Relative per-unit paths stable: `yes`.**

   **Read:** `run9/agent/harness/pinder_frodock_fixes.patch:43–48` constructs `results_dir / f"frodock/{complex_id}/{complex_kind}_decoys/"`, then copies model files there. Canonical `results_dir` is `out/results` (`run_command.sh:51–52,119–120`). Thus comparison paths relative to `out/` are:

   ```text
   results/frodock/<system_id>/<holo|apo>_decoys/model_<rank>.pdb
   ```

   **Measured:** Actual file set equals this formula for every manifest row and ranks 1–50; no additional files inside final decoy tree. See `output_file_audit.json` for all relative result paths, sizes, hashes and comparison results.

   **Inferred:** With same unit inputs and fixed 50-pose configuration, directory and filename set does not depend on other selected units or serial position. No subset invocation executed here; path stability follows preserved construction, not an isolation measurement. Both saved full invocations have identical path sets.

3. **Run-specific content in per-unit result files: `no`, for saved final model PDBs.**

   **Measured:** All 800 reproduce PDBs match corresponding profile-run PDBs byte for byte: 342,779,850 bytes per run. Individual files range 116,559–726,003 bytes. Exhaustive record census finds only 800 `CRYST1`, 4,225,650 `ATOM`, and 5,400 `HETATM` records. No timestamp, elapsed-time, absolute-path, hostname, PID or thread-count metadata records. Crystal record example, from first apo model line 1:

   ```text
   CRYST1    1.000    1.000    1.000  90.00  90.00  90.00 P 1           1
   ```

   `output_evidence.json` records counts; `output_file_audit.json` records every file's SHA-256 and direct byte-equality result. This independently confirms earlier reader's saved-run comparison.

   **Scope:** File modification times differ but are filesystem metadata, outside file bytes. Combined timing summary and logs do contain run-specific wall times, timestamps and paths (`anchors_details.json:42–43`; `run_command/run_command.log:5,7`). `run_specific_content=no` refers to per-unit scientific model files, not every file under `out/`. Combined metrics and leaderboard files cover selected set and are not per-unit byte-comparison targets. Repeatability under reordered, isolated or concurrent invocations remains unmeasured.

4. **Per-unit costs recorded: `all_units`.**

   **Measured:** Every one of 16 manifest units has finite `docking_wall_s` in `run9/agent/results/reproduce/out/anchors_details.json`; exact values retained in `output_evidence.json`. Rounded seconds:

   | System prefix | Holo seconds | Apo seconds |
   | --- | ---: | ---: |
   | 1a19 | 42.387 | 40.500 |
   | 1aua | 198.066 | 207.376 |
   | 1ax2 | 150.616 | 235.191 |
   | 1dtd | 77.674 | 156.016 |
   | 1dv1 | 559.922 | 241.194 |
   | 1glj | 442.639 | 401.635 |
   | 1ht8 | 549.309 | 582.405 |
   | 1nr5 | 326.071 | 325.182 |

   Sum **4536.183000564575 s**. Full IDs appear in `out/results/frodock_setup.csv:2–17` and `anchors_details.json:9–16`. Reproduce `out/run_command/run_command.log` supplies all 16 start/copy pairs: first holo lines 7/700, first apo 701/1437; final holo 9727/10420, final apo 10421/11114. First interval runs 07:13:52.222–07:14:34.609 = 42.387 s.

   **Read:** Timing definition `anchors_details.json:6` and extraction code `run_anchors.sh:109–116,128–134` use logger timestamp from “Running FroDock” to “Copying the results”. This ends before copy completes and excludes later repair/scoring; not total exclusive unit lifecycle cost. Presence of per-unit seconds is established despite narrower timing scope.

5. **Subset identifiers: `args_safe`, through published preprocessing selection.**

   **Read:** Actual saved setup uses published `pinder_methods preprocess --method frodock --data_dir ... --ids "$IDS_LITERAL" --pairs "$kind"` (`run9/agent/harness/setup.sh:3973–3984`). IDs passed as command-line list literal, no user-provided selection file required. Generated setup manifest then drives prediction (`pinder_frodock_fixes.patch:16–20`; `run_command.sh:82`). Saved evaluation adapter gives single-system form (`run_evaluation.sh:115–128`):

   ```sh
   pinder_methods preprocess --method frodock --data_dir <private-prep-dir> \
     --ids '["1a19__A1_P11540--1a19__B1_P11540"]' --pairs holo
   ```

   Command shown as evidence only; not executed. System ID plus `--pairs holo` or `--pairs apo` selects one unit. Native `--ids` takes system IDs, not invented `ID:holo` tokens. `ID:kind` is an optional convention interpreted by saved evaluation wrapper (`run_evaluation.sh:98–103`), which splits it into those two arguments.

   **Measured:** All eight system IDs have length 32 and match ASCII regex `[A-Za-z0-9._:+=-]{1,128}`. All 16 optional `ID:kind` labels likewise match, lengths 36 or 37. Checks recorded in `output_evidence.json`. List-literal brackets/quotes are argument syntax, not characters in identifiers.

   **Boundary:** This is published preprocess selection followed by prediction over its generated manifest. Intake `baseline.json:22,25` describes predict's `--ids`, but preserved prediction loop does not establish that flag alone filters an already-full manifest. Fixed `run_command.sh` itself accepts no subset arguments and enforces eight systems/16 jobs (`99–107`). A probe must prepare selected manifest through published interface and invoke appropriate prediction command; unchanged fixed wrapper rejects reduced scale. Arbitrary mixed pairing subsets may require multiple preprocess selections and combining their generated rows, as saved harness already does.

6. **Measured command ran 16 units: `16_to_63`.**

   **Measured:** Setup CSV contains 16 data rows: eight system IDs × holo/apo; every unit has 50 saved/scored model files. Reproduce log line 4 prints `n_jobs=16 n_solutions=50 mpi_np=8`; saved profile `out/profile/baseline.log:7` independently agrees. `anchors_details.json:437–441` reports 16 jobs. Units exclude 800 candidate poses and eight MPI ranks within each docking job.

7. **Requested host-only rule: all four checks satisfied.**

   **Measured replay:** Copied original six small input files into `run9_outputs/profile/`, verifying SHA-256 equality. `profile_inputs.json` records source/copy paths, bytes and hashes:

   | Input | Bytes |
   | --- | ---: |
   | `stats_cuda_gpu_kern_sum.csv` | 0 |
   | `stats_cuda_gpu_mem_time_sum.csv` | 0 |
   | `stats_cuda_api_sum.csv` | 0 |
   | `stats.log` | 928 |
   | `raw_wall_s.json` | 74 |
   | `gpu_util_raw.jsonl` | 1,424,183 |

   Read current `/home/hal/dev/interp/metis/dut/pipeline/m5/profile_summarise.py` and ran exactly:

   ```sh
   python3 /home/hal/dev/interp/metis/dut/pipeline/m5/profile_summarise.py run9_outputs/profile
   ```

   Exit **0**, stdout/stderr empty. Current summariser SHA-256 **01c9207ec08297a7a0d5e7adfc4c369f0472ac32326c93a83fc0da8e362bb0b3**, unchanged after execution. `summariser_execution.json` records command, exit and hash. No patch applied. Earlier replay described older phrase mismatch; current source lines 24–26 already match saved statements at `profile/stats.log:4,8,12` (“CUDA kernel data”, “GPU memory data”, “CUDA trace data”). Summariser reads exactly six copied inputs (`profile_summarise.py:20–28,51,58–66,83`); no additional input required.

   Read newly emitted `profile/stages.json`, `profile/total_wall_s.json` and all samples in `profile/gpu_util.json`:

   | Stage | `wall_s` | `gpu_s` |
   | --- | ---: | ---: |
   | kernels | 0.0 | 0 |
   | memcpy H2D | 0.0 | 0.0 |
   | memcpy D2H | 0.0 | 0.0 |
   | CUDA API host time | 0.0 | null |
   | other host time | 5621.4601993279975 | null |

   **CUDA rows zero: yes. Telemetry present: some, 38,622 samples. Every retained sample's `util` exactly 0.0: yes. Other host time within 2%: yes.** Total wall **5621.4601993279975 s** equals other-host wall exactly; relative difference **0**, allowed absolute difference **112.42920398655995 s**. First/last retained times relative to command start: **0.10748221299945726 / 5621.430496616002 s**. `profile_evidence.json` records calculations.

   **Read:** Summariser retains samples within command window (`89–90`) and computes residual host time as total minus allocated CUDA rows (`75–81`). Zero rows plus matching skip statements produce full residual host allocation. This evaluates requested rule, not a new CPU-time measurement or concurrency result.

8. **Cross-unit state: `unknown`.**

   **Read:** Preserved loop calls prediction once per manifest row (`pinder_frodock_fixes.patch:19–20`); adapter creates fresh temporary directory, stages current unit inputs (`24–30`), and constructs per-unit result path (`43`). Intake records separate native stage invocations per unit (`baseline.json:27–38`). No seed argument appears in recorded native commands; `data.json:136–139` records unavailable published seeds, while evaluation wrapper says exported seed is not consumed (`run_evaluation.sh:13–16`).

   **Measured limit:** Both byte-identical saved invocations process same units in same serial order. No unit-isolation or reordered invocation observed. Full adapter/native source and dependencies unavailable for complete state audit. Fresh directories/processes support isolation but cannot exclude shared Python state, cache effects or reproducibly initialized sequence-dependent behavior. Neither `yes` nor `no` established. No claim that private working directories alone guarantee concurrency correctness.
