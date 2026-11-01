# Run9 saved-artifact replay

Replay date: 2026-11-01. Scope: local saved evidence, current U48 summariser, source inspection, arithmetic. No baseline or concurrency workload executed. No box contacted, network fetched, git command run, or source changed. All authored files are under `run9_replay/`.

Actual checkout root: `/home/hal/dev/interp/metis`, three parents above working directory. Requested logical A/C paths map to `run9/agent/` and `run9/control/`; literal `run9/A/` and `run9/C/` do not exist here.

## Replay result: exit 1, still parse

Directory sizes inspected with `ls -lah` before reading. Saved profile directory totals about 1.3 GiB: `baseline.nsys-rep` about 98 MiB, `baseline.sqlite` about 1.2 GiB. Neither opened or copied. `baseline.log` also unnecessary. Copied exactly seven profile inputs to `run9_replay/profile/`:

| Input | Bytes |
| --- | ---: |
| stats_cuda_gpu_kern_sum.csv | 0 |
| stats_cuda_gpu_mem_time_sum.csv | 0 |
| stats_cuda_api_sum.csv | 0 |
| stats.log | 928 |
| raw_wall_s.json | 74 |
| gpu_util_raw.jsonl | 1,424,183 |
| nsys-version.txt | 57 |

Copies made with `shutil.copyfile`; SHA-256 source/copy equality checked for all seven. Exact hashes: `input_manifest.json`. Source hashes: `source_sha256.json`.

Required replay command, from original working directory:

```sh
python3 -I /home/hal/dev/interp/metis/dut/pipeline/m5/profile_summarise.py run9_replay/profile
```

Exit code **1**. Stdout empty. Stderr: `invalid profiler output`. Exact subprocess invocation/result: `summariser_execution.json`. Surrounding diagnostic Python commands exited 0; this does not change summariser's recorded exit 1.

`profile_summarise.py:20-28` accepts empty files only when `stats.log` contains exact activity-specific text. Saved `stats.log` lines 4, 8, 12 say:

| Report | U48 required text | Saved text | Result |
| --- | --- | --- | --- |
| Kernel | does not contain CUDA kernel data | does not contain CUDA kernel data | Accepted as zero |
| Memory | does not contain CUDA memory data | does not contain GPU memory data | Rejected |
| API | does not contain CUDA API data | does not contain CUDA trace data | Rejected |

Saved Nsight version: `NVIDIA Nsight Systems version 2025.3.1.90-253135822126v0`.

First actual failure occurs at memory CSV (`profile_summarise.py:60`); empty content has no CSV header and no in-file SKIPPED line, raising `ValueError("missing CSV header")` at lines 45-47. Main catches error and exits 1 at lines 103-108. Read-only diagnostic calls to `report_rows` separately confirmed kernel yields `[]`, memory and API each raise that ValueError; results in `csv_diagnostics.json`. No input text normalized or patched.

`SCHEMAS.md:73` documents same exact strings as source. Broad intent of accepting no-activity reports does not override observed mismatch.

## Profile gate components

Summariser failed before writing any `stages.json`, `total_wall_s.json`, or `gpu_util.json` (`profile_summarise.py:91-96`). Therefore task's success prerequisite for numeric gate evaluation is unmet.

| Component | Exact pipeline rule | Replay result |
| --- | --- | --- |
| Stage count | At least 3 validated rows | unknown |
| Wrapper by name | Case-insensitive token process, wrapper, telemetry, total, overall; whitespace, underscore, hyphen or boundary delimiters | unknown |
| Wrapper by wall | Any row with `0.98 * total_wall_s <= wall_s <= 1.02 * total_wall_s`, inclusive | unknown |
| Timed fraction | `min(1, sum(wall_s) / total_wall_s) >= 0.9` | unknown |
| GPU telemetry | Validated `gpu_util.json` array nonempty | unknown |
| Overall classification | Nonzero profile command exits as parse; absent output files also parse | parse |

Source: `pipeline.js:391-438`, especially validation lines 398-409, facts lines 423-425, wrapper/gate lines 432-435; nonzero command handling at line 455. Gate not called here, and no synthetic successful packet created. Raw telemetry exists, but existence alone is not validation of emitted gate input. Historical stage receipt `run9/control/stages/profile.json` also records FAIL / parse / exit 2; stage exit 2 differs from summariser exit 1.

## Command wall and run9 remaining budget

`raw_wall_s.json` contains:

```json
{"total_wall_s": 5621.4601993279975, "start_monotonic_s": 30267.410915074}
```

Command wall **5,621.4601993279975 s = 93.6910033221 min = 1.5615167220 h**: status `1_to_2h`. This is command alone, not outer profile receipt wall (`SCHEMAS.md:72`).

All 119 receipts read only for rc/wall/budget/timestamps; normalized inventory in `receipts_rc_wall.json`. Total receipt walls 38,388 s. That sum excludes model/controller gaps and is not elapsed run time.

Relevant original receipts:

| Receipt | rc | wall_s | budget_s at start |
| --- | ---: | ---: | ---: |
| 0006-setup | 1 | 57 | 42047 |
| 0041-setup | 1 | 169 | 41465 |
| 0076-setup | 1 | 195 | 40673 |
| 0111-setup | 0 | 266 | 39712 |
| 0112-anchors | 1 | 5091 | 39446 |
| 0113-upload | 0 | 541 | 34207 |
| 0114-anchors | 1 | 6159 | 33666 |
| 0115-upload | 0 | 1627 | 27430 |
| 0116-anchors | 0 | 7347 | 25803 |
| 0117-reproduce-freeze | 0 | 2710 | 18456 |
| 0118-upload | 0 | 2723 | 15745 |
| 0119-profile | 1 | 9728 | 13022 |

