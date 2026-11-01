You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run9_replay/`. Change nothing else, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need (logs by head, tail or grep). Do not run the baseline workload.

## Purpose
The operator wants to know what run9's saved artifacts can establish without fresh execution. Answer neutrally: `unknown` is a correct answer whenever the saved files do not settle a question.

Unit U48 (now merged) changed `dut/pipeline/m5/profile_summarise.py` so that an absent, empty or whitespace-only kernel, memory or API CSV counts as zero when `stats.log` states that the report does not contain its own activity. Run9's profile stopped with `parse` before this change.

## Read
- run9's saved profile output (`run9/A/results/profile/out/profile/`: the three CSVs, `stats.log`, `raw_wall_s.json`, `gpu_util_raw.jsonl`, `nsys-version.txt`) and run9's receipts' rc and wall_s (`run9/C/receipts/`)
- run9's collected box probe (`run9/A/results/probe/probe.json`)
- `dut/pipeline/m5/profile_summarise.py`, `dut/pipeline/m5/pipeline.js` (function validating the profile and the concurrency probe call), `dut/pipeline/m5/concurrency_probe.py`, `dut/pipeline/m5/bounds.py` and `dut/pipeline/m5/SCHEMAS.md` (profile, concurrency probe, bounds and propose sections), read-only (repository root two levels up)

## Tasks
1. Copy the profile input files (not the large raw report) into `run9_replay/profile/` and run `python3 -I <repo>/dut/pipeline/m5/profile_summarise.py run9_replay/profile`. Record its exit code.
2. If it succeeds, apply the profile gate exactly as `pipeline.js` applies it (at least three stages, no process wrapper by name or by `wall_s` within 2% of `total_wall_s` inclusive, `timed_fraction >= 0.9`, `gpu_telemetry` true) and record each component.
3. Using the measured command wall (`raw_wall_s.json`) and the run9 receipts, judge whether the concurrency probe as specified (three sequential single runs of the same command, then batches of 2 and 4, under the profile budget = time left before the 43200 s run ceiling) could have completed its single runs in the time left after profile in run9, and whether it could within 43200 s on a fresh box whose reproduce stage succeeded at the first anchors attempt.
4. From probe.json, the box's CPU count (logical CPUs).
5. Read `concurrency_probe.py`: when `nvidia-cuda-mps-control` is on PATH and the command makes no CUDA calls, would the MPS client-count verification succeed, or would the probe record `mps_failed: true` and repeat without MPS?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run9_replay/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run9_replay/REPORT.md` for the owner with the evidence (commands, exit codes, numbers, code lines).
2. `run9_replay/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"summariser_exit_u48"`: `"zero"`, `"nonzero"`, `"not_run"`
   - `"stage_count_ok"`: `"yes"`, `"no"`, `"unknown"`
   - `"wrapper_rule"`: `"none"`, `"name"`, `"within_2pct"`, `"both"`, `"unknown"`
   - `"timed_fraction_ok"`: `"yes"`, `"no"`, `"unknown"`
   - `"gpu_telemetry"`: `"true"`, `"false"`, `"unknown"`
   - `"gate_after_u48"`: `"pass"`, `"numeric"`, `"parse"`, `"unknown"`
   - `"command_wall"`: `"under_10min"`, `"10_to_60min"`, `"1_to_2h"`, `"2_to_4h"`, `"over_4h"`, `"unknown"` (raw_wall_s, the profiled command alone)
   - `"probe_singles_fit_run9"`: `"yes"`, `"no"`, `"unknown"`
   - `"probe_fits_fresh_box"`: `"singles_and_batches"`, `"singles_only"`, `"no"`, `"unknown"`
   - `"box_logical_cpus"`: `"under_8"`, `"8_to_31"`, `"32_to_63"`, `"64_plus"`, `"unknown"`
   - `"mps_for_cpu_only_command"`: `"verified"`, `"mps_failed_then_plain"`, `"unknown"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
