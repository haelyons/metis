You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run9_par/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need (logs by head, tail or grep).

## Purpose
Earlier readers found that run9's baseline runs on the CPU only, as published, with zero GPU utilisation during the profiled command. The operator must not over-read this. The owner's question is whether parallel computation could improve this study's scientific outcome under time and cost limits. The pipeline's methods are "data-parallel over inputs", "ensembles", "batching", "multi-GPU" and "pipelining" (`dut/pipeline/m5/SCHEMAS.md`, bounds section). Its bound for the first three comes from running copies of the unchanged command concurrently on one box. Separate what was measured from what is inferred from code or documents, and what is unknown. `unknown` is a correct answer whenever the evidence does not settle a question; do not lean toward any answer.

## Read
- the brief as run (`intake_mirror/BRIEF_run5.md`), run9's intake records (`run9/A/intake/`), the harness scripts (`run9/A/harness/`), the published source and configuration as installed by setup where saved under run9, the reproduce and profile logs (`run9/A/results/reproduce/`, `run9/A/results/profile/out/profile/baseline.log`, `stats.log`, `raw_wall_s.json`), and run9's box probe (`run9/A/results/probe/probe.json`)
- `dut/pipeline/m5/SCHEMAS.md` (profile, concurrency probe, bounds, evaluate sections), read-only (repository root two levels up)

## Questions
1. Threads: as configured in run9, does the baseline use one CPU thread or several (threading, OpenMP, BLAS threads, multiprocessing)? On what evidence: a measurement in saved logs or telemetry, or code, configuration and documents only?
2. Work structure: does the measured command consist of units (replicates, seeds, inputs, parameter points, chains) whose computations are independent until results are combined? How many at run9's representative scale? Are they run one after another?
3. Is there any saved per-unit or progress timing from which per-unit wall time can be read?
4. Does the published study (or its upstream software) offer a GPU path for this computation?
5. If more independent units completed in the same wall time, would the study's scientific result change: a tighter uncertainty on the same quantity, a closer match to the published protocol's scale, or neither?
6. Does the published study report an uncertainty or precision for its main quantity that could serve as an equal-outcome target (the same precision reached at lower cost or time)?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run9_par/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run9_par/REPORT.md` for the owner with the evidence (file paths, log lines, code lines, numbers), separating measured, inferred and unknown.
2. `run9_par/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"cpu_threads"`: `"single"`, `"multi"`, `"unknown"`
   - `"cpu_threads_basis"`: `"measured"`, `"code_or_docs"`, `"none"`
   - `"independent_units"`: `"yes"`, `"partly"`, `"no"`, `"unknown"`
   - `"units_at_run_scale"`: `"one"`, `"2_to_7"`, `"8_to_63"`, `"64_plus"`, `"unknown"`
   - `"units_order"`: `"serial"`, `"concurrent"`, `"not_applicable"`, `"unknown"`
   - `"per_unit_timing_saved"`: `"yes"`, `"no"`
   - `"gpu_path_published"`: `"yes"`, `"no"`, `"unknown"`
   - `"more_units_changes_result"`: `"tighter_uncertainty"`, `"closer_to_published_scale"`, `"both"`, `"neither"`, `"unknown"`
   - `"published_uncertainty"`: `"yes"`, `"no"`, `"unknown"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
