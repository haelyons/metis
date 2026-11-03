# s16 assessment: the revised "Sealed comparison (U57, U58)" draft against FINAL.json and SHAPES.json (2026-11-03)

**Scope.** I ran no test. I used no network, contacted no box, ran no git commands and read no credentials. I read:
- `science/s09/` (ASSESSMENT, REQS, PARTS), `science/s13/FINAL.json`, `science/s14/` (ASSESSMENT, CHECK) and `science/s15/` (ASSESSMENT, SHAPES, NARROWING);
- the physical card's plan `20261103-0124-tree/out/work/seed-20261103/R1/physical/1fffee1a/producer.md` (PC below), lines 18–113;
- `dut/pipeline/m5/SCHEMAS.md:330–339` (box record, receipts, `run_box_usd`);
- the U54 `card_extract.json` rule definition in `science/s12/PROMPT.md:56`.

"Draft" means the revised section in my step brief. It has no line numbers, so I cite it by sub-heading. Most Bash calls were denied, so I worked mainly with the file tools and wrote only into `science/s16/`.

## Verdict: partial (the operator's one revision; this goes to the owner)

The revision is a large improvement, and its structure should be kept. In particular, the trusted cross-arm comparator, one input per invocation, per-input references, the `unpaired` + `all_pairs` worst-case interval, the bootstrap ratio of means and the per-invocation compute rows each closes a gap from s14.

Every remaining gap can be fixed by adding to the draft, and none needs a redesign. So the verdict is `partial`, not `insufficient`. Even so, none of the seven comparisons can yet be decided exactly as FINAL.json and the card seal them, and the billed-cost fact is still not recorded. One gap carries most of the weight: **the draft has no trusted evaluator**. Per-pose DockQ is behind K3, K6 and K7, and it is part of K4's timing scope. The draft gives DockQ nowhere to run, because adapters may not compute a metric and the native structures must reach only the evaluator (PC:23, 36).

## What the revision now meets (s15's SHAPES.json)

| s15 item | Status | Where in the draft |
|---|---|---|
| inputs `one_input_per_invocation` | met | Rounds: each (arm, input) pair is its own invocation, with `CMP_INPUT` |
| budget `design_sets_budget` | met | `budget_s` in the design |
| budget `split_into_runs` | met | Purpose: "split by the science step into one design per run" |
| compute `per_invocation_rows` | met | `comparison_compute.json.invocations` |
| compute `exclude_overhead` | met | "Uploads, links and fetches are outside every row" |
| compute `cpu_identity` | met | `system.json`: `lscpu` model and CPU count |
| compute `software_versions` | **partly** | One version string per arm program. No executable hash, no linked FFTW/cuFFT/OpenMP versions; nvidia-smi gives only the driver's CUDA version (PC:22) |
| compute `other` (billed allocation) | **not met** | `usd` is still wall × price per invocation (attribution) |
| leaks `adapter_no_metrics` | met | Adapters "never compute, write or assert a metric" |
| leaks `view_text_screened` | met | The science step owns the view's free text |
| leaks `other` (sealed argv; `C/` unreadable) | **not met** | Arms are still chosen by agent-written adapters, and `C/` is hidden from prompts only |
| K1 shape (outputs, elementwise_abs, per_input_all, paired, all_pairs) | expressible, but see K1 | |
| K2 comparator `other` (symmetric base) | **not met** | `elementwise_abs_plus_rel` uses `abs(b)` |
| K3 shape | the comparator is expressible, but the values cannot be produced | |
| K4 shape (trusted_wall, pooled_mean, paired, bootstrap, ratio of means) | met as a statistic | See K4 for the timing scope |
| K5 shape (per_input_each, unpaired, all_pairs, previous-run reference) | expressible | Null handling and the timeout are wrong (see K5) |
| K6/K7 shape (sealed_extraction, per_input_each, unpaired, all_pairs, abs) | the statistic is expressible | The values cannot be produced (see K6/K7) |