No concurrency receipt exists. Profile receipt ran 2026-11-01T10:46:42Z to 13:28:50Z. `run9/args.json` specifies no ceiling/budget overrides. `pipeline.js:160-168` uses `max(0, 43200 - floor(elapsed_s))`; concurrency receives freshly resolved **profile** budget (`pipeline.js:461-465`). It does not receive a new 12-hour allowance.

After profile, remaining time estimate is **13022 - 9728 = 3294 s**, before further controller work. Integer/fractional timing gives roughly one-second uncertainty, irrelevant here. Three sequential singles at measured command wall need **3 * 5621.4601993279975 = 16864.380597983993 s** (4.6845501661 h), exceeding remainder by **13570.380597983993 s**. Even one measured-duration single exceeds remainder. Hence `probe_singles_fit_run9: no` on requested measured-wall basis.

This is budget comparison, not measured concurrency result: no plain single runtimes saved, and profiler overhead/runtime variation could change unprofiled timings. Actual pipeline never reaches concurrency because parse fails (`pipeline.js:455-457`).

## Fresh-box counterfactual: unknown

First-attempt anchors success alone does not fix fresh setup/model/transfer/freeze/profile durations, plain-run timings, or MPS availability/startup. No measured fresh-box concurrency exists. Status therefore `unknown`, with conditional arithmetic below; these scenarios are not measurements.

Retain saved elapsed pre-first-anchors time (**43200 - 39446 = 3754 s**), replace all anchor attempts/repairs with saved successful anchor wall **7347 s**, retain freeze **2710 s**, profile upload **2723 s**, outer profile **9728 s**, and ignore small controller gaps:

```text
elapsed_before_probe = 3754 + 7347 + 2710 + 2723 + 9728 = 26262 s
probe_budget        = 43200 - 26262 = 16938 s
three_singles       = 16864.380597983993 s
remaining_margin    = 73.61940201600737 s
```

Under those assumptions, absent MPS and unchanged command durations, only singles barely fit. Probe attempts batches only when `n * T1 <= 0.9 * budget - elapsed` (`concurrency_probe.py:123-128`): after singles, guard remainder is **-1620.180597983992 s**. Both n=2 and n=4 skip. Batch CPU contention cannot be inferred from CPU count.

If MPS starts but first CPU-only single fails client-count verification, that discarded single plus three plain singles cost approximately **4 * T = 22485.84079731199 s**, exceeding same 16938 s budget by **5547.84079731199 s**, before daemon overhead. If daemon fails immediately, extra full command need not occur. Saved probe does not record whether MPS binary is on PATH.

A full sequence also cannot be priced as three singles plus six necessarily serialized command walls, nor as five identical command walls: actual batch walls depend on contention and are unknown. With no MPS retry, launching n=2 requires budget at least `(3T + 2T) / 0.9 = 31230.3344407111 s`; launching n=4 then also depends on measured n=2 wall. Plain three-single completion needs at least **16864.380597983993 s**, plus overhead. Fresh-box assumptions do not establish those inputs. Exact arithmetic in `budget_arithmetic.json`.

## Logical CPU count

`run9/agent/results/probe/probe.json:98`: `"nproc": 26`. Saved logical CPU availability count **26**, bucket `8_to_31`. No physical-core count inferred. `nvidia.gpus` lists one NVIDIA H100 PCIe at lines 116-118; GPU presence does not establish command CUDA activity or concurrent throughput.

## CPU-only command under MPS

Conditional answer **mps_failed_then_plain**; MPS client-count verification does not succeed merely because command exits 0.

`concurrency_probe.py:33` detects binary on PATH. Lines 99-114 try MPS then plain mode, with fresh MPS pipe/log directories and daemon startup. After each MPS run, lines 84-89 read control.log, count `NEW CLIENT [0-9]+ from user ` lines and require count increase at least copies launched. CPU-only command making no CUDA calls adds no CUDA MPS clients; zero increase fails single-run requirement. Missing/unreadable log also fails via lines 93-95. First failed single breaks at lines 116-121. Lines 136-145 stop MPS, set `mps_failed = True`, discard attempt directories/logs, repeat complete probe without MPS. Final normal fallback state has `mps: false`, `mps_failed: true`, provided budget permits reaching output. A timeout can interrupt fallback; no claim fallback finished in run9.

## Limits on scientific conclusions

`bounds.py:45-50,70-85` uses measured `concurrency.factor` for whole-workload methods, defaulting k to 1 when factor missing; feasibility threshold is bound >= 1.05. Stage GPU utilization does not manufacture factor. `SCHEMAS.md:112-130` documents those bounds; propose evidence requirements at `SCHEMAS.md:165-177` and `pipeline.js:680-687` require finite factor and verified MPS state for measured no-feasible-method outcome. No replay bounds or proposal executed. Saved parse failure and absent concurrency cannot establish useful headroom, lack of headroom, or any optimization result.

## Local command record

Inspection used `pwd`, targeted `ls -ld` / `ls -lah`, `wc -l`, `rg -n`, `nl -ba ... | sed -n ...`, exact-file `cat`, and head/tail for logs. Initial logical A/C and two-parent source path checks exited 1 because paths do not exist; resolved actual paths above. No large-directory recursive content scan performed. Small JSON receipts parsed with `python3 -I`; only rc/wall/budget/timestamps retained. Profile diagnostic `runpy.run_path(..., run_name="diagnostic_only")` loaded summariser functions without invoking main and checked each copied CSV independently; bytecode writing disabled.

Required summariser ran as subprocess; diagnostic invocation also loaded its source and called report_rows. Other Python work performed local copying, hashing, JSON validation and arithmetic. No baseline or probe code executed. `status.json` contains exactly requested eleven enum fields.
