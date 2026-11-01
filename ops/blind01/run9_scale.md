You are an authorized reader for the blind-01 experiment. The owner authorized readers to see its brief and records. The operator who launched you is blind to this experiment's content and sees only `status.json`, as validated enum values; your final reply is not shown to the operator.

Working directory: experiments/blind-01/m5/ of the metis repository (the current directory). Write only into `run9_scale/`. Change nothing else, run no workloads, contact no box, fetch nothing from the network, and run no git commands. Some directories under `run9/` are large: measure with `du` or `ls`, and read only the files you need (logs by head, tail or grep).

## Purpose
Run9 passed reproduce: the one gated anchor was within tolerance (`run9/A/results/reproduce/anchors_scored.json`), and an earlier reader found the run used a reduced scale relative to the published protocol. The materials came from a mirror whose match to the original is unverified; the owner's rule is that passing published-value anchors checks the properties those anchors measure and does not prove the copy matches the original. The operator wants a neutral account of what this pass establishes, whether "reduced-scale baseline calibration" describes it fairly, and whether running at the published scale would strengthen it. `unknown` is a correct answer whenever the evidence does not settle a question; do not lean toward any answer.

## Read
- the brief as run (`intake_mirror/BRIEF_run5.md`), run9's intake records (`run9/A/intake/`: anchors, references, scale and execution records), the harness scripts (`run9/A/harness/`), `run9/A/results/reproduce/anchors_scored.json`, the reproduce logs and measured outputs (`run9/A/results/reproduce/`), and the `intake_mirror/` reader's report and status
- `dut/pipeline/m5/SCHEMAS.md` (intake, reproduce and anchor scoring sections) and `dut/pipeline/m5/score_anchors.py`, read-only (repository root two levels up)

## Questions
1. Items: of the intake's items, how many are gated anchors and how many ungated references? Did the references fall within the tolerance they would have had as anchors?
2. What does the gated anchor measure: the study's main scientific quantity, a secondary output, or an incidental property (a count, a size, a runtime)?
3. Scale: which dimension did the representative scale reduce (replicates or samples, length or steps, problem size, several), by roughly what factor, and were the published values obtained at the published scale?
4. Does the anchor's expected value depend on scale, or only its sampling noise?
5. Tolerance: how does the anchor's tolerance compare with the sampling noise expected at run9's scale (much wider, comparable, narrower, or no noise because the output is deterministic)? Where did the tolerance come from (published uncertainty, intake judgement, other)?
6. Margin: how far inside the tolerance was the measured value, as a fraction of the tolerance?
7. Sensitivity: would a plausible defect in the copied materials (wrong input data, wrong parameter, different software version) be likely to move the anchor outside tolerance at run9's scale? Would it at the published scale?
8. Full scale: what would a run at the published scale add — a tighter comparison of the same quantities, additional published quantities, nothing beyond noise — and would it resolve whether the mirror copy matches the original?
9. Runtime: from run9's measured times, estimate the published-scale serial runtime on the same box.

## Rules
- Never read `.keys` files, credential files or anything under `~/.codex/`.
- Do not commit or push; the launcher commits `run9_scale/`.
- No fabrication. If something cannot be established, use the `unknown` value.

## Outputs
1. `run9_scale/REPORT.md` for the owner with the evidence (file paths, values, arithmetic), separating measured, inferred and unknown.
2. `run9_scale/status.json`, one JSON object with exactly these keys, each taking only the listed values:
   - `"gated_anchors"`: `"one"`, `"two_plus"`
   - `"references_within_tolerance"`: `"all"`, `"some"`, `"none"`, `"no_references"`, `"unknown"`
   - `"anchor_quantity"`: `"main"`, `"secondary"`, `"incidental"`, `"unknown"`
   - `"scale_dimension"`: `"replicates_or_samples"`, `"length_or_steps"`, `"problem_size"`, `"several"`, `"not_reduced"`, `"unknown"`
   - `"scale_factor"`: `"under_2x"`, `"2_to_10x"`, `"10_to_100x"`, `"over_100x"`, `"unknown"`
   - `"published_values_at_published_scale"`: `"yes"`, `"no"`, `"unknown"`
   - `"anchor_expectation"`: `"scale_invariant"`, `"scale_dependent"`, `"unknown"`
   - `"tolerance_vs_noise"`: `"much_wider"`, `"comparable"`, `"narrower"`, `"deterministic"`, `"unknown"`
   - `"tolerance_source"`: `"published_uncertainty"`, `"intake_judgement"`, `"other"`, `"unknown"`
   - `"margin"`: `"under_25pct_used"`, `"25_to_75pct_used"`, `"over_75pct_used"`, `"unknown"`
   - `"defect_detectable_run_scale"`: `"likely"`, `"unlikely"`, `"unknown"`
   - `"defect_detectable_published_scale"`: `"likely"`, `"unlikely"`, `"unknown"`
   - `"full_scale_adds"`: `"tighter_same_quantities"`, `"more_quantities"`, `"both"`, `"nothing_beyond_noise"`, `"unknown"`
   - `"full_scale_resolves_provenance"`: `"yes"`, `"partly"`, `"no"`, `"unknown"`
   - `"published_scale_runtime"`: `"under_12h"`, `"12_to_48h"`, `"2_to_7d"`, `"over_7d"`, `"unknown"`

   No other keys and no free text.

Finish within 15 minutes. End with a final reply that is exactly the contents of status.json.
