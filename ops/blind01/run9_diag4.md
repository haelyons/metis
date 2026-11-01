You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run9_diag4/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need (logs by head, tail or grep).

## What the operator knows (metadata only)
Run9's profile failed because Nsight Systems 2025 wrote empty kernel, memory and API summary CSVs and stats.log says each report was SKIPPED for lack of CUDA data (`run9_diag2/`, `run9_diag3/`: read their status.json and REPORT.md). Before changing the summariser to count such reports as zero, the operator must know whether the workload truly does no CUDA work, or whether the GPU was busy and Nsight did not capture it. Counting a missed capture as zero would record a false host-only profile.

## Read
- the profile output under run9 (`out/profile/`: `gpu_util_raw.jsonl`, `baseline.log`, `stats.log`, `nsys-version.txt`, `raw_wall_s.json`), the reproduce anchors logs and harness scripts (`run_command.sh`, `run_anchors.sh`, `setup.sh`), the box probe, intake's records (baseline.json, EXECUTION.json) and `intake_mirror/BRIEF_run5.md`
- `dut/pipeline/m5/profile_nsys.sh` and `dut/pipeline/m5/SCHEMAS.md`, read-only (repository root two levels up)

## Questions
1. During the profiled command's own interval (raw_wall_s.json's start and wall on the telemetry clock), what was GPU utilisation?
2. Which compute API does the baseline use as configured in this run: CUDA (directly or through a library such as cuBLAS, PyTorch, JAX, OpenMM's CUDA platform), OpenCL, another GPU API, or CPU only? Is that the published configuration's choice, or did the harness or intake select a CPU or non-CUDA path (for example a CPU platform fallback because a GPU platform failed)?
3. Do baseline.log or stats.log show Nsight failing to inject or trace (warnings about injection, unsupported API, static CUDA runtime, processes not traced, or detached children)?
4. Is the published baseline described as a GPU workload?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run9_diag4/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run9_diag4/REPORT.md` for the owner with the evidence (file paths, log lines, numbers).
2. `run9_diag4/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"gpu_util_during_command"`: `"zero"`, `"under_10pct"`, `"10_to_50pct"`, `"over_50pct"`, `"unknown"` (mean over the interval)
   - `"compute_api"`: `"cuda"`, `"opencl"`, `"other_gpu"`, `"cpu_only"`, `"unknown"`
   - `"api_choice"`: `"published"`, `"harness_or_intake_fallback"`, `"unknown"`
   - `"nsys_capture_problem"`: `"yes"`, `"no"`, `"unknown"`
   - `"published_gpu_workload"`: `"yes"`, `"no"`, `"unknown"`
   - `"empty_reports_true_finding"`: `"yes"` (no CUDA work happened, so zero CUDA time is correct), `"no"` (CUDA work happened and was missed), `"unknown"`

   No other keys and no free text.

Finish within 10 minutes. End with a final reply that is exactly the contents of status.json.
