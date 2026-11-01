You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run9_replay2/`. Change nothing else, contact no box, fetch nothing from the network, run no git commands, and do not run the baseline workload.

## Purpose
A previous reader (`run9_replay/`: read its REPORT.md and status.json first) replayed the merged U48 summariser (`dut/pipeline/m5/profile_summarise.py`, repository root two levels up) on copies of run9's saved profile inputs, and it exited nonzero. The operator suspects that Nsight Systems 2025's skip statements in `stats.log` use different wording from the summariser's expected phrases: Nsight is believed to print "does not contain CUDA kernel data", "does not contain GPU memory data" and "does not contain CUDA trace data" for the kernel, memory and API reports, while the summariser expects "CUDA kernel data", "CUDA memory data" and "CUDA API data". Confirm or refute this; do not assume it.

## Tasks
1. Copy run9's profile inputs (`run9/A/results/profile/out/profile/`: the three `stats_cuda_*.csv` files, `stats.log`, `raw_wall_s.json`, `gpu_util_raw.jsonl`) into `run9_replay2/u48/`. Import the summariser module from the repository (for example with `importlib` from its path) and call its `summarise()` on that directory so the exception is visible. Record which check raises.
2. For each report, classify the skip statement in `stats.log`.
3. Copy the summariser into `run9_replay2/patched_summarise.py`, change only the three activity phrases to the wording `stats.log` actually uses, copy the inputs again into `run9_replay2/patched/`, and run the patched copy on them with `python3 -I`. Record the exit code.
4. If the patched run succeeds, apply the profile gate exactly as `dut/pipeline/m5/pipeline.js` applies it (at least three stages; no process wrapper by name or by `wall_s` within 2% of `total_wall_s` inclusive; `timed_fraction >= 0.9`; `gpu_telemetry` true when `gpu_util.json` is non-empty) and record each component.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run9_replay2/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run9_replay2/REPORT.md` for the owner with the evidence (commands, exception, exit codes, the exact skip lines with paths shortened, gate arithmetic).
2. `run9_replay2/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"u48_failing_check"`: `"kernel_statement"`, `"memory_statement"`, `"api_statement"`, `"telemetry"`, `"wall"`, `"other"`, `"none"`
   - `"kernel_phrase"`: `"cuda_kernel_data"`, `"other"`, `"absent"`
   - `"memory_phrase"`: `"cuda_memory_data"`, `"gpu_memory_data"`, `"other"`, `"absent"`
   - `"api_phrase"`: `"cuda_api_data"`, `"cuda_trace_data"`, `"other"`, `"absent"`
   - `"patched_exit"`: `"zero"`, `"nonzero"`, `"not_run"`
   - `"stage_count_ok"`: `"yes"`, `"no"`, `"unknown"`
   - `"wrapper_rule"`: `"none"`, `"name"`, `"within_2pct"`, `"both"`, `"unknown"`
   - `"timed_fraction_ok"`: `"yes"`, `"no"`, `"unknown"`
   - `"gpu_telemetry"`: `"true"`, `"false"`, `"unknown"`
   - `"gate_after_fix"`: `"pass"`, `"numeric"`, `"parse"`, `"unknown"`

   No other keys and no free text.

Finish within 10 minutes. End with a final reply that is exactly the contents of status.json.
