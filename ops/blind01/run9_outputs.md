You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run9_outputs/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need (logs by head, tail or grep). Never copy `.nsys-rep`, `.sqlite` or other files over 10 MB.

## Purpose
Earlier readers (`run9_units/`, `run9_par/`, `run9_replay2/`: read their REPORT.md and status.json first) found that run9's measured command runs 8 to 63 distinct inputs ("units") one after another, that a published option selects a subset of units, and that a unit's output is repeatable bit for bit. The operator is specifying a probe that runs a few units through the published subset option, serially and concurrently, each invocation in its own working directory with an empty `out/`, and compares each unit's output files byte for byte against the same files in run9's reproduce outputs (`run9/A/results/reproduce/out/`, which equal the frozen baseline outputs). It also checks a proposed "host-only" profile rule against run9's saved profile files. Answer neutrally; `unknown` is correct whenever the evidence does not settle a question.

## Read
- the earlier readers' reports, the brief as run (`intake_mirror/BRIEF_run5.md`), run9's intake records (`run9/A/intake/`), harness scripts (`run9/A/harness/`), the published source and configuration as saved under run9, the reproduce logs and outputs (`run9/A/results/reproduce/`), and run9's profile outputs (`run9/A/results/profile/out/profile/`)
- for question 7, the current summariser `/home/hal/dev/interp/metis/dut/pipeline/m5/profile_summarise.py` (read and run it; do not edit it)

## Questions
1. Does a run write a separate output file (or files) for each unit, one combined file covering all units, or both (per-unit files plus a combined summary)?
2. If per-unit files exist: is each file's path (relative to `out/`) determined by the unit alone, so that the same unit writes the same path in a full run and in a subset run?
3. Do per-unit result files contain anything that differs between two runs of the same unit (timestamps, wall times, absolute paths, host names, process ids, thread counts)?
4. Do run9's saved reproduce logs or outputs record each unit's own cost in seconds, for all units, some, or none?
5. Can the published subset option take the units' identifiers directly as command-line arguments, and are those identifiers made only of ASCII letters, digits and `._:+=-`, at most 128 characters each? Or does selection need a file, or something else?
6. How many units did run9's measured command run?
7. Host-only rule. Copy only run9's small profile files (`stats_*.csv`, `stats.log`, `raw_wall_s.json`, `gpu_util_raw.jsonl`, and any other small file the summariser reads) into `run9_outputs/profile/` (or reuse the copies under `run9_replay2/` if they are complete), run `python3 /home/hal/dev/interp/metis/dut/pipeline/m5/profile_summarise.py run9_outputs/profile`, and read its `stages.json`, `total_wall_s.json` and `gpu_util.json`. Report: whether the rows `kernels`, `memcpy H2D`, `memcpy D2H` and `CUDA API host time` all have `wall_s` 0 and `gpu_s` 0 or null; whether `gpu_util.json` has at least one sample; whether every sample's `util` is exactly 0; and whether the `other host time` row's `wall_s` is within 2% of `total_wall_s`.
8. Does a unit's computation in one invocation read any state left by earlier units of the same invocation (a shared random stream, an in-process cache, a warm start), so that a unit run alone or in a different order could produce different output?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run9_outputs/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run9_outputs/REPORT.md` for the owner with the evidence (file paths, code and log lines, numbers), separating measured, read from code or documents, and inferred.
2. `run9_outputs/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"per_unit_outputs"`: `"separate"`, `"combined"`, `"both"`, `"unknown"`
   - `"unit_paths_stable"`: `"yes"`, `"no"`, `"not_applicable"`, `"unknown"`
   - `"run_specific_content"`: `"no"`, `"yes"`, `"unknown"`
   - `"per_unit_costs_recorded"`: `"all_units"`, `"some_units"`, `"none"`, `"unknown"`
   - `"subset_ids"`: `"args_safe"`, `"args_unsafe_chars"`, `"needs_file"`, `"other"`, `"unknown"`
   - `"units_count"`: `"under_4"`, `"4_to_7"`, `"8_to_15"`, `"16_to_63"`, `"64_or_more"`, `"unknown"`
   - `"cuda_rows_zero"`: `"yes"`, `"no"`, `"unknown"`
   - `"telemetry_samples"`: `"none"`, `"some"`, `"unknown"`
   - `"telemetry_all_zero"`: `"yes"`, `"no"`, `"unknown"`
   - `"other_host_within_2pct"`: `"yes"`, `"no"`, `"unknown"`
   - `"cross_unit_state"`: `"no"`, `"yes"`, `"unknown"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
