# Run9 second saved-input replay

Date: 2026-11-01. Read `run9_replay/REPORT.md` and `run9_replay/status.json` before inspecting the source or inputs. The suspected wording mismatch is **confirmed for memory and API**, while the kernel wording already matches. Direct U48 invocation fails first at the memory report. Changing only the activity phrases makes the summariser exit **0**, but the exact pipeline profile validator still returns **`numeric`** because the residual host stage occupies the entire command wall time.

## Scope and input provenance

All writes are under `run9_replay2/`. No baseline workload, network request, box contact, git command, credential file, `.keys` file, or `~/.codex/` access occurred. Existing launcher logs in the output directory were left untouched. Original inputs and repository summariser were not changed.

The requested logical `run9/A/results/profile/out/profile/` path does not exist in this checkout. The saved inputs are at `run9/agent/results/profile/out/profile/`, consistent with the prior replay. The repository root is `/home/hal/dev/interp/metis`, three parents above the working directory, rather than two. The imported module is `/home/hal/dev/interp/metis/dut/pipeline/m5/profile_summarise.py`.

Copied the following six files independently into both `run9_replay2/u48/` and `run9_replay2/patched/` with `shutil.copyfile`:

| Input | Bytes |
| --- | ---: |
| `stats_cuda_gpu_kern_sum.csv` | 0 |
| `stats_cuda_gpu_mem_time_sum.csv` | 0 |
| `stats_cuda_api_sum.csv` | 0 |
| `stats.log` | 928 |
| `raw_wall_s.json` | 74 |
| `gpu_util_raw.jsonl` | 1,424,183 |

`input_manifest.json` records source sizes and SHA-256 hashes. Both copies were checked against those hashes. Source inputs and original module were checked again after execution; all unchanged. The large baseline report/database were not read or copied.

## Commands and direct exception

Commands below run from the original working directory. `replay.py` performs the six-file copies, direct import replay, separate report diagnostics, phrase-only patch, patched subprocess, and hash checks:

```sh
python3 -I run9_replay2/replay.py
node run9_replay2/gate_replay.cjs
```

Both orchestration commands exited **0**. Their child results are recorded separately: direct U48 child **1**, patched summariser child **0**. The replay's subprocess arguments are recorded exactly in `execution.json`; equivalent commands with paths shortened relative to the working directory are:

```sh
python3 -I run9_replay2/u48_direct.py ../../../dut/pipeline/m5/profile_summarise.py run9_replay2/u48
python3 -I run9_replay2/patched_summarise.py run9_replay2/patched
```

`u48_direct.py` loads the repository module with `importlib.util.spec_from_file_location`, disables bytecode writes, and calls `module.summarise(Path(sys.argv[2]))` directly. It does not call the CLI's exception-catching `main()`. Its stderr, with absolute prefixes shortened here, is:

```text
Traceback (most recent call last):
  File "run9_replay2/u48_direct.py", line 8, in <module>
    module.summarise(Path(sys.argv[2]))
  File "dut/pipeline/m5/profile_summarise.py", line 60, in summarise
    for name, value in report_rows(directory / "stats_cuda_gpu_mem_time_sum.csv"):
  File "dut/pipeline/m5/profile_summarise.py", line 47, in report_rows
    raise ValueError("missing CSV header")
ValueError: missing CSV header
```

Full traceback, including interpreter caret annotations, is in `u48_direct.stderr.txt`. The failing check is **`memory_statement`**: the empty memory CSV's skip phrase fails the check at lines 24–28, then header validation raises at line 47. Kernel parsing has already succeeded; API parsing has not yet been reached by `summarise()`. Separate `report_rows()` calls establish kernel returns no rows and both memory and API raise `ValueError("missing CSV header")`; see `report_diagnostics.json`. Wall and telemetry are not the first failure.

## Skip statements and phrase-only patch

These are the exact skip lines from `run9_replay2/u48/stats.log` (identical to the source log). Their already-relative database path is retained; absolute checkout prefixes are omitted from evidence paths throughout this report.

```text
SKIPPED: out/profile/baseline.sqlite does not contain CUDA kernel data.
SKIPPED: out/profile/baseline.sqlite does not contain GPU memory data.
SKIPPED: out/profile/baseline.sqlite does not contain CUDA trace data.
```

