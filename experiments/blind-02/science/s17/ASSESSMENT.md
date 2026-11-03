# s17 assessment: seed-neutral draft of "Sealed comparison (U57, U58)" (2026-11-03)

**Scope.** I ran no test. I used no network, contacted no box, ran no git commands and read no credentials. I read:
- `science/s13/FINAL.json`, `science/s14/` (ASSESSMENT.md, CHECK.json), `science/s15/` (SHAPES.json, ASSESSMENT.md) and `science/s16/` (ASSESSMENT.md, CHECK.json);
- the operator's revised draft, verbatim in `science/s16/PROMPT.md:42–88`;
- the U54 `card_extract.json` rules in `science/s12/PROMPT.md:50–67`;
- `dut/pipeline/m5/SCHEMAS.md`: lines 47–48 (`harness_from`), 230 (wf `isolation`, used for the new isolation rule) and 330–339 (box record, receipts, `run_box_usd`).

Most Bash calls were denied, so I wrote every file with the file tools, and only into `science/s17/`.

`DRAFT.md` is one section, starting with `## Sealed comparison (U57, U58)`. It keeps the operator's structure and order. These rules are unchanged: sealing, the view, mode exclusivity, the intake and reproduce rules, the round shuffle, PASS whatever the outcomes, and the evaluate facts. It names no program, case, file or number from the seed, its materials or the earlier steps' findings. That includes the bootstrap resample count: the operator's draft had a fixed count that matched the card's, and it is now the design field `bootstrap_resamples`. The only tools it names are system tools the operator's draft and SCHEMAS.md already use (`lscpu`, `nvidia-smi`, `uname`), plus `ldd`.

## Changes, per s16 finding (CHECK.json: missing K1–K7 and compute_facts; six problems)