Several s14 items can now be expressed **without a contract change**. A later design must use the following:
- **Gating of K4–K7 on K1–K3** (PC:65, 102). Write the agreement phase as its own design (K1–K3, A0 and A1, 1 replicate, matching "1 invocation per arm/case", PC:101). Launch the main design only if every agreement comparison is `supported`. The draft's split rule allows this.
- **Gain/loss sign for K6/K7** (PC:29). Write each as two one-sided superiority comparisons, `higher_better` (gain iff lo > m) and `lower_better` (loss iff hi < −m). With `unpaired` + `all_pairs`, lo = min(dense) − max(standard) and hi = max(dense) − min(standard), which is exactly the card's rule.
- **K5's three tiers.** Use three comparisons, each with a reference that maps the 4 cases to that tier's seconds. The main design then holds K4 + 3 + 4 = 8 comparisons, within the cap of 12.
- **K4's strict "> 1.05"** (PC:29). Set `threshold` to the next double above 1.05, so that `lo >= threshold` is equivalent to `lo > 1.05`.

## Missing items and problems, with the smallest fix for each

### metric_not_capturable: K3, K6, K7 (and K4's scope)
- **Why.** Per-pose DockQ must come from a pinned DockQ evaluator that alone has the native references (PC:23, 36). The draft has no such role:
  - adapters run only the arm's program and may not compute metrics;
  - `data.json` exposes every input to the arms;
  - `sealed_extraction` uses U54's kinds, which return one number per file (a JSON Pointer, or the *last* regex match, `s12/PROMPT.md:56`). So "best of 50" (a maximum) and "the pose ranked first" (the first match) cannot be extracted.
- **K4.** Its timing scope is the complete workflow, including DockQ (PC:68). Without an evaluator, A0's and A1's walls exclude DockQ, so K4 would be decided on a scope other than the sealed one.
- **Smallest fix.**
  1. Add an optional design field `evaluator: {what, references}`, with the references held in `C/` and in no view.
  2. Add a sealed adapter `harness/evaluate.sh` that runs the published, pinned evaluator. The trusted wrapper runs it after the arm's adapter in the same invocation, and only it receives `CMP_REFERENCE` and `CMP_EVAL_OUT`. Its wall time counts toward the arm's `wall_s` when a design flag `timing_includes_evaluator` is true.
  3. Allow `cmp_files` and `cmp_extract` to name evaluator files.
  4. Add a `reduce` field to extraction rules (`first`, `last`, `max`, `min`, applied to all regex matches or to a JSON array).

### statistic_unfit: K1, K2, K3, K5, K6, K7
- **(a) Vacuous agreement.** Agreement takes only replicates "where both arms ran with rc 0", and is supported "when every pair agrees and none is missing". If A1 fails on every replicate of an input, that input has zero pairs and is **supported**. Fix: an invocation with a nonzero `rc`, a timeout or no wrapper file makes its pair *missing*, and agreement with `n = 0` is void with reason `missing_values`.
- **(b) Nulls drop out of metric comparisons.**
  - K5: a timed-out or failed dense invocation becomes null and vanishes from `unpaired` differences. The remaining replicates can then give "supported", but the card records that run as unavailable at that tier (PC:29, 107) and the seed requires overruns to be preserved.
  - K6/K7: the same drop gives a gain or loss from the surviving replicates, while the card says "Missing/timeout arms mean unavailable comparison" (PC:29).
  - Fix: a per-comparison field `missing: "drop" | "void" | "fail"`. `fail` makes that unit `not_supported` (K5); `void` makes it void with reason `missing_values` (K6, K7, agreement). Record `n_missing` per row.

