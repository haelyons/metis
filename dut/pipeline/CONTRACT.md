# qt2 build contract

Binding for every module agent. Read fully before writing code. Design rationale lives in
`/tmp/claude-1000/-home-hal-stage/01679595-7e0a-4a87-9dfe-92f32b9672f2/scratchpad/meta/synthesis/` (INTEGRATED.md, then substrate.md, cost.md, criteria.md, flow.md, options-and-card.md); this file fixes the interfaces. Where this file and a report disagree, this file wins.

## 0. Decisions from the human (2026-10-16), already applied below

- `require_compute_lever = {physical: true, interp: true}`; gate before producers via `compute_open` status and `sequential` status: ineligible only when both are closed (`compute_open` settled or none, and `sequential` none); a branch with <2 eligible options picks what it has and logs.
- `pool_k = 3`. `seed_ideas` (free-text ideas from the human) enter as pool candidates with their own producer, labelled `seed`.
- Budget-only constraint: $1,000 at Lambda on-demand list prices. No `max_gpus`, no "one machine", concurrent instances allowed, no FLOP accounting. PRODUCER verbatim prompt loses the words "one machine, up to 8 GPUs,".
- Minimal estimates: default cost encoding is time boxes (DESIGN hours × price-sheet rate); `need`, scenarios, yields optional. A GUESS only where a number drives the plan; every load-bearing GUESS/PROXY names the phase that measures it.
- Restructuring: `PLAN.restructuring` is required (`method` may be none). Scored by card `reshape` and `baseline`. On restructured plans, `lever` (c) reads "same hardware, method only". (Replaces the optional `PLAN.speedup`, which counted toward `lever` only when it extended the range.)
- WIDENER definition suffix: adopted, with a second definition sentence (a problem whose steps run one after another counts, even where more hardware changes only how soon the answer arrives). Writer: render-by-default from producer card fields; WRITER kept as a side cell for the replay comparison. Cost inputs non-blocking in the dramaturg. Payoff shown as dollars at `decides_by`. Credit covers storage, not tax. Reading budget ~25 min; cards for every pick including rejects and halts.
- johns-world is the shared 4-core host for producers' local pilots: hang guard in the PRODUCER suffix; every local command under `timeout`.

## 1. Layout and conventions

```
/home/hal/stage/qt2/
  CONTRACT.md            this file
  src/text.js            shared text helpers            (owner: gates agent)
  src/schemas.js         JSON schemas                   (owner: gates agent)
  src/cost.js            numbers, cost evaluation, block (owner: cost agent)
  src/pick.js            seeded draws, pick rule         (owner: pick agent)
  src/gates.js           gates, decision rule, selftest  (owner: gates agent)
  src/render.js          card, table, inventory, result  (owner: render agent)
  src/prompts.js         all prompt text, criteria, roles(owner: prompts agent)
  src/main.js            workflow script body            (owner: main agent)
  src/replay.js          replay workflow script body     (owner: replay agent)
  tests/run.js           test runner (given)
  tests/<module>.test.js one per module (owner: that module's agent)
  tests/fixtures/        copied inputs (each agent copies what it needs, under its own subdir)
  tools/                 python helpers for the replay (owner: replay agent)
  build.js               (given) concatenates src into dist/
  dist/question_tree_v2.js, dist/replay_v2.js   (built; never hand-edited)
/home/hal/stage/.claude/agents/qt-*.md          role files (owner: prompts agent)
```

