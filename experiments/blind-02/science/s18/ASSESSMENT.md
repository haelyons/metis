# s18: independent audit of `science/s17/DRAFT.md` (seed content, then sufficiency), 2026-11-03

**Scope.** I ran no test. I used no network, contacted no box, ran no git commands, read no credentials and did not edit DRAFT.md. I read:
- the seed `m5/BRIEF.md:1-23`;
- `science/s13/FINAL.json`, `science/s15/SHAPES.json` and `science/s15/ASSESSMENT.md`;
- s14's CHECK.json, and s16's CHECK.json, ASSESSMENT.md and PROMPT.md (the definitions and the operator's revised draft);
- `science/s17/ASSESSMENT.md` and `DRAFT.md` (lines 1-74);
- the physical card's plan `20261103-0124-tree/out/work/seed-20261103/R1/physical/1fffee1a/producer.md` ("PC"), lines 18-113;
- `dut/pipeline/m5/SCHEMAS.md`: line 38 (nvidia record), lines 228-233 (implement views, wf `isolation`), line 334 (receipt GPU sampling) and line 335 (`gpu_busy_known`).

## 1. Seed audit: `none`

I read every line of DRAFT.md against the seed, the card and the findings of s13-s17. I also searched it for the seed's program, data, evaluator and library names, the case identifiers, and the seed's and card's numbers. Every hit was a substring of a generic word:
- "pose" occurs inside "Purpose" (line 2) and "propose" (line 41);
- "26" occurs inside the date "2026" (line 2);
- "3600" is seconds per hour (line 55);
- "score" occurs inside `score_comparison.py` and `comparison_scored.json` (lines 61-74).

I considered and rejected these items one by one:

| Item (DRAFT.md line) | Why it is not seed content |
|---|---|
| `nvidia-smi`, GPU busy sampled every second, driver and CUDA versions (43, 50) | The existing m5 contract already has all of these (`SCHEMAS.md:38, 334-335`, `boxrun.sh:76`), and so did the operator's own blind draft (`s16/PROMPT.md:73, 75`). m5 is a general GPU pipeline. |
| `lscpu`, `uname`, `ldd` (43) | Generic system tools. |
| Gap labels "G1 comparison arms, G3 tolerance and equivalence, G6 compute metadata", owner approval date, "science steps s13 to s17" (2) | Route and contract identifiers. The blind operator already wrote them (`s16/PROMPT.md:43`). They name contract mechanisms, not what the seed asks or what was found. |
| Private-data evaluator (13, 33, 35, 46-49) | The generic held-out evaluation pattern. It does not reveal the domain, the data or the metric. |
| Reducers `value_at_max_key` / `value_at_min_key`, `max`, `first` (12) | Generic arg-max and order reducers. |
| `elementwise_abs_plus_rel_max` (18, 63) | The generic symmetric closeness test. |
| `given`, `strict`, `sign`, `missing`, cross-run gating (2, 25, 27-28, 66, 70) | Generic statistical and decision mechanics. |
| Bounds 2-5 arms, 1-10 inputs, 1-8 commands, 0-10 outputs, 1-30 replicates, 0-3 warmups, 1000-1000000 resamples, 1-12 comparisons | None matches a seed or card number. The card's bootstrap resample count is now a design field (`bootstrap_resamples`), as s17 states (`s17/ASSESSMENT.md:11`). |

No line names a program, library, dataset, case, file or output of the seed. No line quotes the seed, and no line carries a seed or finding number, margin or reference value. Taken together, the text tells a reader only that some run compares published configurations with tolerances, a private evaluator and compute accounting. That does not reveal what the seed asks or what the route found. **Seed content: none.**

## 2. Sufficiency: `partial` (one problem, no missing item)

### What the draft now meets

DRAFT.md closes every s16 finding (`s16/CHECK.json`) and all three of s15's `other` codes. For each comparison, here is the shape it needs (from SHAPES.json) and how the draft expresses it:

- **K1** (needs `cross_arm_outputs`, `elementwise_abs`, `per_input_all`, `paired_replicate`, `all_pairs`):
  - Per-field `select` outputs (line 9). Transform and rank fields use `exact` or abs 0; coordinates use an abs tolerance.
  - A `{glob, order: natural}` location reads many per-item files (36, 62).
  - A length mismatch disagrees (63), so a tie or cutoff mismatch fails, as PC:58 requires.
- **K2** (needs a symmetric abs+rel base): `elementwise_abs_plus_rel_max` (63).
- **K3** (needs per-item quality from a private evaluator, compared elementwise): `evaluator` + `evaluate.sh` + `eval/` locations (13, 35, 36).
- **K1-K3, common rules:**
  - A side that failed or is empty is missing (62).
  - A disagreement decides first (69).
  - `missing: fail` or `void` blocks a vacuous "supported" (65, 69).
- **K4** (needs `trusted_wall`, `pooled_mean`, `paired_replicate`, `bootstrap`, ratio of means, strict bound):
  - `scope: invocation_and_evaluator` gives the complete-workflow scope (PC:68), at line 11.
  - `ratio_at_least` with `lower_better` gives mean(A0)/mean(A1) (64).
  - The bootstrap resamples replicate rounds jointly across inputs (64, 67), and `strict: true` gives "> threshold" (25, 69).
- **K5** (needs `per_input_each`, `unpaired`, `all_pairs`, a previous-run reference, and failure on overrun):
  - Non-inferiority, `lower_better`, null margin: supported iff every replicate is within the tier (69).
  - `missing: fail` makes a timeout not supported (65), and `timeout_s` can be set per arm and input (15, 52).
  - One comparison per tier, with references whose `source` names the run and the rule (26).
- **K6/K7** (need `sealed_extraction`, `per_input_each`, `unpaired`, `all_pairs`, abs margin, gain/loss sign, tier eligibility):
  - Two-sided superiority with `sign` (69-70). With `unpaired` + `all_pairs`, lo = min(dense) − max(standard) and hi = max(dense) − min(standard), which is exactly PC:29's rule.
  - `reduce: max` with `expect_count` for best-of-all, and `first` (in rank order) or `value_at_max_key` for rank 1 (12, 37, 53).
  - `given` = that tier's K5 row (28, 66), and `missing: void` (PC:29: "unavailable comparison").
- **Gating K4-K7 on K1-K3**: separate designs, with launch conditioned on the earlier `comparison_scored.json` (2).
- **compute_facts:**
  - per-arm wall and GPU-busy seconds, with the evaluator kept separate (56);
  - hardware identity: CPU model, GPU name, UUID and memory, driver, CUDA, kernel (43);
  - executable and library SHA-256 (43, 50);
  - the bill, kept separate from attribution (59), with `final: false` marking an estimate (PC:112).
- **Leaks:**
  - Sealed `commands`/`env` run by the trusted wrapper (5-6, 47).
  - Isolation, with `C/` and the design path hidden (31).
  - The view excludes criteria, margins, references and timeouts (30).

So, as written, the draft can run every arm (A0-A2 use published commands only), and it can express and decide K1-K7 as SHAPES.json shapes them. That is why `missing` is empty.

### The problem: `leaks_or_biases`, the evaluator can learn the arm

Line 2 promises an evaluator "that the pipeline runs on each arm's output without naming the arm", and line 51 says its environment "never" carries the arm id. But:
- the invocation directory is `comparison-work/<round>/<arm>/<input>/` (line 45);
- the evaluator runs with its working directory `run/` inside that directory (49), and `CMP_ARM_OUT` is that directory's `out/` (51).

So the arm id is in the evaluator's working directory and in `CMP_ARM_OUT`. The view also maps each arm id to its description (30), so an agent-written `evaluate.sh` could branch on the arm. That is exactly the bias the arm-blind evaluator is meant to exclude, and it bears on K3, K6 and K7. The sealed bytes would make such branching auditable afterwards, but nothing prevents it.

**Smallest fix.** Name invocation directories by an opaque per-invocation token, for example a SHA-256 of the round, arm, input and a sealed salt, or a sequential index. Record the token-to-(round, arm, input) map only in `C/` and in the fetched result path under `A/results/...`. Also state that no path or variable the evaluator receives contains the arm id.

### Notes for the builder (not problem codes; each can be built as written)

1. **Isolation views (line 31).**
   - `SCHEMAS.md:230` makes the view the only writable host directory, and `:233` defines per-role views and copy-back for implement only.
   - The draft names `hidden` and `box_access` but no `directory`, view content or copy-back for intake, harness and repairs, and these roles write into `A/` and `harness/`.
   - One way to build it is to use the run directory as the view with `C/` hidden. The draft should say which.
   - The bubblewrap setup unshares PID/IPC only, so the network stays available. That answers s17's open concern about network access (`s17/ASSESSMENT.md:54`).
2. **Per-item reconstruction.** A step that runs once per retained item can exceed the cap of 8 arm commands (line 5). It can be put in the evaluator (its `spec` may name several pinned programs), and it still falls inside the `invocation_and_evaluator` wall.
3. **Rank-1 extraction.** `value_at_max_key` needs the key and value in one file under one rule (37). Otherwise use `first` over an evaluator output written in the arm's rank order; the design must state which.
4. **Timeout scope.** The arm part and the evaluator part are capped separately (52), so a whole invocation can exceed the largest tier without being killed. K5 still decides correctly, because the complete-workflow wall is compared with the tier.
5. **Calibration run.** At least one comparison is required (16). A calibration run whose walls feed the tier references therefore needs one comparison, any one.
6. **Residuals s17 already disclosed** (`s17/ASSESSMENT.md:53-55`). The mode-`000` protection runs as the same user, and arms without `commands` are agent-run. Neither affects A0-A2, which all use published commands.

## For the owner

- The draft carries no seed content, so the operator may commit it as far as seed content is concerned.
- On sufficiency, the verdict is `partial`, with one small fix: arm-opaque invocation paths for the evaluator. Notes 1 and 3 are worth stating in the same edit.
- Still open from s13 §5 and s17: the source of the tolerances and margins, and approval of the main run above USD 20.
- s17 sealed no predictions, so `outcomes.json` is empty. This step runs no test.
- Next action: stop, `contract_gap`.
