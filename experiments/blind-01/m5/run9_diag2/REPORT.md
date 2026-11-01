# Run9 profiler parser diagnosis

Local diagnosis only. All writes confined to `run9_diag2/`. No workloads, network access, box contact, git commands, credential reads, or pipeline edits. Repository root is `../../..` from this working directory, rather than the prompt's two-level description.

## Fetched files

Profile output: `run9/agent/results/profile/out/profile/`. Directory listing reports these regular files and exact byte sizes:

| File | Bytes | Copied to `work/` |
| --- | ---: | --- |
| `baseline.log` | 818,032 | No; unnecessary |
| `baseline.nsys-rep` | 102,508,216 | No; binary trace excluded |
| `baseline.sqlite` | 1,271,185,408 | No; database excluded |
| `gpu_util_raw.jsonl` | 1,424,183 | Yes |
| `nsys-version.txt` | 57 | Yes |
| `raw_wall_s.json` | 74 | Yes |
| `stats.log` | 928 | Yes |
| `stats_cuda_api_sum.csv` | 0 | Yes |
| `stats_cuda_gpu_kern_sum.csv` | 0 | Yes |
| `stats_cuda_gpu_mem_time_sum.csv` | 0 | Yes |

All seven requested files are present. Only those seven were copied into `work/`, each below 20 MB. SHA-256 comparisons confirm each copy equals its source. Large trace/database files were listed, never opened or copied.

## Exact failure

Unmodified summariser reproduced rc 1 with:

```sh
python3 -I -B -c "import sys; sys.path.insert(0, '/home/hal/dev/interp/metis/dut/pipeline/m5'); import profile_summarise as p; from pathlib import Path; p.summarise(Path('run9_diag2/work'))"
```

`-B` prevents bytecode writes beside the imported pipeline module. Full exception is saved in [reproduce_traceback.txt](reproduce_traceback.txt); stdout was empty.

```text
profile_summarise.py:57, summarise:
    kernels = sum(value for _, value in report_rows(directory / "stats_cuda_gpu_kern_sum.csv"))
profile_summarise.py:46, report_rows:
    raise ValueError("missing CSV header")
ValueError: missing CSV header
```

Exception type: `ValueError`. Message: `missing CSV header`. Raising line: `/home/hal/dev/interp/metis/dut/pipeline/m5/profile_summarise.py:46`. Failing input: kernel summary, `stats_cuda_gpu_kern_sum.csv`. Memory/API reports have the same empty-file condition but execution stops before reading them.

`report_rows()` checks for absent activity only when its CSV does not exist (lines 22–27). Here the CSV exists with zero bytes. Header search finds nothing; the fallback sees no `SKIPPED` text inside the CSV and raises. `main()` lines 105–107 suppress the reason, printing only `invalid profiler output`. `profile_nsys.sh` lines 139–141 disable the ERR trap immediately before invoking the summariser, explaining rc 1 without `infra.json`.

## Offending input and validity

All three CSVs contain exactly zero bytes: no header, no rows, no excerpt to quote. Corresponding `stats.log` excerpt, preserving actual report/skip text:

```text
Processing [out/profile/baseline.sqlite] with [/opt/nvidia/nsight-systems-cli/2025.3.1/target-linux-x64/reports/cuda_gpu_kern_sum.py] to [out/profile/stats_cuda_gpu_kern_sum.csv]... PROCESSED (EMPTY RESULTS)
SKIPPED: out/profile/baseline.sqlite does not contain CUDA kernel data.
Processing [out/profile/baseline.sqlite] with [/opt/nvidia/nsight-systems-cli/2025.3.1/target-linux-x64/reports/cuda_gpu_mem_time_sum.py] to [out/profile/stats_cuda_gpu_mem_time_sum.csv]... PROCESSED (EMPTY RESULTS)
SKIPPED: out/profile/baseline.sqlite does not contain GPU memory data.
Processing [out/profile/baseline.sqlite] with [/opt/nvidia/nsight-systems-cli/2025.3.1/target-linux-x64/reports/cuda_api_sum.py] to [out/profile/stats_cuda_api_sum.csv]... PROCESSED (EMPTY RESULTS)
SKIPPED: out/profile/baseline.sqlite does not contain CUDA trace data.
```

Blank lines between records omitted. `nsys-version.txt` contains:

```text
NVIDIA Nsight Systems version 2025.3.1.90-253135822126v0
```

This is valid Nsight **empty-result export behavior**, evidenced separately for every requested report by `PROCESSED (EMPTY RESULTS)` and an explicit no-activity skip. The files do not represent truncated nonempty tables. Zero-byte CSV alone would not establish validity; matching exporter diagnostics do. No header spelling or duration unit caused this failure.

Two additional compatibility mismatches would matter after fixing the first check: the current missing-file branch expects `CUDA memory data` and `CUDA API data`; this exporter says `GPU memory data` and `CUDA trace data`.

## Smallest concrete fix

[profile_summarise.patch](profile_summarise.patch) is a reviewable candidate, **not applied** to the pipeline. Change only `report_rows()` in `profile_summarise.py`:

1. Apply absent-activity handling when the report is missing **or exactly zero bytes**.
2. Recognize report-specific diagnostics: kernel = `CUDA kernel data`; memory = `CUDA memory data` or `GPU memory data`; API = `CUDA API data` or `CUDA trace data`.
3. Require a full `SKIPPED: <path> does not contain <matching activity>.` line in this profile directory's `stats.log`. Missing/unrelated diagnostics must not convert an empty file into zero activity. Missing files without evidence still raise; unexplained empty files still raise `missing CSV header`.
4. Keep normal CSV parsing for nonempty reports. Replace the existing blanket headerless-CSV `SKIPPED` fallback with `raise ValueError("missing CSV header")`; an arbitrary occurrence of `SKIPPED` must not excuse corrupt input. All valid skips observed here are in `stats.log`, with empty CSVs.

This accepts every valid format observed here and preserves the older no-activity wording already anticipated by the code. Do not accept every empty CSV, insert fabricated duration rows, or ignore CSV parse failures. No change to `profile_nsys.sh` is needed to resolve this exception. Logging the exception detail from `main()` would improve future diagnosis, but is separate from the acceptance fix.

## Local validation

Candidate source was loaded in memory from the unchanged pipeline source plus the saved patch; no replacement pipeline module was written. Summarisation ran only against temporary copies inside `run9_diag2/`, subsequently removed. Results saved in [fix_validation.txt](fix_validation.txt):

- Full seven-file observed fixture succeeds; all four CUDA timing rows are zero. Measured host remainder is 5,621.4601993279975 s; 38,622 telemetry samples lie inside the measured wall interval.
- Missing reports with matching observed skip diagnostics succeed. Historical memory/API skip wording succeeds.
- Empty report without evidence, wrong-activity skip, nonempty headerless garbage containing `SKIPPED`, malformed CSV row, negative duration, and nonfinite duration all fail.
- Nonempty duration CSVs still parse correctly for `ns`, `us`, `µs`, `ms`, and `s`.

These checks establish this summariser fix against saved artifacts. They do not establish downstream pipeline acceptance or require another scientific run.
