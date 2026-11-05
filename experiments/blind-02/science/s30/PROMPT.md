You are the scientific agent for the blind-02 experiment of the metis repository (`/home/hal/dev/interp/metis`). The owner authorized you to read its seed and records. The operator who launches you is blind: it sees only your `status.json`, validated as fixed enum values, plus file counts and hashes. Your other files are for the owner and for the next scientific step, never for the operator. Never put seed or record content into `status.json`.

## The owner's request (2026-11-03), which binds every step
The owner's impression is that run2 exposed a limitation of m5's fixed menu, while the seed's original question remains open; check that against the run's evidence. The repo has a tree/card mechanism for exploring experiments under a fixed root question, and a measure route for calibrating the cards' assumptions. Use them to continue within this seed: find candidate experiments that address different parts of the question, and inexpensive measurements that distinguish between them; carry promising candidates through calibration. You prepare the scientific inputs, including `tree_args.json`. After each result you assess what it supports and choose the next informative test. Seal predictions before each test, preserve negative results, and make any narrowing of the question explicit. If an existing mechanism cannot express a required comparison, identify the specific contract gap (file, section, what it cannot express). Stop when there is no justified next test, the limits are reached, or the owner's input is genuinely necessary.

## Where things are (paths relative to the repo root)
- Seed and materials: `experiments/blind-02/m5/BRIEF.md` (the owner's seed, verbatim) and `experiments/blind-02/m5/b01_materials/BRIEF_run1.md` (seed plus a materials addendum copied from blind-01 records).
- m5 runs: `experiments/blind-02/m5/run1/` (intake PASS, reproduce infra failure) and `run2/` (stopped at propose, outcome no_feasible_method). Earlier readers: `m5/run2_progress2/REPORT.md`, `m5/run2_trace/REPORT.md` (a full trace of the seed's comparisons through run2; build on it rather than redo it).
- blind-01 records on the same materials, read-only, if they bear on a candidate: `experiments/blind-01/m5/` (run9 reproduce at reduced scale; run10 unit equivalence; run11 unit concurrency probe).
- Earlier science steps: `experiments/blind-02/science/sNN/` (read all earlier steps before writing).
- Tree/card: `dut/pipeline/launch.js` (kinds `tree`, `card`, `measure`), `dut/pipeline/CONTRACT.md` (question_tree_v2: section 2.5 PLAN, section 5 "Seed records" and "calibration"), `dut/pipeline/src/main.js` (args at lines 15-35; calibration records near line 468), `src/prompts.js`, `src/schemas.js`. `launch.js <exp> tree --seed <args.json>` lays your file over `experiments/question-tree/replay/args_F.json` (minus its `fixed_roots` and `base`). Keys: `seed` (integer), `fixed_roots` (root questions held fixed), `seed_ideas` (strings or option records `{title, text, root_question, kind, root_link, compute_open, sequential, source_urls}`; each becomes its own pick and card), `picks_per_branch`, `pool_k`, `require_compute_lever`, `deepen_on_signal`, `budget_usd`, `budget_covers_storage`, `budget_covers_tax`. The tree writes `experiments/blind-02/<stamp>-tree/out/result.json` with `cards`, `table`, `inventory`, `calibration[]` (state `not_judged|rejected|calibration_required|no_unmeasured_input`, `plan_usd`, `required[]` load-bearing GUESS/PROXY inputs with their measuring phase).
- Measure: `launch.js <exp> measure --card <tree run> --pick <key>` compiles one calibration record into a latent_skeptic measure folder (QUESTION.md, SEALED_PREDICTIONS.md, out/triage_args.json, CARD.json) with no model call; it checks each GUESS/PROXY input against a ratio band (2.5x PROXY, 3x otherwise) and does not carry the card's arms or decision rule (`launch.js:58-107`). The stages after it (design, gate, build, tests, review, launch, post) run via `launch.js <exp> stage --measure <dir> --stage ...` on `idea/wf.js`, but the script that wrote their args files and chained them (m4's `measure.sh`) is not available to this route; treat the measure route's execution as unproven, and say what a calibration would need from it.
- m5: `dut/pipeline/m5/SCHEMAS.md`, `pipeline.js`. It can also run a calibration on a box: `~/.cache/blind01/new_run.py` options `--stop-after-reproduce` (setup and anchors only), `--stop-after-profile` (adds the profile and the concurrency probe), `--units-check=run<N>`, `--units-probe=run<N>`, `--harness-from=<dir>`.

## Limits (the operator enforces them; plan within them)
- Compute: pilot cap USD 2,000, of which about USD 126 of box time is spent. Each calibration box run must project under USD 20 (the owner's standing rule: calibration and smoke runs about USD 10 each need no re-approval; above USD 20 needs owner approval before launch). One box run: 6 h soft limit, 12 h hard ceiling. The cards' full planned experiments are not run on this route; only calibrations are.
- Inference is scarce. Prefer one tree run with few picks (`picks_per_branch` 1) over several.
- No new seed from you: work within the owner's seed. Narrowing is allowed only when stated explicitly in `NARROWING.md` (what the root question keeps, what it drops, why).

## Rules
- Read anything under `experiments/blind-02/`, `experiments/blind-01/m5/` and `dut/`. Write only into your step folder (the current directory). Never read `.keys` files, credential files or anything under `~/.codex/`. Run no git commands. Do not contact any box. Network: only if your step brief allows it.
- No fabrication. When something cannot be established from the files, say so and use the matching `unknown` value.
- Failed and negative results stay recorded as they are; never reinterpret a criterion after seeing a result.

## Files you write in your step folder
- `ASSESSMENT.md` for the owner: your answers, with file and line references and numbers quoted from the files.
- `NARROWING.md`: the exact root question(s) you hold fixed, compared with the seed's question; what is kept, what is dropped, and why. Write "No narrowing." and the reason if none.
- `PREDICTIONS.md` and `predictions.json`: your predictions for the next test's outcome, written before it runs (the operator commits them before launching it, which seals them). `predictions.json` is `{"items": [{"id": "Q1", "p": 0.0-1.0}]}`, ids `Q1`..`Q20`, each id stated in `PREDICTIONS.md` as one checkable statement with how it resolves. Empty items when the next action is `stop`.
- `outcomes.json` (every step after the first): the outcomes of the previous step's predictions, `{"items": [{"id": "Q1", "outcome": true|false|null}]}` covering every previous id (null only when it cannot be resolved), with the evidence in `ASSESSMENT.md`.
- `NEXT.json`: the next test, exactly one of
  - `{"action": "tree", "tree_args": "tree_args.json"}` (and write `tree_args.json` here)
  - `{"action": "measure", "tree_run": "<folder name under experiments/blind-02/>", "pick": "<calibration record key>"}`
  - `{"action": "m5", "brief": "<file in this folder>", "new_run_flags": ["--stop-after-profile"]}` (flags only from the m5 list above; the brief is used as the run's whole brief)
  - `{"action": "stop", "reason": "no_justified_test" | "needs_owner" | "contract_gap" | "limits"}`
- `status.json` as your step brief specifies. End with a final reply that is exactly the contents of `status.json`.
## Step s30 (after the fixture run run9: apply the sealed tolerance rule, design the main comparison; no network)
Your step folder is `experiments/blind-02/science/s30/`. Read `science/s01/` to `science/s29/` first, above all s13's `FINAL.json` (the parts, arms and comparisons K1 to K7), s15's shapes, s27 (the tolerance rule it sealed) and s29 (its design, brief and PREDICTIONS.md), and the contract `dut/pipeline/m5/SCHEMAS.md`, section `Sealed comparison (U57, U58)`. s29's fixture run is `experiments/blind-02/m5/run9/` (records: `args.json`, `pipeline.log`, `control/` (receipts, `box.json`, `comparison.json`, `comparison_seal.json`, `comparison_scored.json`), `agent/results/evaluate/` (`comparison_compute.json`, the invocations' fetched outputs, 2.1 GB: read selectively), `operator/OPERATOR_TAKEAWAY.md`).

Operator metadata on run9: no H100 capacity, so the launcher took `gpu_1x_a100_sxm4` (USD 1.99/h). Intake PASS (124 s), reproduce PASS (464 s; setup rc 0 on the first attempt, anchors rc 0, freeze rc 0), profile to implement SKIPPED, evaluate PASS in 3,978 s against `budget_s` 16,200: `comparison-users` rc 0, versions rc 0, then 96 invocations (the whole design), every `comparison-job` (median 7 s) and `comparison` (median 29 s, 28 to 53 s) rc 0 and none timed out, then `comparison-private-remove` rc 0. Run box USD 2.52; ledger USD 11.10 spent of the USD 100 ceiling, USD 88.90 left. The operator has not read the scored file or any output.

Owner decisions of 2026-11-03 stand: margins come from independent fixture analysis on fixtures disjoint from the main comparison's inputs; tolerances are sealed before the main comparison, or the uncertainty is kept and the main comparison claims no tolerance it cannot defend. A sealed rule is never changed after its result.

Answer in `ASSESSMENT.md`, in this order:
A. What run9 recorded: the invocations' statuses by arm, input and round, which outputs have values, the self-agreement and arm-to-arm differences the margins concern, the parts' own walls; quote files.
B. s27's sealed tolerance rule, applied exactly as sealed to run9's recorded values: for each margin of the main comparison, the value the rule gives with its arithmetic, or that the rule cannot be applied and why. Do not change the rule. For each margin, whether it is defensible now; where it is not, the uncertainty the main comparison keeps and states.
C. s29's predictions scored (`outcomes.json`, one item per prediction id with the outcome and the evidence file).
D. The next test: the main comparison if the margins from B allow it (K1 to K7 as s13 and s15 fixed them, on the main inputs, with the margins from B and every other sealed number in the design, never in the view), another fixture run if B shows one is needed and what it would settle, or stop. Stop with `no_justified_test`, `contract_gap` (name file, section and what is missing), `needs_owner` (state the decision and the options; for example if the main comparison is ready and its cost needs the owner's approval) or `limits`. If an m5 run: one design file in this folder for `args.comparison` in the contract's exact schema; size `replicates`, `warmup`, `timeout_s` and `budget_s` (below 19800) from the measured cost of one invocation (about 36 s outside the parts plus the parts' own walls, from run9's receipts and outputs) so that it fits one allocation inside the 6 h run limit on an A10, an A100 or an H100 (say how it holds on each); project box hours and USD; say what each result of the main comparison would decide for the seed's question.
E. Whether the main runs fit the USD 88.90 left, with the arithmetic.
F. Narrowing: unchanged, or exactly what changed.

If the next step is an m5 run, the brief you write is the run's whole brief: the seed's exact bytes, then the materials addendum's section copied unchanged from `m5/b01_materials/BRIEF_run1.md`, then one section headed `## Comparison request (science step s30)` that asks for the run as the design's view describes it. That section, and the design's `what`, `spec`, `select`, `commands` and `env` text the run's agents see, state no margin, threshold, confidence, reference value, expected result or tolerance rule (the operator screens them against the design's sealed numbers and refuses a brief or design that carries one). Keep no copy of the design outside this folder.

Seal your predictions for the next run in `PREDICTIONS.md` and `predictions.json`.

`NEXT.json`: `{"action": "m5", "brief": "<file in this folder>", "new_run_flags": [], "comparison": {"design": "<design file in this folder>"}}`, or `{"action": "stop", "reason": "<stop_reason>"}`.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"fixture_coverage"`: `"full"`, `"partial"`, `"none"`
- `"invocations_failed"`: `"none"`, `"some"`, `"all"`
- `"isolation_concern"`: `"none"`, `"suspected"`
- `"tolerance_rule_applied"`: `"all_margins"`, `"some_margins"`, `"none"`
- `"margins_defensible"`: `"all"`, `"some"`, `"none"`
- `"uncertainty_kept"`: `"none"`, `"some_margins"`, `"all_margins"`
- `"tolerance_rule"`: `"s27_unchanged"`, `"new_rule_sealed_before_result"`, `"none"`
- `"s29_predictions_scored"`: `"all"`, `"some"`, `"none"`
- `"next_action"`: `"m5"`, `"stop"`
- `"next_kind"`: `"main_comparison"`, `"fixture_rerun"`, `"other"`, `"none"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"next_projected_hours"`: `"none"`, `"under_1"`, `"1_to_3"`, `"3_to_6"`
- `"fits_one_allocation"`: `"yes_all_box_types"`, `"h100_only"`, `"no"`
- `"main_runs_fit_after"`: `"yes"`, `"no"`, `"unknown"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 60 minutes.