### margin_rule_unfit: K1, K2
- **K2.** The card seals |a − b| ≤ atol + rtol·max(|a|, |b|) (PC:58). The draft's base is `abs(b)` only, which is stricter and asymmetric, so a "not supported" can be wrong. Fix: add the comparator `"elementwise_abs_plus_rel_symmetric"` with base `max(abs(a), abs(b))`.
- **K1.** One output has one tolerance for every number in the file.
  - MEGADOCK's ranked output holds the rotation/translation entries and the scores on the same lines. Exact identity of the transforms (atol 0) cannot be checked without also requiring identical scores, and GPU scores are not reproducible (s13 §2: 39 distinct hashes over 40 files).
  - The 50 decoys are 50 files, but an output maps to one path.
  - Fix: an optional `select` per output, either a regex whose capture groups the *trusted comparator* keeps in order, or column indices. Also allow an output path to be an ordered list or a sorted glob of files, concatenated by the comparator. Adapters then never need to rewrite outputs.

### budget_unfit: K5
- **Why.** The only timeout is the time left in `budget_s`. The card's per-invocation cap at the largest frozen tier (PC:107) cannot be expressed, and one hung dense invocation consumes every later round.
- **Fix.** Add an optional design field `timeout_s` (one number, or a map per arm and input). The timeout becomes min(`timeout_s`, time left). A timeout is recorded as `"timeout"` and handled by the `missing` rule above.

### compute_unfit: compute_facts
- **(a) Billed allocation (s15 `other`).** FINAL.json's `usd` is the billed allocation, including setup, idle and failed work (PC:68, 111–112). The draft records only attribution (`wall_s × price`). `run_box_usd` (`SCHEMAS.md:337`) is a run-level number that treats an active box's end as the accounting time, and nothing marks it as an estimate. Fix:
  - add `allocation: {started_utc, ended_utc, hours, usd, final}` from `C/box.json`, refreshed at takeaways when the matching record has `ended_utc` (`SCHEMAS.md:332–333`); `final` is false otherwise;
  - rename the per-row and per-arm `usd` to `attributed_usd`.
- **(b) Versions and hardware identity.** The card pins executable hashes, linked FFTW/cuFFT/CUDA/OpenMP versions and GPU identity (PC:22). Fix:
  - the pipeline records the SHA-256 of each arm's executable, named in `versions.sh` output as `{arm: {version, executable}}`;
  - `system.json` adds `ldd` of each executable and `nvidia-smi --query-gpu=name,uuid`. At present only `box.type` implies the GPU model.

### leaks_or_biases (s15 `other`, unchanged from s14 problem 9)
- **Why.** The harness agent still writes every adapter, and nothing checks that the arms share identical flags and differ only in the declared axis (PC:23, 40–48). Criteria are hidden by prompt wording only ("prompts name it and never `C/`"). Nothing states that agents cannot read `C/` or the design path.
- **Fix.**
  - Add an optional sealed `arms[].argv`, the exact published command line, passed as `CMP_ARGV`. The pipeline checks that the adapter executes it, for example by having the wrapper log the executed argv.
  - Require the design source and `C/` to lie outside every agent's readable roots.

## Not problems
- **Arms.** All three are published MEGADOCK binaries and flags, including A0's thread and affinity settings, so `arm_not_runnable` does not apply.
- **Order.** Each round contains every (arm, case) pair once, shuffled from `order_seed`; a round is the card's balanced block (PC:30, 106).
- **Sealing.** The comparison seal, the arms seal and the scorer's re-check are sound.
- **Reference.** Per-input values from a named previous run are sound for K5.
- **K5's split outcomes.** Mixed replicates come out `inconclusive` rather than `not_supported`. Only "supported" means "within tier", so the reading is unchanged.

## For the owner
- This was the operator's single revision, and the verdict is still `partial`. The decision on the six fixes above is yours.
- The two largest are the trusted evaluator (K3, K4's scope, K6, K7) and the missing-value rule (K1–K3, K5–K7). Both are additions.
- Still open from s13 §5, and not affected by this check:
  - the source of the tolerances atol, rtol, eps_xyz and eps_eval;
  - approval of the main run above USD 20 (PC:75 projects USD 49.48).
- s15 sealed no predictions, so `outcomes.json` is empty. This step runs no test.
- Next action: stop, `contract_gap`.
