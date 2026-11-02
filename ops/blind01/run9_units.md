You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run9_units/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need (logs by head, tail or grep).

## Purpose
Earlier readers (`run9_par/`, `run9_scale/`, `run9_scale2/`: read their REPORT.md and status.json first) found that run9's measured command runs 8 to 63 independent units one after another, that run9 reduced "replicates or samples" by 10 to 100 times, and that more units would bring the run "closer to the published scale". The owner suspects those categories merged distinctions that matter. The operator is designing a small comparison of the same few units run serially and concurrently on the box, holding inputs and per-unit configuration fixed and checking outputs. Answer neutrally; `unknown` is correct whenever the evidence does not settle a question.

## Read
- the earlier readers' reports, the brief as run (`intake_mirror/BRIEF_run5.md`), run9's intake records (`run9/A/intake/`), harness scripts (`run9/A/harness/`), the published source and configuration as installed where saved under run9, the reproduce logs and outputs (`run9/A/results/reproduce/`), and `run9/A/results/profile/out/profile/baseline.log`

## Questions
1. What is one unit: a distinct input (a different case, dataset or system), a repeated trial of the same input and configuration (another seed or replicate), an additional candidate generated for the same input (later selected or ranked), a parameter point, a chain or walker of one sampling process, a mix, or other?
2. Which dimension did run9 reduce relative to the published protocol: the number of inputs, trials per input, candidates per input, parameter points, the length of each unit, or several?
3. If that dimension were expanded to the published value, what would change: coverage (more inputs or conditions covered), precision (a tighter estimate of the same quantity), the outcome on each input (for example a better best-of-more result), a mix, or nothing? Is this stated in the published material, read from code, or inferred?
4. How are unit results combined into the reported quantity: averaged or pooled, best or maximum taken, reported per unit, or other?
5. From the saved per-unit timings: typical unit wall time, and the spread of unit costs (coefficient of variation).
6. Can the published program run a chosen subset of units without changing its code (a command-line option or configuration file), or would that need a configuration or code change?
7. Given fixed inputs and per-unit configuration, is one unit's output repeatable bit for bit, within a tolerance, or not repeatable?
8. Does a unit's random state depend on its position in the serial sequence (for example one random stream shared across units), so that running units separately or concurrently would change their outputs?
9. How does the baseline set its internal thread count (all cores by default, a fixed number, an environment variable), and roughly how many threads does one run use relative to the box's logical CPUs (`run9/A/results/probe/probe.json`)?
10. Does a run write anywhere other than its own `out/` or temporary files (shared caches, files inside input or source trees) that concurrent copies could collide on?
11. Did the earlier categories ("replicates_or_samples", "closer_to_published_scale", "independent_units") merge distinctions that your answers above separate?

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run9_units/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run9_units/REPORT.md` for the owner with the evidence (file paths, code and log lines, numbers), separating measured, read from code or documents, and inferred.
2. `run9_units/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"unit_kind"`: `"distinct_inputs"`, `"repeated_trials"`, `"candidates_same_input"`, `"parameter_points"`, `"chains_or_walkers"`, `"mixed"`, `"other"`, `"unknown"`
   - `"reduced_dimension"`: `"inputs"`, `"trials_per_input"`, `"candidates_per_input"`, `"parameter_points"`, `"unit_length"`, `"several"`, `"unknown"`
   - `"expansion_effect"`: `"coverage"`, `"precision"`, `"per_input_outcome"`, `"mixed"`, `"none"`, `"unknown"`
   - `"expansion_effect_basis"`: `"published_text"`, `"code"`, `"inferred"`, `"none"`
   - `"combination"`: `"average_or_pooled"`, `"best_or_max"`, `"per_unit"`, `"other"`, `"unknown"`
   - `"unit_wall"`: `"under_1min"`, `"1_to_10min"`, `"10_to_60min"`, `"over_60min"`, `"unknown"`
   - `"unit_cost_cv"`: `"under_10pct"`, `"10_to_50pct"`, `"over_50pct"`, `"unknown"`
   - `"subset_selectable"`: `"published_option"`, `"config_edit"`, `"code_change"`, `"unknown"`
   - `"unit_output_repeatable"`: `"bitwise"`, `"within_tolerance"`, `"not_repeatable"`, `"unknown"`
   - `"random_state"`: `"per_unit_independent"`, `"sequence_dependent"`, `"no_randomness"`, `"unknown"`
   - `"thread_setting"`: `"all_cores_default"`, `"fixed_number"`, `"environment_variable"`, `"unknown"`
   - `"threads_vs_cpus"`: `"under_half"`, `"half_or_more"`, `"unknown"`
   - `"writes_outside_out"`: `"no"`, `"yes"`, `"unknown"`
   - `"earlier_categories_merged"`: `"yes"`, `"no"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
