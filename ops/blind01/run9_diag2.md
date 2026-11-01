You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run9_diag2/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need.

## What the operator knows (metadata only)
Run9's profile stage failed: the fixed profiler command (`dut/pipeline/m5/profile_nsys.sh`) exited rc 1 late in the command, with no `infra.json`. A first diagnosis (`run9_diag/status.json` and its REPORT.md, which you may read) found the failure source is the profiler, the log tail has no cause, and the smallest fix is a profiler fix. Reading the code: every failing step before the summariser triggers the ERR trap (infra.json, exit 2), so rc 1 without infra.json means `dut/pipeline/m5/profile_summarise.py` failed, and its `main()` swallows the exception and prints only "invalid profiler output". The operator needs the exact check that failed to write the smallest fix.

## Do
1. Find the fetched profile output for run9 (the profile stage's results folder, `out/profile/`): list its files and sizes. Note which of `stats_cuda_gpu_kern_sum.csv`, `stats_cuda_gpu_mem_time_sum.csv`, `stats_cuda_api_sum.csv`, `stats.log`, `raw_wall_s.json`, `gpu_util_raw.jsonl` and `nsys-version.txt` are present.
2. Copy only those small files (each under 20 MB; never copy `.nsys-rep`, `.sqlite` or other large files) into `run9_diag2/work/`.
3. Run the summariser's `summarise()` on `run9_diag2/work/` with the exception shown, without editing the pipeline's file, for example:
   `python3 -I -c "import sys, traceback; sys.path.insert(0, '<repo>/dut/pipeline/m5'); import profile_summarise as p; from pathlib import Path; p.summarise(Path('run9_diag2/work'))"`
   (run from this directory with `<repo>` the repository root, two levels up). Record the exception type, message and the line in profile_summarise.py that raised it.
4. Inspect the offending input (the CSV header and the first rows of the failing report, the telemetry line, or whatever raised) and decide whether the input is a valid Nsight Systems output format that the summariser does not handle, or genuinely invalid or truncated data.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run9_diag2/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run9_diag2/REPORT.md` for the owner: files present, the exception and line, the offending input excerpt (headers and at most a few rows), and the smallest change to `profile_summarise.py` or `profile_nsys.sh` that would accept every valid format seen here while still rejecting invalid data.
2. `run9_diag2/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"stats_files_present"`: `"all"`, `"some"`, `"none"`
   - `"reproduces_locally"`: `"yes"`, `"no"`, `"unknown"`
   - `"summariser_error"`: `"invalid_csv_row"`, `"missing_csv_header"`, `"missing_name_column"`, `"unknown_time_unit"`, `"missing_report_file"`, `"invalid_duration"`, `"invalid_telemetry"`, `"invalid_wall_or_origin"`, `"json_decode"`, `"other"`, `"none"`, `"unknown"`
   - `"failing_input"`: `"kern_sum"`, `"mem_time_sum"`, `"api_sum"`, `"telemetry"`, `"raw_wall"`, `"other"`, `"unknown"`
   - `"input_valid_nsys_format"`: `"yes"`, `"no"`, `"unknown"`
   - `"fix_location"`: `"profile_summarise"`, `"profile_nsys"`, `"both"`, `"unknown"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
