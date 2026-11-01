You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run9_diag3/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands.

## What the operator knows (metadata only)
`run9_diag2/status.json` (read it and its REPORT.md; the copied files are in `run9_diag2/work/`): run9's profile failed because `dut/pipeline/m5/profile_summarise.py` raised "missing CSV header" on `stats_cuda_gpu_kern_sum.csv`, reproduced locally; the input is a valid Nsight Systems format and the fix belongs in profile_summarise.py. The operator will write the fix as a contract for an implementer and a test author who cannot see this experiment, so the operator needs the format variant as categories.

## Do
Using only `run9_diag2/work/` and the two REPORT.md files, classify the kernel summary file and the other inputs. You may run `profile_summarise.py`'s functions on copies inside `run9_diag3/work/` (copy from `run9_diag2/work/`), including a copy where you treat the kernel report as having no rows, to see whether the rest of the summary then succeeds. Do not edit the pipeline's files.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run9_diag3/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run9_diag3/REPORT.md` for the owner with the evidence.
2. `run9_diag3/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"kern_file_state"`: `"empty"` (zero bytes or only whitespace), `"status_lines_only"` (nsys text, no CSV header row), `"header_unmatched"` (a CSV header row exists but the summariser's duration-column regex does not match it), `"other"`
   - `"stats_log_says_no_kernel_data"`: `"yes"` (stats.log states the report has no CUDA kernel data, e.g. "does not contain CUDA kernel data"), `"no"`, `"unknown"`
   - `"stats_log_says_skipped"`: `"yes"` (stats.log has a SKIPPED line for the kernel report), `"no"`, `"unknown"`
   - `"duration_column_form"`: `"not_applicable"` (no header), `"unit_not_in_parentheses"`, `"different_column_word"`, `"no_duration_column"`, `"other"`
   - `"other_reports_parse"`: `"both"` (mem_time_sum and api_sum both parse with the current code), `"one"`, `"neither"`, `"unknown"`
   - `"succeeds_if_kern_has_no_rows"`: `"yes"`, `"no"`, `"unknown"`
   - `"workload_has_cuda_kernels"`: `"yes"`, `"no"`, `"unknown"` (from the telemetry, the API and memcpy reports and the logs)
   - `"nsys_version"`: `"2023"`, `"2024"`, `"2025"`, `"other"`, `"unknown"` (year prefix from nsys-version.txt)

   No other keys and no free text.

Finish within 10 minutes. End with a final reply that is exactly the contents of status.json.