| s16 finding | Change in DRAFT.md | Resolves |
|---|---|---|
| **metric_not_capturable** (K3, K6, K7, and K4's timing scope): no trusted evaluator | Adds the design field `evaluator` `{what, spec, timeout_s}` and a sealed `harness/evaluate.sh`. The wrapper runs it after the arm part, with `CMP_ARM_OUT`, `CMP_EVAL_OUT` and `CMP_PRIVATE` and **without the arm id**. Evaluator-only data live under `cmp-private/`, which has no link in `run/`, is set to mode `000` while the arm runs (a change makes the invocation `invalid`), and may not be named by any adapter (a static byte check before upload). `cmp_files`/`cmp_extract` locations may start with `eval/`. The metric field `reduce` (`first`, `last`, `min`, `max`, `mean`, `value_at_max_key`, `value_at_min_key`) and `expect_count` are fixed in the design, not by the harness agent. A `trusted_wall` metric gets a `scope`, so `invocation_and_evaluator` gives the whole-workflow timing scope. | K3, K6, K7; K4 scope |
| **statistic_unfit (a)**: vacuous agreement | A side whose invocation is not `ok`, whose evaluator failed, or whose file is missing, unparsable or empty after selection is *missing*. Agreement with no compared pair is void. A disagreement decides "not supported" before the missing-value rule. | K1, K2, K3 |
| **statistic_unfit (b)**: nulls drop out | Per comparison, `missing` `drop` / `void` / `fail`. Under `fail`, the arm's missing value makes the unit not supported (reason `missing_values`). Rows add `n_missing`. | K5 (`fail`), K6/K7 (`void`), agreement (`void` or `fail`) |
| **margin_rule_unfit** K2 | New comparator `elementwise_abs_plus_rel_max`: `abs_tol + rel_tol * max(abs(a), abs(b))`. | K2 |
| **margin_rule_unfit** K1 | Output `select`: a regex fixed in the design whose capture groups the trusted comparator keeps. Several outputs may select different fields of one file, each with its own tolerance (for example exact identity for some fields and an absolute tolerance for others). A `cmp_files` location may be `{glob, order}` (`lexical` or `natural` order) for multi-file outputs. | K1 |
| **budget_unfit** K5 | Design field `timeout_s` (global, per arm, or per arm and input), plus `evaluator.timeout_s`. A timeout kills the process group and is recorded as `timeout`. `not_run` is recorded when the budget is exhausted. Timeouts are held in `C/` only, not in the view, because a cap derived from the reference values would leak them. | K5 |
| **compute_unfit (a)**: billed allocation | `allocation` `{type, price_usd_h, started_utc, ended_utc, hours, usd, final}`, rewritten at takeaways after `C/box.json` is refreshed (`SCHEMAS.md:333`). `final` is false while the box is active. Per-row and per-arm `usd` is renamed `attributed_usd`. `all_invocations` adds totals that include warmups and failures. | compute_facts |
| **compute_unfit (b)**: versions and hardware identity | The trusted `cmp_system.py` records each executable's SHA-256 and every `ldd`-resolved library with path and SHA-256, plus GPU `name`, `uuid` and memory, driver and CUDA versions. Each command row also records the resolved executable and its SHA-256 per invocation. | compute_facts |
| **leaks_or_biases**: arms chosen by agent adapters | Optional sealed `arms[].commands` (argument vectors, no shell) and `env`, with placeholders for input, paths and `spec` fields. When they are set, the **trusted wrapper** runs the commands and the adapter only prepares. Arms then differ exactly as the science step wrote them. | leaks `other` |
| **leaks_or_biases**: `C/` hidden by prompt only | New "Isolation" rule: in comparison mode, every agent call runs under wf `isolation` (`SCHEMAS.md:230`) with `C/` and the design path in `hidden`, `box_access` false, and no fallback. | leaks `other` |

**Also added (not s16 findings; from s15's notes, resolved because they remove judgement at decision time):**
- `given`: per-unit eligibility on earlier comparisons. This expresses "the quality comparison at a time limit counts only where the dense arm met that limit" (s15 §1, K6/K7) and in-design gating.
- `strict` for `ratio_at_least`, replacing s16's "next double above the threshold" workaround.
- `sign` on two-sided superiority rows, giving gain or loss, so K6/K7 need one comparison per limit rather than two.

Gating across runs stays with the science step, as the Purpose bullet now states (s16 judged this expressible).

## s15's three `other` codes

1. **K2 comparator** (symmetric base): resolved by `elementwise_abs_plus_rel_max`.
2. **compute `other`** (billed allocation): resolved by `allocation` and the `attributed_usd` rename.
3. **leaks `other`** (arms differ only in the declared axis; `C/` unreadable): resolved by sealed `commands`/`env` run by the wrapper, and by mandatory isolation.

## How FINAL.json's comparisons fit (for the next science step; not in DRAFT.md)

- **Agreement run** (one design): K1 as two or more `select` outputs over the ranked output, `exact` or `elementwise_abs`. K2 with `elementwise_abs_plus_rel_max`. K3 on the evaluator's per-item scores, `elementwise_abs`. All use `per_input_all`, `missing: fail`.
- **Main run** (a second design), 10 comparisons, within the cap of 12:
  - K4: `trusted_wall` scope `invocation_and_evaluator`, `pooled_mean`, `bootstrap`, `strict: true`.
  - K5 as three comparisons, one per time limit: `reference` values per input, `unpaired`, `all_pairs`, `missing: fail`, with `timeout_s` at the largest limit.
  - K6 and K7 as three comparisons each: `sealed_extraction` with `reduce` `value_at_max_key` (score-ranked first) and `max` (best of all), `unpaired`, `all_pairs`, two-sided superiority with an `abs` margin, `missing: void`, each with `given` set to its limit's K5 comparison.
  - The main run is launched only if the agreement run's comparisons are all `supported`.
- I have not written a design. Margins and reference values belong in it, and the owner sets them.

## Limits the owner should know

- **Private data.** It is protected by link omission, a mode change checked by the wrapper, and a static name check. That is not a kernel sandbox: a deliberately obfuscated adapter running as the same user could still get round it. Because the adapter bytes are sealed and hashed, such a bypass would be auditable afterwards, not prevented.
- **Isolation cost.** Mandatory isolation for intake and harness calls assumes that the isolated namespace keeps the network those roles need. SCHEMAS.md:230 does not state this either way. If it does not hold, those calls fail and do not fall back.
- **Arms without `commands`.** These are still run by an agent-written adapter. Arm identity is only enforced when the design sets `commands`.
- **Not yet checked.** Nothing here has been built or tested. An independent content check, like s14 and s16, has not been run on this draft.

## What the owner must still decide

1. The source of the tolerances and margins for the agreement and quality comparisons (still open from s13 §5).
2. Approval of the main run above USD 20 (s15 projects USD 49.48).
3. Whether to accept the residual protections above (private-data protection without a sandbox; isolation possibly blocking network), or to require a stronger mechanism before building.

So the owner has more to decide than margins alone (`owner_decisions: more`).

## Predictions and next action
- s16 sealed no predictions, so `outcomes.json` is empty.
- This step runs no test, so it seals none.
- Next action: stop, `contract_gap`. The draft awaits its seed-content audit and the operator's commit to `dut/pipeline/m5/SCHEMAS.md`.