Module rules (the Workflow runtime executes one self-contained plain-JS file; no Node APIs):
- Plain script. No `import`, `export`, `require`, `module.exports`. Top-level `function` and `const` only. The build concatenates files in this order: text, schemas, cost, pick, gates, render, prompts, then the main body. `main.js` and `replay.js` must begin with `export const meta = {...}` (a pure literal) followed by the line `// @@MODULES@@`; build.js inserts the modules there.
- Names are prefixed by module: `txt_`, `SCHEMA_`, `cost_`, `pick_`, `gate_`, `render_`, `P_` (prompt functions), `CRIT_` (criteria strings), `ROLE_` (role file contents), `ORIG_` (the user's original prompts). No other top-level names.
- Forbidden: `Date.now()`, `new Date()` without args, `Math.random()`, filesystem, `console.log` in modules (return logs as arrays). Determinism given `seed`.
- A module may call only modules earlier in the build order. `render` may call `cost_render_short`, `cost_render_block`, `cost_render_derivations`, `cost_menu`, `txt_*`. `gates` may call `txt_*`, `cost_*`. `pick` calls `txt_*` only. `main`/`replay` call anything.
- Each of cost, pick, gates, render exposes `<prefix>selftest()` returning `{ok: boolean, failures: [string]}` with its planted cases embedded as JS literals. `main` S0 calls all four and returns `{error}` if any fails.
- Tests: `node tests/run.js` concatenates `src/*.js` in build order plus every `tests/*.test.js` and runs them in a `vm` context exposing `assert` (node:assert/strict), `test(name, fn)`, and `fixture(relpath)` (returns parsed JSON or text from `tests/fixtures/`). Tests must be pure; no network.
- Keep prompt strings free of em-dashes. Write code that reads like the existing script (`/home/hal/.claude/projects/-home-hal-stage/01679595-7e0a-4a87-9dfe-92f32b9672f2/workflows/scripts/question-tree-wf_670c1d45-049.js`): compact, commented where a rule has a reason, no speculative options.

## 2. Records

All records are returned by agents through the harness `schema` option (JSON Schema, root `type: object`, `required ⊆ properties`). Arrays of items are wrapped as `{items: [...]}`.

### 2.1 Roots and framer
```
QUESTIONS   {items: [{question}]}
OVERLAP     {pairs: [{a: rootId, b: rootId, shared_subject}]}          // shared_subject ≥ 3 words
VERDICT     {verdict: "COMPUTE-BOUND"|"NOT COMPUTE-BOUND",
             compute_signals: [{subproblem, what_compute_buys}]}       // 0..3
```

### 2.2 Options (branch agents)
```
OPTIONS {items: [{ id,            // the heading label used in the branch file
                   title, summary,
                   root_link,     // one sentence, or "none"
                   compute_open,  // one sentence: the quantity more parallel compute would increase here
                                  // (samples, ensemble members, resolution, model runs, model size, search width;
                                  // interp: models, layers, features, prompts, seeds analysed), where published
                                  // measurements of its effect stop with a source URL, and what is unknown above
                                  // that; OR "settled: <what is known> <URL>"; OR "none"
                   sequential,    // one or two sentences: the chain one answer waits on (what each step waits for, roughly how
                                  // many steps), how many independent runs the answer needs, how much of one GPU one run keeps
                                  // busy; whether the steps must run in order, and if not, what change would let them run at
                                  // the same time, what must be true of the system for that to pay off, and the nearest source
                                  // that tried it, with its URL; OR "none: <why the work already splits into independent pieces>"
                   source_urls: [str] }]}                              // ≤ 3
```
Script derives `compute_open_status`: "settled" if `compute_open` starts with "settled" (case-insensitive), "none" if it equals "none"/"none known" after trim, else "open". Script derives `sequential_status`: "none" if `sequential` starts with "none" (case-insensitive, after trim), else "named". `sequential` is prose: required non-empty (G-opt), never checked for truth. Option key = `${root}:${branch}:${id}`.

### 2.3 Option critic
```
OPTION_SCORES {items: [{ id,
                         distance: "SAME"|"ADJACENT"|"ELSEWHERE", distance_reason,
                         scores: [{criterion, value: integer 1..5, reason}] }]}   // no NA
```
Criteria sets (names are the keys used everywhere): physical `["stakes","open","reshape"]`; interp `["stakes","open","internals","reshape"]`. Totals = sum of the values of every criterion but `reshape` (stakes + open, plus internals for interp), computed by `gate_totals`; `reshape` routes the top pick and the pool and never enters a total, so the open route and the legacy reproduction keep their totals. Script floors (each logged): `compute_open_status` settled/none → the `open` value is overwritten to 1 before totals; `sequential_status` none → the `reshape` value is overwritten to 1 before routing.

### 2.4 Deduplication and price sheet
```
DEDUP       {clusters: [{topic, members: [key]}]}                       // partition of all keys; topic ≥ 3 words
PRICE_SHEET {read_at,                                                   // ISO date string from the page fetch, agent-supplied
             instances: [{gpu, gpu_memory_gb, n_gpus, per_gpu_usd_h, page_text}],
             filesystem: {usd_gib_month, page_text, example: boolean}}
```

### 2.5 PLAN (producer; also the EXTRACT output)
```
PLAN {
  option_title,                                  // echoed; gate_plan compares normalised to the pick
  question, hypothesis,                          // one sentence each, plain words (card fields)
  compute_axis: {quantity, unit, levels: [number]},   // ≥2 levels, max/min ≥ 2
  held_fixed: [str],
  predictions: {if_lever, if_not,                // card fields; one must contain a digit
                decision_rule,                   // contains a digit
                noise_rule,                      // how a real difference is told from run-to-run noise
                expected: "if_lever"|"if_not"|"unsure", expected_why},
  compute_tested: "yes"|"partly"|"no", compute_tested_why,
  scored_against,                                // what the measured outcome is compared with
  arms: [{id, what}],
  baseline: {what, value?, source_id?},
  anchor: {what, published_value?, tolerance, source_id?, independent_code?} | {absent_reason},
  checks: [str],
  phases: [{id, what, stop_rule?, gate?: {on: number_id, op: ">="|"<=", value: number, else: str}}],  // execution order
  numbers: [{ id,                                // ^[a-z][a-z0-9_]{0,30}$ ; reserved: budget_usd, fs_usd_gib_month
              name, unit,
              basis: "CITED"|"PROXY"|"MEASURED"|"DERIVED"|"DESIGN"|"GUESS",
              value?,                            // required unless DERIVED
              expr?,                             // DERIVED only
              source_id?, quote?, page_setting?, // CITED, PROXY
              differs_in?: [str],                // PROXY required; MEASURED optional
              command?, output?, output_line?, machine?,   // MEASURED; output under <dir>/pilot/
              rests_on?,                         // GUESS; free text, no URLs or source ids
              band?,                             // optional {abs: x}, x > 0: absolute half-width within which a measurement holds the value (U55)
              measured_by? }],                   // phase id; required when load-bearing GUESS/PROXY
  cost: {
    rates: [{id, gpu, gpu_memory_gb?, n_gpus, per_gpu_usd_h}],       // checked against the price sheet
    lines: [{id, phase, what, kind: "work"|"allotment"|"storage",
             rate?, hours?,                      // exprs (string, or a bare number); work/allotment
             need?,                              // expr; estimated work when hours is a time box
             usd?,                               // expr; storage or dollar allotment
             optional?: boolean, instead_of?: [line_id], condition?: str}],
    scenarios: [{id, what, set: {number_id: value}}],
    yields: [number_id],
    spend_cap_usd?,
    total_stated: number },
  full_scale: [{id, what, usd: expr, ratio_to?: number_id}],
  outside_budget: [{what, qty, unit}],
  restructuring: {
    sequential_part,                             // card field, ≤ 18 words: what one answer waits on step after step, and how many steps
    method,                                      // card field, ≤ 22 words: why those steps need not run in order and how the plan
                                                 // computes them at the same time; or "none"
    condition?,                                  // what must hold about this system for the method to pay off, and the cheap measurement that checks it
    condition_phase?,                            // id of the phase that makes that measurement before the main spend
    baseline_sequential?,                        // the fastest sequential implementation the plan times, and how it is tuned
    baseline_copies? },                          // independent copies run side by side on the same GPUs, which the plan also times
  scope_gap: [str],
  novelty: {closest_prior,                       // ≤ 30 words: nearest published result and the largest compute amount it used
            closest_source_id?, prior_max_level?: number|null,
            left_open,                           // ≤ 30 words
            decides: "no"|"partly"|"yes",
            searched: boolean},
  limits: [str],                                 // card field(s)
  test_summary,                                  // ≤ 45 words, card field
  sources: [{id, url, quote, supports}],
  files_read: [str]
}
```
Card fields (plain words, no record ids as words, caps in words): question 25, hypothesis 22, predictions.if_lever 22, predictions.if_not 25, test_summary 45, novelty.closest_prior 30, novelty.left_open 30, anchor.what 24, limits (joined) 30, restructuring.sequential_part 18, restructuring.method 22. Any card field may cite `[source_id]`.

A plan is "restructured" when `restructuring.method`, trimmed and lowercased, is not "none" (`gate_restructured`). The two restructuring card fields are shown, checked by `gate_cardfields` and sent to the dramaturg only on a restructured plan. On a restructured plan the existing fields carry the rest: `compute_axis` is the chain length or the number of runs the answer needs; `predictions.if_lever`/`if_not` say where on that axis, as numbers, the parallel version does or does not reach the same answer sooner than each baseline (`if_not` names the expected failure); `anchor` checks the parallel result against the sequential one within a tolerance; `test_summary` names both baselines; `novelty.closest_prior` is the nearest published parallel version.

Expression grammar (cost): numbers; ids of numbers, rates (→ instance $/h), lines (→ line $), and the reserved GIVEN ids `budget_usd` and `fs_usd_gib_month` (the price sheet's `filesystem.usd_gib_month`); operators `+ - * / ^ ( )`; functions `ceil floor min max pow`. Literals outside {0, 0.5, 1, 2, 3, 4, 7, 8, 10, 12, 24, 30, 60, 100, 1000, 1024, 3600, 1e3, 1e6, 1e9, 1e12} are logged as "unlabelled constant". Every expression field (`numbers[].expr`, `lines[].hours/need/usd`, `full_scale[].usd`) accepts a string or a bare number; cost.js reads it through `String()`. A plan may refer to a GIVEN id and may not define it (`reserved` error); the cost block tags both [q]. A plan that uses `fs_usd_gib_month` with no price sheet gets an `undefined` error.

Load-bearing: a number that is an ancestor of any non-optional, non-alternative line's `hours`/`usd`/`need`, any `yields` entry, or any `phases[].gate.on`. Uncertain: load-bearing and (GUESS, or PROXY, or MEASURED with non-empty `differs_in`).

### 2.6 Dramaturg, critic, repairs
```
FINDINGS {items: [{ref, status: "SUPPORTED"|"PARTIAL"|"UNSUPPORTED"|"CONTRADICTED"|"UNREACHABLE", page_quote, note, page_value?: number}]}
          // ref ∈ {"card:<field>", "src:<source_id>", "num:<number_id>", "rate:<rate_id>"}
CRITIQUE {scores: [{criterion, value: integer 1..5 | "NA", ref, reason}],   // ref: "card:<field>" or "plan:<field path>"
          decides_by: phase_id | "none", decides_by_reason}
REPAIR_FIELDS {fields: {<field path>: text}}
REPAIR_EXPR   {numbers: [{id, expr}], lines: [{id, hours?, usd?, need?}]}
```
Card criteria: physical `["stakes","lever","verifiable","open","reshape","baseline"]`; interp `["stakes","lever","verifiable","open","internals","reshape","baseline"]`. `lever` may be "NA" only when `compute_axis` is absent and the branch is exempt (never, under current args; keep the rule). `baseline` may be "NA" only when the plan is not restructured.

Decision rule (`gate_decision`): core refs = `card:question, card:hypothesis, card:test_summary, card:if_lever, card:if_not, card:anchor, card:closest_prior` (plus `card:sequential_part` on a restructured plan) plus every `src:` cited by a core card field. PASS iff no core item is UNSUPPORTED, CONTRADICTED or UNREACHABLE. `num:`/`rate:` items never block; a CONTRADICTED `num:` with `page_value` is re-evaluated as a scenario and blocks only if the plan is then over budget (cost agent exposes `cost_evaluate(plan, given, {overrides})`).

## 3. Module APIs

### text.js
`txt_words(s)->int`, `txt_sentences(s)->[str]`, `txt_normalize_title(s)->str` (lowercase, strip punctuation/quotes, collapse spaces), `txt_jaccard(a,b)->number` (token sets), `txt_coined_codes(s)->[str]` (regex `\b[A-Z]{1,2}\d{1,2}\b` minus whitelist A10 A100 H100 H200 B200 V100 L4 L40 and tokens inside URLs), `txt_numbers(s)->[str]` (numeric tokens, normalised: commas removed), `txt_has_digit(s)->bool`, `txt_contains_record_id(s, ids)->[str]` (exact token match), `txt_norm_number(s)->str`.

### schemas.js
`SCHEMA_QUESTIONS, SCHEMA_OVERLAP, SCHEMA_VERDICT, SCHEMA_OPTIONS, SCHEMA_OPTION_SCORES, SCHEMA_DEDUP, SCHEMA_PRICE_SHEET, SCHEMA_PLAN, SCHEMA_FINDINGS, SCHEMA_CRITIQUE, SCHEMA_REPAIR_FIELDS, SCHEMA_REPAIR_EXPR`. Keep them shallow where possible; PLAN is the one deep record. Add `description` strings where a field's meaning is not obvious from its name (the harness shows them to the agent).

### cost.js
```
cost_parse(src) -> ast | throws {kind:'parse', msg}
cost_eval_plan(plan, given, opts?) -> EVAL        // opts.overrides: {number_id: value}; opts.scenario: id
  given = {budget_usd, price_sheet, budget_covers_storage, budget_covers_tax}   // price_sheet.filesystem.usd_gib_month is the GIVEN id fs_usd_gib_month
  // EVAL.numbers also holds fs_usd_gib_month when the plan refers to it; the block's Budget row then ends "· filesystem $X/GiB-month [q]"
  EVAL = { ok, errors: [{kind: 'parse'|'undefined'|'cycle'|'reserved'|'quote'|'gate_ref', where, msg}],
           numbers: {id: value}, rates: {id: usd_h}, rate_corrections: [{id, stated, sheet}],
           lines: [{id, phase, kind, hours, usd, optional, instead_of, time_box, need_h, margin}],
           planned, planned_with_options, alternatives: [{line_id, total}], unallocated,
           scenarios: [{id, what, total}], yields: [{id, base, by_scenario: {sid: value}}],
           gates: [{phase, on, op, value, base_value, passes, uncut_total_at_threshold, else}],
           uncertain: [{id, basis, value, differs_in, measured_by, cum_spend_through_measured_by, k_budget, k_box, dir: 'higher'|'lower'}],
           full_scale: [{id, what, usd, multiple_of_budget, ratio_to_value}],
           flags: [str], log: [str] }
cost_check_quotes(plan) -> [{id, ok, msg}]       // CITED/PROXY value appears in quote after txt_norm_number
cost_load_bearing(plan) -> {ids: [id], uncertain: [id]}
cost_render_block(eval, plan, given) -> string   // fixed block, cost.md §8.4 format, ≤ 16 lines typical
cost_render_short(eval, plan) -> string          // ≤ 45 words for the card body
cost_render_derivations(eval, plan) -> string    // appendix: each DERIVED number with values substituted
cost_menu(eval, plan) -> [{id, name, value, tag}] // planned_usd, planned_h, unallocated_usd, pilot_cum_usd, gate_value, headroom, fs_*, axis_span, ...
cost_selftest() -> {ok, failures}
```
Headroom: k_budget = smallest k ≥ 1 (log-space bisection over [1, 1000]) at which planned spend with boxes stretched (hours = max(box, need)) reaches min(spend_cap_usd, budget_usd), direction whichever raises spend; k_box = smallest k at which a dependent `need` exceeds its box. Flags per cost.md §8.2 (unmeasured load-bearing uncertain input; measured_by after first dependent spend; k_budget < 1.5; gate failing at base; box ≥10% of planned with no need and no stop_rule; stated vs computed > max($1, 2%); rate corrected to sheet; instance not on sheet). Reference behaviour: `scratchpad/meta/synthesis/cost-sim/gplan.js` and the six encodings `p03,p05,p06,p10,p16,p18.json` (copy to `tests/fixtures/cost/`); expected values are in cost.md §2. The encodings predate this contract: convert field names where they differ, and record each conversion in the test file.

### pick.js
```
pick_hashStr(s)->uint32, pick_mulberry32(a)->fn, pick_u(seed, key)->number in [0,1)
pick_legacy_index(seed, key, n)->int             // the old pickIndex, for the reproduction test
pick_run(input) -> {picks, frontier, inventory, log}
  input = { seed, args: {pool_k, picks_per_branch, require_compute_lever: {physical, interp}},
            branches: [{root, branch: 'physical'|'interp',
                        options: [{key, id, title, total, scores: {criterion: value}, distance, compute_open_status, sequential_status, compute_open}]}],
            clusters: [{topic, members: [key]}],
            seed_ideas: [{key, title, text}] }
  picks: [{key, root, branch, kind: 'top'|'random'|'pool'|'seed', rank, total, tie_note, replaced: [{key, reason}]}]
  frontier: [{root, key, title, compute_open, distance}]      // open ≤ 2, status != none, stakes ≥ 4, not picked
  inventory: [{key, root, branch, title, distance, cluster_topic, total, status, reason}]
            // status ∈ picked_top | picked_random | picked_pool | collided | not_eligible | not_picked
```
Rules (flow §2.10 + criteria §8.4): seeded order u_k = pick_u(seed, `order:${key}`); eligible = distance != ELSEWHERE and not gated, where gated = require_compute_lever[branch] and compute_open_status settled/none and sequential_status none; top, reshape route = among eligible options with reshape ≥ 4 and stakes ≥ 3, the highest reshape + stakes, ties by reshape, stakes, open (interp: reshape, stakes, internals, open), then u_k (log "reshape route"); if none qualifies (log "no reshape option"), the open route: highest total with open ≥ 3 (fallback highest total, log "no open option"), ties by open, then stakes (interp: open, internals, stakes), then u_k; reshape is floored to 1 when sequential_status is none and counts 0 when absent; random = next eligible in u-order; `picks_per_branch` n → n−1 randoms; collisions across roots resolved after picking (keep better distance, then top before random, then lower u_k; loser takes next eligible option in its branch whose cluster has no pick; repeat; log); pool = ELSEWHERE options whose cluster has no pick, one per cluster (lowest u_k), reshape ≥ 4 first, then the rest, each in u-order, first `pool_k` (never by total); seed_ideas all become `seed` picks; branch with <2 eligible picks what it has and logs. Reproduction test: with the old rule (`pick_legacy_index`, strict `>` ties, random from all non-top) the stored scores must give the run's 20 picks (`scratchpad/meta/flow-work/results.json`, `seedlib.py`, `replay.py`; expected picks in `scratchpad/table.md`). Planted: flow P18 (i)–(iv); cases 19 (a reshape-route top beats a higher total on the open route), 20 (compute_open none with sequential named is eligible; both none is not_eligible), 21 (the pool takes reshape ≥ 4 over a lower u_k with no reshape score), 22 (sequential "none: independent runs" floors reshape to 1), 23 (no option at reshape ≥ 4 reproduces the current top pick).

### gates.js
```
gate_opt(options)->{ok, errors}                                  // ids unique, fields non-empty (sequential included), 3..25 options
gate_restructured(plan)->boolean                                 // restructuring.method trimmed, lowercased not "none"; missing or empty counts as none
gate_oc(scores, options, criteria)->{ok, errors, degenerate:[id]} // all ids/criteria present, 1..5, reason ≥ 15 chars and != criterion
gate_totals(scores, criteria, statusById)->{id: total}            // applies the open floor for settled/none; leaves reshape out
gate_dedup(clusters, keys)->{ok, errors}                          // partition; topic ≥ 3 words
gate_dedup_jaccard(options, clusters, threshold)->{ok, violations} // cross-root title Jaccard ≥ threshold must share a cluster
gate_overlap(pairs, rootIds)->{ok, errors}
gate_price_sheet(sheet)->{ok, errors}                             // ≥5 instances incl. 8× H100; prices in (0, 20)
gate_plan(plan, eval, pick, args)->{action: 'halt'|'repair'|'ok', reasons, annotations}
   // halt: schema-level missing required; if_lever == if_not normalised; decision_rule has no digit; levels < 2 or max/min < 2;
   //       no phase; no source; compute_tested == 'no' where required and the plan is not restructured;
   //       eval.planned > budget && total_stated > budget
   // repair: eval.errors of kind parse/undefined/cycle/reserved/quote/gate_ref; planned > budget while total_stated ≤ budget
   // annotations: option_title mismatch after txt_normalize_title (re-key note); every eval.flags; unresolved source ids in card fields;
   //       prior_max_level not in its source quote; novelty fields empty; on restructured plans: condition, condition_phase,
   //       baseline_sequential or baseline_copies empty, condition_phase not a phase id, without a gate, or not before the
   //       phase with the largest core planned spend, anchor with neither independent_code nor tolerance
gate_cardfields(plan, caps)->{ok, failing: [{field, reasons}], annotations}
gate_number_preservation(orig, rewritten)->boolean
gate_findings(items, sentRefs)->{ok, errors, degenerate}
gate_decision(items, coreRefs, plan, eval, given)->{result, blocking: [item], listed: [item]}
gate_critique(critique, cardFieldNames, plan, criteria)->{ok, errors}   // NA: lever without compute_axis; baseline when not restructured
gate_core_refs(plan)->[ref]                                         // adds card:sequential_part on a restructured plan
gate_dramaturg_items(plan, cardFields, opts)->[item]               // the dramaturg's items for main and replay; cardFields [[ref name, plan path]]; opts.rates adds rate: items
gate_selftest()->{ok, failures}
```

### render.js
```
render_card(ctx)->string
  ctx = {pick, option, root_question, plan, eval, given, findings: [FINDINGS, FINDINGS|null], decision, critique|null,
         beyond_prior: boolean|null, annotations: [str], halted: {gate, reasons}|null}
  sections in order: header line; Question; What is known; Hypothesis; If compute is the lever / If not
  (labels "If the hypothesis holds / If not" when compute_tested == 'no'); Test; Compute axis (script line:
  quantity, levels, closest prior level, beyond_prior, "prior art checked without web search" when !searched);
  Check first; Would not show; Cost (cost_render_short); on a restructured plan a Restructuring section after Hypothesis
  ("**Restructuring.** {sequential_part} {method}"), otherwise the script line "*Restructuring.* none." after Compute axis;
  then "Judges" and appendix: cost_render_block, cost_render_derivations, every non-SUPPORTED finding verbatim (both samples),
  critique scores with ref text and reason, option-critic scores and reasons, "Producer says (not judged)": expected, compute_tested, decides, searched; link to producer.md
render_table(rows)->string                   // index: ~25 words/row; columns per criteria.md §8.5, Reshape (option → card, no drop labels), Baseline ("—" when NA), plus "decides at $X · plan $Y · N GUESS"
render_inventory(inventory)->string
render_frontier(frontier)->string
render_result({header_counts, table, frontier, cards, inventory, log})->string   // RESULT.md; header prints on-goal cards U4 and U3
render_selftest()->{ok, failures}
```
Word budget target: prose ≤ 222 words, whole card ≈ 290–320 words before the appendix; restructured cards about 315–340 (the section's caps add up to 40 words).

### prompts.js
Functions returning strings; verbatim originals as `ORIG_*` constants; a `PROMPT_DIFF` string listing every in-body edit. Sources: INTEGRATED.md §3, substrate.md §10, cost.md §8.5 (trimmed to the minimal-estimates decision), criteria.md §8.1–8.3, options-and-card.md §2.2 and §5.3. Required exports:
`P_PLAYWRIGHT(EX1, EX2)`, `P_GUEST(EX1, EX2)`, `P_REASK(roots)`, `P_OVERLAP(roots)`, `P_FRAMER(question, path)`, `P_WIDENER(framerPath, path)`, `P_DEEPENER(framerPath, path)`, `P_INTERP(framerPath, path)`, `P_DEDUP(lines)`, `P_OPTION_CRITIC(root, criteria, options)`, `CRIT_OPTION(branch)`, `P_PRODUCER({idTitle, branchPath, path, dir, optionRecord, rootQuestion, framerPath, priceSheetText})`, `P_EXTRACT(producerPath, dir)`, `P_REPAIR_EXPR(errors, record)`, `P_REPAIR_FIELDS(fields, caps, record)`, `P_WRITER(root, option, planNoCost, menu)`, `P_DRAMATURG(items)`, `P_CRITIC(root, option, cardText, planFields, criteria)`, `CRIT_CARD(branch)`, `P_PRICE_SHEET()`, `ROLE_FILES` (object name → markdown with frontmatter `name`, `description`, `tools`, `model`), `EX1_TEXT`, `EX2_TEXT`. PRODUCER verbatim text with ": one machine, up to 8 GPUs," removed (it reads "up to $1,000 of GPU credit at Lambda's on-demand prices (https://lambda.ai/pricing)"). No prompt tells a generator which values halt or score (H1).
Sequential-structure prompts (prompt version qt2-2): the shared branch suffix asks for `sequential` right after the `compute_open` sentence; the WIDENER carries a second definition sentence; `CRIT_OPTION` adds `reshape` for both branches; `P_OPTION_CRITIC` passes each option's `sequential`; the PRODUCER suffix adds the restructuring paragraph after the sentence on sources, and its card-field list and caps gain `restructuring.sequential_part` 18 and `restructuring.method` 22; `CRIT_CARD` adds `reshape` and `baseline` and edits `lever` (c) (the speedup sentence is deleted); `P_CRITIC`'s decides_by sentence excludes only throughput the question does not ask about; `PROMPT_DIFF` lists each edit.
Role files: `qt-bare` (tools: none; if the harness rejects an empty list use `Read` and the sentence "Decide only from the text in the prompt."), `qt-research` (WebFetch, WebSearch, Bash, Read, Write, Edit), `qt-producer` (same), `qt-web` (WebFetch, Bash), `qt-extract` (Read). Model pinned only in `qt-extract` (sonnet); other models are passed per call.

### main.js (workflow body)
Args: `seed`, `base` required; `fixed_roots?: [str]` (5), `seed_ideas?: [str]`, `require_compute_lever` (default both true), `deepen_on_signal` (false), `pool_k` (3), `picks_per_branch` (2), `budget_usd` (1000), `budget_covers_storage` (true), `budget_covers_tax` (false). Missing required → `return {error}`.
Stages per INTEGRATED.md §3: S0 selftests; S1 generators (`qt-bare`) + S1b overlap (sonnet) + one re-ask; price sheet (`qt-web`, sonnet) in parallel with framers; S2 framers (`qt-research`); S3 branches (`qt-research`); S4′ option critic as each branch returns (`qt-bare`, session model); barrier; S4 dedup (sonnet) with Jaccard check and one resample; S5 `pick_run` (options carry `sequential_status`; the reshape floor is applied and logged before it); S6 producers (`qt-producer`) → extract fallback (`qt-extract`) → `cost_eval_plan` + `gate_plan` → repair (`qt-bare`, sonnet) once → halt rows; S7 render by default (`gate_cardfields` → repair fields once with `gate_number_preservation`); S8 dramaturg (`qt-web`) on items built from the card fields, sources, numbers (CITED/PROXY load-bearing or in full_scale) and rates → `gate_decision`; S9 critic (`qt-bare`, sonnet) on every card in parallel with the dramaturg; second dramaturg on each PASS and on 2 seeded REJECTs; S10 return `{table, cards, inventory, frontier, log, result_md, price_sheet}` where `result_md = render_result(...)` and `price_sheet` is the sheet the run read (null if it failed twice; replays need it). Labels: `${root}:${branch}:${kind}:${stage}`. `optionRecord` (what a generator or judge sees of an option) carries `sequential`; `header_counts.u4` counts distinct clusters among first-sample PASS cards whose critic scores `reshape` ≥ 4 and `baseline` ≥ 3. Every agent call passes `agentType` and, where this contract says so, `model`. Agents that return null are logged and handled (null never throws).
Harness facts: `agent(prompt, {label, phase, schema, effort, agentType, model})`; `pipeline`, `parallel`, `log`; no filesystem; the launching user turn is relayed to every agent (keep task text self-sufficient).

### replay.js (workflow body)
Args: `phase: 'A'|'B'`, `seed`, `given`, `price_sheet?`, and the stored inputs the main session extracts (the script cannot read files): `picks: [{root, branch, kind, id, title, producer_path, dir}]`, `options_by_branch`, `roots`, `old_scores`. Phase A: price sheet (if absent) → `qt-extract` on each producer.md → `cost_eval_plan` + `gate_plan` → render; writer side cell (`P_WRITER` with menu) on the 10 picks lowest in u-order; returns records, cards, both texts, gate outcomes. Phase B (args include phase-A records and planted cards): dramaturg on all cards + planted set; critic on all; option critic ×3 samples per stored branch; dedup judge on stored options with Jaccard check; overlap judge on stored roots; returns raw outputs. Stored options get `sequential` = "not given (stored run)", so no reshape floor applies and the option critic reads the summary; extraction fills `restructuring`; phase B reads a record whose plan has no `restructuring` (written before the field existed) as `{sequential_part: '', method: 'none'}`. `tools/prepare_replay_args.py` builds the args JSON from `scratchpad/meta/flow-work/results.json`, `scratchpad/table.md` and `/home/hal/stage/runs-v3/seed-1`; `tools/score_predictions.py` scores the filed predictions (cost.md C1–C12, criteria K1–K3, flow P8′/P9′/P10′, options-and-card O3/P2′, and the replay parts of the reshape predictions HP3 and HP5) from the replay outputs and prints a table.

## 4. Done criteria per agent
- Module file(s) under `src/`, tests under `tests/`, fixtures under `tests/fixtures/<module>/`. `node tests/run.js` passes for your module (other modules may be absent: the runner skips a missing file and your tests must not depend on another agent's module except through the APIs above, stubbing locally inside your test file if needed).
- `<prefix>selftest()` implemented with the planted cases named in the reports for your area.
- Final message: file list, test count and result, every place you deviated from this contract and why, and open questions. No prose beyond that.

## 5. Changes after build (integration)

The seven module agents' reported deviations accepted as the actual behaviour, and the integration fixes. Where this section and §1–§4 disagree, this section wins.

**pick.js**
- Frontier: options with `open` ≤ 2 (after the settled/none floor), status != none, stakes ≥ 4, and not picked (any kind).
- Pool gate: pool candidates must also pass the compute-lever gate (status not settled/none where `require_compute_lever[branch]`).
- `pick_run_legacy({seed, branches: [{root, branch, options: [{key, id, title, total}]}]}) -> {picks: [{key, root, branch, kind, id, title, total}]}`: the first run's rule (top = first of the highest totals, strict `>`; random = `pick_legacy_index` over the other options in list order), exported for the replay.
- `open ≥ 3` for the top pick applies whatever `require_compute_lever` says. `rank` is the 1-based place among all options of the branch (total, tie keys, u_k). `tie_note` is "tie of N broken by open / internals / stakes / seeded order" on top picks, '' elsewhere. Seed picks have root, branch, rank and total null, no cluster and no inventory row. Collisions are only across roots; a losing slot with no candidate left is dropped and logged.

**render.js**
- ctx extra fields: `decision2` (gate_decision on findings[1], or null: "PASS 2/2"), `producer_path` (the producer.md link; main and replay both set it, the one name render reads), `n_options` (options in the pick's branch: "random 8/11"). main also sets `tag`.
- The payoff ("$X at P · plan $Y · N GUESS") is in the Judges line and the table's last column, not the header. Compute axis prints the range and the number of levels. Check first appends "Tolerance: X." when anchor.what lacks it. Would not show is `limits` only. Appendix adds Annotations and Root question before the producer link. A seed pick's header reads "seed pick" and its table row `seed·idea·N` with Picked "seed".

**cost.js**
- `uncertain[].dir` ('higher'|'lower'): the direction that raises spend; the block prints "budget reached at X (k× dir)".
- Box flag as log: a constant-hours time box ≥ 10% of planned with no need and no stop_rule goes to `eval.log` ("time box X (N h, P% of plan): work not estimated"), not to flags (minimal estimates).
- Extra flags: uncut plan over budget at a gate threshold; planned spend over budget; `measured_by` naming a phase not in the plan. Duplicate ids across numbers, rates and lines are `reserved` errors; `undefined` also covers a non-DERIVED number with no value, a line with neither rate+hours nor usd, unknown rate, `instead_of`, yield, `ratio_to`, scenario key, override key or `opts.scenario`. Any parse, undefined, cycle or reserved error stops evaluation (`planned` null, `ok` false); quote and gate_ref errors do not.
- Overrides and scenarios evaluate with time boxes stretched to their need. `ratio_to_value` is usd ÷ value(ratio_to). Alternative totals are relative to the core planned spend. `cost_menu` values are rendered strings; extra ids `planned_with_options_usd`, `gate_value_2…`, `fs_<id>`, `fs_<id>_x`, `fs_<id>_ratio`, every yield and every DERIVED number. "Main guess" = the uncertain input with a `measured_by` and the smallest k_budget.
- PROXY/GIVEN details: `cost_check_quotes` checks CITED and PROXY values against their quote (commas, Unicode minus, k/K/M/B/T multipliers; a number inside a word such as "H100" does not count); a missing quote is logged "not checked", not an error. GIVEN ids are `budget_usd` and `fs_usd_gib_month` (integration fix 12), tagged [q]. `budget_covers_storage: false` drops storage lines from planned spend; `budget_covers_tax` changes only the Budget row text.

**gates.js**
- `gate_cardfields` fails a field on: its word cap; a record id (only ids holding a digit or "_"); a coined code; cost text (a dollar figure other than "$1,000", a multiple of the budget, compute-hours); an `[id]` that is not a source. Neither if_lever nor if_not holding a digit fails `predictions.if_lever`. Sentences over 20 words are annotations only.
- `gate_core_refs` adds the sources of `anchor.source_id` and `novelty.closest_source_id`. `gate_decision` re-evaluates a CONTRADICTED `num:` with `cost_eval_plan(plan, given, {overrides})`; with a null plan (planted cards) nothing is re-evaluated; its `ev` argument is unused. `gate_oc` and `gate_findings` return ok false on degenerate items. `gate_plan`: a missing required field halts at once with no annotations; `speedup.extends_range` exempts the whole levels check; a title mismatch is annotated, the caller re-keys.
- `gate_dramaturg_items(plan, cardFields, opts)` (integration fix 8): the one item builder main and replay call. `[s1, s2]` citations split as `gate_cited_ids` splits them; full-scale reach uses cost's expression index. Its signature drops the `costEval` argument the fix list named: nothing in the builder reads an evaluation.

**schemas.js**: expression fields accept a string or a number (`anyOf`, integration fix 11); `cost.scenarios` and `cost.yields` are optional; `anchor` is an anyOf of the two forms; the id pattern is stated in a description only.

**text.js**: `txt_jaccard` uses the tokeniser the 0.4 threshold was calibrated with (strdedup.py); `txt_numbers` returns normalised values; `txt_norm_number` handles M and the Unicode minus; `txt_coined_codes` returns every occurrence.

**prompts.js**: `qt-bare` declares `tools: []`. The `qt-research` body reads "You read only the files the prompt names; fetch any web page you need. You return only the schema." The PRODUCER drops the colon with the removed words, its bounded read admits "what you write under [dir]", and it names `fs_usd_gib_month` beside `budget_usd`. `EX1_TEXT`, `EX2_TEXT`, `PROMPT_DIFF` keep their contract names; helpers are `P_str`, `P_lines`, `P_branchSuffix`, `ROLE_md`, `ROLE_BODY`. `PROMPTS.md` and the role files are generated by `tools/genmd.js` and `tools/writeroles.js`.

**main.js**
- Labels: pick stages `${root}:${branch}:${kind}:${stage}` (seed picks `seed:idea:seed:<stage>`); a resample appends `-resample` to the stage; the second dramaturg sample is `dramaturg-2`. Before picking: `roots:playwright`, `roots:guest`, `roots:overlap`, `roots:<generator>:reask`, `run:price-sheet`, `run:dedup`, `R<n>:framer`, `R<n>:<branch>:<role>`, `R<n>:<branch>:option-critic`. Two picks of the same kind in one branch share labels.
- A plan for another option of the same branch is re-keyed to it, halting only if that option's cluster has a pick; one failed cost repair halts as "cost record broken"; the critic gets one resample; the overlap judge is not resampled and each generator is re-asked at most once; thrown errors in a pick become "script error" halt rows; a render failure falls back to the raw record. Card caps and criteria lists live in main.
- Seed ideas: physical card criteria, exempt from the compute-lever halt (their pick has branch null); header and table say `seed`.
- `calibration` in the return (2026-10-21): one record per pick, `{key, title, state, plan_usd, required: [{id, name, unit, band, basis, value, differs_in, measured_by, cum_spend_through_measured_by, k_budget, phase, line}], resolved: [], anchor, predictions, judged}`; state is `not_judged` (halted), `rejected`, `calibration_required` (PASS with a load-bearing GUESS or PROXY) or `no_unmeasured_input`. A measure run (`launch.js <exp> measure`) compiles from it and resolves inputs through the ledger. U55 (2026-11-03, contract gap G2): `name`, `unit` and `band` copy the plan's `numbers` entry with the same `id` (each null when absent; a `band` that is not `{abs: x}` with finite `x > 0` counts as absent), and `judged` is `{plan, pick, given, gate_args}`: the plan the record's `plan_usd` was evaluated from, the pick, and the `given` and `args` objects that `cost_eval_plan` and `gate_plan` received for it, or null when the pick has no evaluated plan Each is a copy taken when they received it: a later change to the plan (a field repair, for example) never reaches `judged` (second review of U55, 2026-11-03). An m5 calibration run (`args.card`, m5/SCHEMAS.md "Card calibration (U54)") measures the inputs, and `m5/card_resolve.js` ("Card write-back and re-judging (U56)") writes a copy of this array with `resolved` entries, a state that may become `calibrated` or `refuted`, and `rejudged`; the tree itself only ever writes `resolved: []`. U55 changes no prompt and no other output: a rerun with `--resume <earlier run's out dir>` answers every agent call from the cache and reproduces the earlier run's table, cards and calibration states, adding only the new fields.
- `sanitizePlan` before G-plan (2026-10-20, blind-01): a producer number under a `cost_GIVEN` id is dropped, and a `full_scale[].ratio_to` that is not a number id is removed, each annotated; `REPAIR_EXPR` rewrites expressions only, so the gate's "repair" action could never clear either error and every such card halted "cost record broken".
- `deepen_on_signal`: when set and the framer returned signals, the DEEPENER prompt gets one more line, "Signals from the framer: <subproblem>: <what compute buys>; …".
- Annotations: "inconsistent: decides_by none with lever ≥ 4" (criteria case 17); "prose over 240 words (N)" when the card body before Judges, without its header and italic script lines, exceeds 240 words.
- Before the final render, every `num:` item either dramaturg sample judged UNSUPPORTED, CONTRADICTED or UNREACHABLE is shown as `basis: 'GUESS'`, `rests_on: 'citation not confirmed: <status>'` (citation fields dropped, `measured_by` kept) in a plan copy re-evaluated for render; the record keeps the producer's plan and eval.
- `header_counts.u3` (on-goal cards): distinct clusters among first-sample PASS cards whose `plan.compute_tested` is "yes" or "partly".

**replay.js**
- Phase A records: `{pick: {key, root, branch, kind, id, title}, plan, eval, gate, card, writer_text, writer_raw, menu, block, repairs, cardfields, np_failures, beyond_prior, annotations, halted, error?}`; a halt is recorded and the pick still gets card fields (one repair), card and writer; only a null extract stops it. Phase A returns `{phase, price_sheet, records, log}`.
- Phase B requires `price_sheet` and returns `{phase, dramaturg: [{key, items, findings, findings_ok, decision}], planted: [{id, expected, items, findings, findings_ok, decision}], critic: [{key, critique, critique_ok}], option_critic, new_scores, dedup: {samples, ok, clusters, jaccard_pairs_n, jaccard_violations_n}, overlap: {raw, gate}, pick_run, pick_run_by_sample, pick_run_legacy, log}`. A planted card is one `card:text` item plus one `src:` item per source, all core, decided with no plan. The option critic is never resampled (independent samples); scores are the rounded mean, distance the median label.
- `planted_cards` come from `tools/make_planted.py` (W11, W13, I1: altered quote, changed number, broken URL, clean).

**Tools and probe**: `tools/e2e_main.js` and `tools/e2e_replay.js` run the built bundles with stub agents; `tools/make_planted.py`; `tools/measure_floor.py` (context floor per agent; thresholds qt-bare ≤ 12K, qt-research ≤ 15K); `probe/probe.js` (Stage-1 workflow: one qt-bare and one qt-research agent); `tools/score_predictions.py` also scores O4, O6 (mechanical), C2 and C8.

**Sequential-structure field and reshape criterion (2026-10-16).** Applied in §0, §2.2, §2.3, §2.5, §2.6 and §3 above; where this entry and the earlier §5 items disagree (the pool gate, `u3` as the only on-goal count), this entry wins.
- Options gain `sequential` (G-opt: non-empty) and the script's `sequential_status`; the option critic gains `reshape`, floored to 1 on `sequential_status` none and left out of every total. Eligibility, top pick and pool follow §3 `pick.js`; a gated option's inventory reason reads "compute_open <status>, sequential none". The frontier is unchanged.
- `PLAN.speedup` is replaced by the required `PLAN.restructuring`; the levels check has no exemption; `compute_tested` "no" halts only a plan that is not restructured. `gate_restructured(plan)` is the one predicate main, replay and the gates use (render has its own copy, `render_restructured`, since render may not call gates): a missing record or an empty `method` counts as none, as "none" does. The "before the main spend" annotation fires when `condition_phase` is at or after the phase with the largest core planned spend (non-optional, non-alternative `eval.lines` dollars); with no evaluated lines it is not checked.
- Card criteria gain `reshape` and `baseline`; G-crit accepts `baseline` "NA" only on a plan that is not restructured (a score is also accepted there). The card's restructuring fields go to `gate_cardfields` and the dramaturg only on restructured plans; the critic's card text lists them on every plan, so it reads `method: none`.
- Card: a restructured card's prose may run 40 words over the 240-word annotation threshold (280), the two restructuring caps. Table: Reshape → and Baseline columns before Decides at. RESULT.md header: "on-goal cards U4 n · U3 m".
- S0: pick cases 19–23; gate_selftest adds a planted set of two highs (a linear-Gaussian smoother over 10^6 steps computed as a parallel prefix; an alignment dynamic program along anti-diagonals) and two lows (eight independent jobs; an ensemble run as copies side by side), which checks only the gates (G-opt, G-oc, totals, G-plan, core refs, card fields, dramaturg items, G-crit); the judges' calibration on these is a model run, not S0.
- Replay: phase B normalises records without `restructuring` on read (phase-A records are not modified); `tests/replay.test.js` now expects `model: 'sonnet'` on the extract call, which replay.js already passed. `tools/score_predictions.py` scores the replay parts of HP3 (option `reshape` on the 119 stored options) and HP5 (card `reshape` and `baseline` on the stored plans).

**Dedup fallback and lever labels (2026-10-17, after replay B).** `gate_dedup` returns `{ok, errors, soft}`: `ok` covers the partition only; a topic under 3 words is a soft fault. The dedup check still resamples on any fault (partition, soft, Jaccard); after both samples fail, `dedup_best(samples, options, keys, threshold)` keeps the sample whose partition is valid with the fewest soft faults plus unmerged Jaccard pairs (ties to the earlier sample), and only without one does the run fall to one cluster per option (replay B lost a 119-option clustering to one Jaccard-0.4 pair and a 2-word topic). Render: a restructured plan keeps the "If compute is the lever" labels and "plan expects: the lever" when `compute_tested` is "no", matching the gates, which halt only an unrestructured "no".
Dedup handles: the dedup judge (main and replay) sees each option as `root:branch:K<n>` (n = its position in its branch) instead of its id; `dedup_handles(options)` builds the lines and the map, `dedup_unhandle(clusters, toKey)` maps the judge's members back to option keys before any gate (unknown handles pass through and fail `gate_dedup`). Run F's branches wrote long ids ("A. Inference-time steering of VLA internals"), which the judge shortened to keys that did not exist, so both samples failed and the run fell to one cluster per option.

**Seed records (2026-10-17).** `seed_ideas` entries may be option records `{title, text, root_question, kind, root_link, compute_open, sequential, source_urls}` as well as strings. A record's `root_question` reaches the producer and critic (in place of null), `kind: 'interp'` selects the interp card criteria, and the other fields fill the option record the producer and critic read. Strings behave as before.

**Sources and instance hours (2026-10-18).** The PRODUCER suffix adds two sentences: a line's hours are wall-clock hours of the whole instance, not GPU-hours (40 GPU-hours on an 8-GPU instance are 5 hours); and cited pages must open without a login or paywall, a value found only in a paywalled full text being taken from an open source instead. When the planned total is over budget while the stated one is not, and the ratio is within 5% of a multi-GPU rate's GPU count, G-plan adds a repair line naming the GPU-hours mistake, and P_REPAIR_EXPR may then divide by that GPU count (its one allowed new number). Found on the immersion-coolants runs: a paywalled anchor table rejected round 0, and GPU-hours at an 8-GPU rate halted round 1 at 7.9x.

**Understudy runtime (2026-10-21).** `idea/wf.js` serves `agent()` from two model families (OpenCode via oc.js, Claude via claude_cli.js) with the other family as understudy; policy in `idea/understudy.js`, config in `config.json` `understudy`. Scripts are unchanged: the same prompts and schemas go to either family; a pinned `model: 'opus'|'sonnet'|'haiku'` selects a tier, not a vendor. `workflow({scriptPath})` is provided one level deep and `budget` as a stub. The bundle (dist/) is not affected. The Workflow-tool runtime remains the other way to run a dist script; wf.js runs now also record, per call, the family that answered and why.
