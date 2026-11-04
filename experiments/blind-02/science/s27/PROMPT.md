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
## Step s27 (fixture analysis for margins: error budget, sealed tolerance rule, fixture run design; no network)
Your step folder is `experiments/blind-02/science/s27/`. Read `science/s01/` to `science/s26/` first, above all s13's `FINAL.json` (the parts, arms and comparisons K1 to K7), s15's shapes and s26. The sealed comparison mechanism is merged (commit 65cd5d59): read `dut/pipeline/m5/SCHEMAS.md`, section `Sealed comparison (U57, U58)`, whole; it is the contract s23 drafted and s24 and s25 audited, as implemented. The operator demonstrated its isolation on a live box before this step and measured its overhead: public probe shakedown-m5 run20 (code e3ebd33c; experiments/shakedown-m5/predictions/run17-20_scored.md): 18 invocations, 0 leaks and 0 failed controls over 30 hostile arm and evaluator parts; about 30 s per invocation outside the parts' own walls (comparison-job receipt median 8.0 s, comparison receipt median 29.5 s, parts median 7.2 s); USD 0.49 for the box. The merge adds one later fix round (allow lists, cleanup order, exemption pattern), checked by tests and a Codex review but not re-probed on a box.

Owner decisions of 2026-11-03: the margins of the output comparisons (K1 to K3, and any other margin the comparisons need) come from independent fixture analysis: on fixtures disjoint from the main comparison's inputs, never from the arms' differences on the main inputs. Establish a defensible numerical error budget and seal the resulting tolerances before the main comparison; if that is not possible, keep the uncertainty (the main comparison then states it and claims no tolerance it cannot defend). One combined box ceiling of USD 100 covers the calibration and main runs, including setup, failed attempts and idle time (USD 1.67 spent so far, whole allocations, up to USD 3.29 per hour for one H100); the main runs must fit what remains after this one.

Answer in `ASSESSMENT.md`, in this order:
A. The main comparison's inputs as s13 and s15 fixed them (by id), and the fixtures you choose: how each fixture exercises the same numerical path as the main inputs (precision, reductions, the code paths K1 to K3 compare), and why it is disjoint from every main input (state the rule that makes it so). Use the published materials only.
B. The analytic error budget, per output the margins concern: the sources of run-to-run and arm-to-arm numerical difference that a correct arm can show (floating-point precision, reduction and summation order, nondeterministic kernels, library versions, compiler flags, seeds), each with its expected size and the evidence for it (quote the published source, file and line). Say which sources the fixtures measure and which only the analysis bounds.
C. The tolerance rule, sealed now, before any fixture result: exactly how each margin of the main comparison will follow from the fixture run's recorded values and the analytic budget (for example: margin = the larger of k times the largest self-disagreement between duplicate arms over the fixtures and replicates, and the analytic bound; with k and every constant fixed here), what result of the fixture run makes a margin indefensible (then the uncertainty is kept, as the owner directs), and how a later step applies the rule without judgment. Write it in `TOLERANCE_RULE.md` and as `tolerance_rule.json` `{"items": [...]}`, one item per main comparison margin.
D. The fixture run: one design file in this folder for `args.comparison`, in the contract's exact schema. Arms: A0 the published baseline, a duplicate of A0 with identical commands (self-agreement), and the arms whose outputs the main comparison compares; inputs: the fixtures only; outputs: those the margins concern; the evaluator only if the margins need it. Comparisons may be none (a run that only records values for the rule) or exact-agreement checks that cannot bias the rule; state which and why. Choose `replicates`, `warmup` and `timeout_s` so that the run fits one allocation inside the 6 h run limit with the measured overhead; `budget_s` below 19800. Project box hours and USD.
E. What each possible fixture result would decide (margins defensible, indefensible, or the fixture run failing), and how the main comparison's design follows.
F. Narrowing: unchanged, or exactly what changed.

The brief you write is the run's whole brief: the seed's exact bytes, then the materials addendum's section copied unchanged from `m5/b01_materials/BRIEF_run1.md`, then one section headed `## Comparison request (science step s27)` that asks for the fixture run as the design's view describes it. That section, and the design's `what`, `spec`, `select`, `commands` and `env` text the run's agents see, state no margin, threshold, confidence, reference value, expected result or tolerance rule (the operator screens them against the design's sealed numbers and refuses a brief or design that carries one). Keep no copy of the design outside this folder.

Seal your predictions for the fixture run in `PREDICTIONS.md` and `predictions.json` (for example the largest self-disagreement per output, whether the analytic bound covers it, whether each margin will be defensible). s26 sealed none: write `outcomes.json` `{"items": []}`.

`NEXT.json`: `{"action": "m5", "brief": "<file in this folder>", "new_run_flags": [], "comparison": {"design": "<design file in this folder>"}}`, or `{"action": "stop", "reason": "<stop_reason>"}` when no fixture run is justified (with `needs_owner` if a decision only the owner can make blocks it, `limits` if it cannot fit the budget).

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"error_budget_feasible"`: `"yes"`, `"partly"`, `"no"`
- `"budget_basis"`: `"fixtures_and_analysis"`, `"fixtures_only"`, `"analysis_only"`, `"none"`
- `"fixtures_disjoint"`: `"yes"`, `"no"`
- `"self_agreement_arms"`: `"none"`, `"one"`, `"two_or_more"`
- `"margins_covered"`: `"all"`, `"some"`, `"none"`
- `"tolerance_rule_sealed"`: `"yes"`, `"no"`
- `"fixture_comparisons"`: `"none"`, `"exact_only"`, `"other"`
- `"evaluator_in_fixture_run"`: `"yes"`, `"no"`
- `"next_action"`: `"m5"`, `"stop"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"next_projected_usd"`: `"none"`, `"under_5"`, `"5_to_20"`, `"over_20"`
- `"next_projected_hours"`: `"none"`, `"under_1"`, `"1_to_3"`, `"3_to_6"`
- `"main_runs_fit_after"`: `"yes"`, `"no"`, `"unknown"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 60 minutes.