They occur at log lines 4, 8, and 12, respectively, after processing the corresponding kernel, memory, and API reports. Report-script paths in this same saved log identify Nsight Systems `2025.3.1`. This establishes the wording in these saved artifacts, without asserting how every Nsight version behaves.

| Report | Original phrase | Observed phrase | Classification | Original accepts empty CSV |
| --- | --- | --- | --- | --- |
| Kernel | `CUDA kernel data` | `CUDA kernel data` | `cuda_kernel_data` | yes |
| Memory | `CUDA memory data` | `GPU memory data` | `gpu_memory_data` | no |
| API | `CUDA API data` | `CUDA trace data` | `cuda_trace_data` | no |

`patched_summarise.py` is a copy of the repository module with its three-entry activity table set to those observed phrases. Kernel already matches, so only two string literals change. No code logic or other text changes. `phrase_patch.diff` contains the complete diff:

```diff
         activity = {"stats_cuda_gpu_kern_sum.csv": "CUDA kernel data",
-                    "stats_cuda_gpu_mem_time_sum.csv": "CUDA memory data",
-                    "stats_cuda_api_sum.csv": "CUDA API data"}[file.name]
+                    "stats_cuda_gpu_mem_time_sum.csv": "GPU memory data",
+                    "stats_cuda_api_sum.csv": "CUDA trace data"}[file.name]
```

The patched subprocess ran with **`python3 -I`**, exited **0**, and emitted no stdout or stderr. It produced `patched/stages.json`, `patched/total_wall_s.json`, and `patched/gpu_util.json`. All three report totals are zero because the saved CSVs are empty and their skip statements are now accepted. No durations were fabricated.

## Exact profile gate and arithmetic

`gate_replay.cjs` extracts the complete, unchanged `validateProfile()` function from `dut/pipeline/m5/pipeline.js` and evaluates it locally with Node's `vm`. The extracted source is saved as `validateProfile.source.js`. The JSON reader and `nonnegative` helper match the pipeline definitions. Its destination is a local directory whose `out/profile` symlink points to `patched/`; the validator's packet is written only to `run9_replay2/gate/profile-packet.json`. No surrounding pipeline, upload, workload, concurrency probe, or remote operation runs. The validator command exits **0**, with validator return value **`numeric`**. Full component evidence is in `gate_evidence.json`.

The validator's type, numeric, telemetry, and stage-window checks pass. Its output has `profile_complete: true`. Input stage values are:

| Stage | Kind | `wall_s` | `gpu_s` |
| --- | --- | ---: | ---: |
| `kernels` | compute | 0 | 0 |
| `memcpy H2D` | transfer | 0 | 0 |
| `memcpy D2H` | transfer | 0 | 0 |
| `CUDA API host time` | other | 0 | null |
| `other host time` | other | 5621.4601993279975 | null |

The gate is applied exactly as `pipeline.js:398–435` specifies, including zero-duration stages and inclusive wall bounds:

| Component | Arithmetic / evidence | Result |
| --- | --- | --- |
| Stage count | `5 >= 3` | yes |
| Wrapper by name | Case-insensitive `(?:^|[\s_-])(?:process|wrapper|telemetry|total|overall)(?:$|[\s_-])`; no stage matches | false |
| Wrapper by wall | Inclusive interval `[0.98 * 5621.4601993279975, 1.02 * 5621.4601993279975]` = `[5509.030995341437, 5733.889403314558]`; `other host time = 5621.4601993279975` lies inside | true |
| Timed fraction | `min(1, (0 + 0 + 0 + 0 + 5621.4601993279975) / 5621.4601993279975) = 1`; `1 >= 0.9` | yes |
| GPU telemetry | All emitted samples validate; `gpu_util.json` has `38622 > 0` samples | true |
| Overall | `5 >= 3 && !true && 1 >= 0.9 && true` is false | numeric |

Thus `wrapper_rule` is **`within_2pct`**, with no name match. Phrase repair resolves parsing but does not pass the profile gate. Nonempty telemetry establishes the gate's telemetry fact, not positive GPU activity or an optimization result.
