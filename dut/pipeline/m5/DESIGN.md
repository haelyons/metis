# m5: benchmark-first scientific parallelism

This is a design only. It uses the public pipeline contracts; no files under `experiments/` are inputs.
The route stops on failed reproduction, preserves negative results, and produces two separate takeaways.

## Layout, roles, and execution

- `R` is an explicit run directory outside `experiments/`; `A=R/agent/` contains all scientific content, including runtime transcripts.
- `S=R/operator/` contains only `signatures.jsonl` and `OPERATOR_TAKEAWAY.md`. The blind operator can read only `S`.
- `C=R/control/` is script-owned state: policy, immutable seals, stage receipts, and billing. Models cannot write it.
- On the dev box, `B=~/<tag>_run/`, `O=B/results_<tag>/out/`; fetched content goes to `A/results/`, never `S`.
- Reuse `launch.js stage` snapshots/args/returns, `measure/prompt_stage.js`, and `wf.js agent()` with schemas. Add an explicit m5 route/run root; never depend on experiment-local `pipeline.js` or default experiment paths.
- Owner policy (2026-10-26): Codex may read private (blind) content and is preferred for long or open-ended content-reading roles: research, baseline tuning, implementation, independent tests/review, and research takeaways. The self-hosted `lambda/gpt-oss-120b` handles narrow, high-volume extraction, labelling, scientist calls, and votes using bounded evidence packets with source pointers, measurements, and one question.
- No Claude agents for now: Claude inference is reserved for the human-facing operator. Narrow calls use Lambda -> Codex; long calls use Codex -> OpenCode Go. OpenCode may be at its usage limit; fail fast on exhaustion, without waiting or another family. Refusals halt.
- Existing controls: `node idea/wf.js --config R/control/wf.json --script m5/pipeline.js --args R/control/args.json --out R/agent/wf --mode fallback --on-refusal halt`. The m5 script is an implementation unit below; use an explicit run root outside `experiments/`. Store the resolved policy in `C/policy.json`.
- In that full config, set `understudy.primary_family="codex"`, `understudy.chain={"opencode":["codex"],"codex":["opencode"],"claude":[]}`; route narrow roles to `primary_family:"opencode"`. Set `understudy.families.opencode.by_role` to `lambda/gpt-oss-120b` for narrow roles and OpenCode Go models for long roles; set Codex tiers/by-role models explicitly. Lambda is an OpenCode-dispatched endpoint, not a selectable `--family`; chains resolve once from the primary, so narrow fallback ends at Codex.
- `idea/understudy.js` merges defaults: deleting Claude entries alone does not exclude Claude, and `--family` only selects a primary. Remove Claude assignments from routes, overrides, and panels. No family exclusion exists: propose `understudy.disabled_families:["claude"]` plus validation after resolution/before cache reuse and at every dispatch (including panels, repairs, and fallbacks); reject disabled models and incompatible resume provenance. Also propose skipping the repair turn on explicit OpenCode quota/cap errors in `wf.js`; these guards are not implemented yet.
- Give implementer, test author, baseline tuner, and operator separate filesystem views and fresh sessions. A different cwd alone provides no blindness; do not share wf journals, exports, or resume caches across roles.
- `serve/lambda_serve.sh` has one shared state for serve/dev. Schedule them sequentially: persist work on the dev filesystem and fetch packets to `A` before switching. Serve mode cannot attach `--fs`; inference uses local packets through its tunnel. Use Codex (OpenCode Go fallback) while dev remains up.
- Reuse `up --dev --fs metis-env-us-east-1`, `~/.cache/metis-serve/box.sh`, `status`, and confirmed `down`. The watchdog is a lifetime cap, not an idle detector; add a route idle timer and stop on completion/failure.
- Keep `run_<tag>.py` plus `onbox_<tag>.sh` as the only execution wrappers; baseline sources/data/tests are declared payload inputs. Name all build/cache directories in the execution contract. The method never edits the launcher.
- Enforce ONBOX preflight, pinned installs without replacing stock torch, capabilities, real-input 1–2% dry run, and measured guards before every long phase: 1.5x projection, `REMOTE_TIMEOUT`, 600 s fetch margin, remaining USD.
- Detached timeout/marker execution survives SSH loss; atomic endpoint records, raw rows, heartbeat, compute summary and `RUN_VALID.json` survive every exit. Preserve exits 0/2/3/4/5; m5 explicitly stops immediately on anchor failure (4).
- Use the contract's `--stage/--in/--out` interface, injectable external commands, pure parsers, real-output fixtures, and separate work directories per repetition. Keep content logs private; public errors are enums only.
- Any failed gate skips downstream scientific stages, emits their SKIPPED records, and always runs stage 8. Stopping means no further method work, not loss of accounting/takeaways.

## Signature contract and budget

Existing `measure/signature.py` requires every v1 field and rejects extras. Do not attach arbitrary keys to v1.
Add `m5/signatures.py`: an explicit v2 envelope `{schema_version:2, signature:<validated v1>, facts:<stage schema>}`.
Reuse v1 validation/exits/blockers. Stage facts have exact keys/types, reject extras/nonfinite numbers, and use null for unavailable values.
Emit one atomic envelope per stage to `S/signatures.jsonl`; intake emits exactly one, including failure/not-found. Also emit bounded model-call/allocation envelopes for costs.
Allocation envelopes use v1 `kind=launch,type=dev|serve` and numeric `facts.allocated_gpu_s`; sum only allocations for USD/time totals, only model-call records for token totals. Stage costs are attribution, never extra spend.
Use fixed stage/type/id enums and opaque sequential run IDs, never filenames, benchmark names, quoted errors, free text, domain metrics, or content-derived labels. Do not recursively scan agent JSON into operator output.
Every stage carries v1 `status,exit_code,exit_kind,error_class,depth,wall_s,gpu_s,usd,tokens_in,tokens_out,model_family,run_valid,calibration_valid,blockers`; other required v1 fields retain documented defaults.
`depth` is the last completed stage, 0–8. Lambda is an endpoint reported as `model_family=lambda`, although dispatch uses the OpenCode runner. Unknown token counts are marked by `facts.tokens_known=false`, not invented.
In facts below: flags are boolean/null, counts are nonnegative integers/null, ratios are finite numbers/null. `tokens_known` is common; missing stages emit SKIPPED with null facts. `run_valid` reflects anchors only; equivalence/performance remain separate flags.
Costs below are planning estimates of total input+output tokens and allocated workload GPU-hours, summed across GPUs. Add 2–6 GPU-hours for sequential open-model serving and measured idle/startup time.
Target 45–85k tokens, 10–40 workload GPU-hours; private scale can be larger only within the USD 2,000 pilot cap. Reserve USD 100 for shakedown, 1,500 for private work, 400 for failures/idle/serving; no ledger balancing.
Scripts enforce aggregate billed allocation time x instance price, including serving, failed runs, and idle time. `gpu_s` means measured GPU-busy seconds; never substitute allocated seconds. Missing busy telemetry sets `facts.gpu_busy_known=false` (common).

## Stages

### 1. Intake

- In: optional `--brief /path/to/brief`; otherwise a bounded public benchmark search. Role: scientific intake, narrow Lambda extraction (Codex fallback) or Codex research (OpenCode Go fallback), never blind operator.
- Out: `A/intake/{brief.md,benchmark.json,anchors.json,data.json,baseline.json,EXECUTION.json}` with citations, pins/hashes, commands, licences, representative scale, scoring rules, and input/output interface. Do not invent a benchmark when search fails.
- Facts: `found` flag, `anchors_count` count, `data` enum available/partial/unavailable/unknown, `licence` enum permitted/restricted/unknown, `stock_environment` flag, `size` enum tiny/small/medium/large/unknown (<=1/10/100/>100 GiB data+peak working set).
- Gate: found, >=1 credible independent anchor, required data accessible, licence permits intended run, stock image feasible; unknown stock compatibility is resolved by stage 2, false blocks. No brief: cap search at three candidates/two calls; if none qualifies, found=false and stop.
- Cost: 6–10k tokens (search adds <=4k), 0 GPU-hours. Stock feasibility is provisional until a clean baseline launch confirms it.

### 2. Reproduce and establish controls

- In: intake files; scripts stage untouched published source/config under `B/baseline-published/`, data under `B/data/`; run published anchor protocol at representative scale, not a toy extrapolation.
- Out: `O/reproduce/{env.json,anchors.json,baseline-outputs/,raw.jsonl}`, `A/controls.json`. Independent baseline tuner (Codex, OpenCode Go fallback, no method access) produces `B/baseline-tuned/` and configuration-only `A/baseline-tuned.patch` from a small declared settings sweep; no method code yet.
- Facts: `anchors_passed` count, `anchors_total` count, `stock_verified` flag, `tuned_control_valid` flag; v1 validity and blockers reflect measurements. Never silently repair/substitute the published baseline.
- Gate: all anchors pass with original reference tolerances and clean stock launch; failure exits 4 before profiling/method work. Tuning cannot rescue failed reproduction; tuned control passes anchors and intake-declared repeatability bounds, then final sealed equivalence at stage 7.
- Freeze published/tuned source, commands, seeds, splits, environment, and output hashes. Tuner and method author are separate; retain both comparators even if tuning finds no gain.
- Cost: 4–8k tokens for tuning/adapter instructions, 1–4 GPU-hours; scripts perform installs, sweeps, and scoring.

### 3. Profile

- In: frozen controls, real representative inputs. Script runs native stage timers, CUDA events/framework profiler or Nsight when available, plus `nvidia-smi`; one narrow Lambda call may label otherwise unmapped stages.
- Out: `O/profile/{trace,stages.json,raw.jsonl}` and `A/profile-packet.json`: per-stage wall/GPU time, transfers, CPU waits, memory, GPU occupancy/utilisation when measurable, and overlap without double-counting critical-path time.
- Facts: `profile_complete` flag, `timed_fraction` ratio in [0,1], `gpu_telemetry` flag. Gate: complete critical path and >=90% timed coverage; missing counters stay explicitly unavailable, timing gaps stop proposal preparation.
- Cost: 0–2k tokens, 0.25–1 GPU-hours. Profile published baseline first; also profile tuned control if its bottleneck differs. Final performance uses unprofiled runs.

### 4. Seal predictions

- In: `A/profile-packet.json`, controls, anchors, outcome definition. Scientist makes one narrow Lambda call (Codex fallback); script supplies Amdahl bounds and feasible entries from the five-item menu below.
- Out: `A/PREDICTIONS.json`; script canonicalises bytes and writes SHA-256 plus ordered timestamp/receipt to immutable `C/seals/0001.json` before method code exists. Store a read-only copy; verify it before build and evaluation.
- Seal expected speedup intervals for every feasible menu entry, predicted outcome-vs-compute points, equivalence metrics/tolerances, stochastic paired-seed tests, sample sizes, confidence rule, hardware/cost basis, timing scope, and minimum worthwhile gain.
- Seal fixed evaluation inputs/splits, at least three compute budgets, repetitions (>=5 timing pairs), warmup, scheduling order, and equal-outcome target. Equivalence margins come from scientific requirements/baseline variability, never method outputs; lack of significance alone is not equivalence.
- Facts: `seal_present` flag, `seal_verified` flag, `prediction_count` count. Gate: complete, immutable seal; no feasible entry stops as a negative result. Any scope/tolerance change starts a new sealed run; never overwrite prior predictions.
- Cost: 2–4k tokens, 0 GPU-hours beyond already recorded baseline variability runs.

### 5. Propose and gate once

- In: profile, sealed predictions. Script ranks feasible methods by predicted gain/cost; menu is exactly data-parallel over inputs, batching, multi-GPU, ensembles, pipelining. Scientist chooses one in one narrow call.
- Five cheap skeptics receive the same bounded claim/evidence packet in separate sessions, no other votes. Lambda preferred, otherwise Codex; each returns approve/reject/abstain plus fixed reason codes. Script aggregates; no critique-merging agent.
- Out: `A/proposal.json`, `A/votes/1.json`–`5.json`, `A/GATE.json`. Facts: `method` enum of the five menu entries/none, `expected_speedup` ratio from seal, `votes_approve` count, `votes_total=5`, `vote_share` ratio in [0,1], `gate_pass` flag.
- Gate: >=4/5 approve, sealed minimum worthwhile gain predicted, resource guards pass; missing/invalid/abstaining votes count against approval. Fresh sessions reduce shared-context bias; vote share is not calibrated probability. No repeated voting to obtain a pass.
- Cost: 6–9k tokens total, 0 workload GPU-hours. Re-gate only for a scope change under a new seal/run.

### 6. Implement and independently test

- In: frozen baseline, `A/proposal.json`, sealed interface, execution contract. Method author uses Codex (OpenCode Go fallback) on dev box; output `A/method.patch` applies only to `B/baseline-published/` in `B/method/`, plus declared configuration changes.
- Separate test author gets anchors, baseline interface/fixtures, sealed tolerances and contract in a restricted view; never diff, method source, build transcript, or implementer session. Output `A/tests/` is frozen before method results are released.
- Reuse upstream tests; author only missing adapter/parsing/guard, equivalence, and parallel edge tests (ordering, dropped/duplicated inputs, tails, seeds). Implementer never sees independent test source; trusted scripts execute tests and return bounded failure categories.
- Out: `O/build/{tests.json,smoke.json}`, `A/REVIEW.json`. One independent content-capable review before launch checks diff, seal, payload and projected costs; reviewer cannot alter test expectations.
- Facts: `patch_applies` flag, `tests_pass` flag, `blind_tests` flag, `launch_review_pass` flag. Gate: seal unchanged, baseline untouched, tests/smoke pass, review passes; one bounded repair using existing tests, then stop on failure.
- Cost: 18–35k tokens including test author/review, 0.5–2 GPU-hours. No per-build review loop or new tests agent for each repair.

### 7. Evaluate: three independent verdicts

- In: frozen controls/method/tests/seal. Trusted evaluator script, not method author, writes `O/eval/{validity.json,equivalence.json,performance.json,curve.json,raw.jsonl}` with distinct scorers and immutable input hashes.
- Validity reruns all anchors under method configuration against published results. Equivalence pairs baseline/method outputs on sealed held-out inputs with exact alignment/counts; applies sealed deterministic bounds or powered statistical equivalence tests, including stochastic paired seeds.
- Performance reruns published configuration and tuned control; same data, precision, outcome and timing scope. Randomise paired order, warm caches equally, synchronise GPUs, include launch/transfer/merge overhead, report spread and sealed confidence intervals.
- Compare on identical allocated resources where possible; otherwise match total USD budget using measured instance tariffs and report latency plus cost ratio. Report `speedup=T_published/T_method` only at matched outcome and no higher cost; more GPUs alone cannot establish a gain. Repeat against tuned control.
- Measure outcome at every sealed compute budget for all three arms; record allocated GPU-hours and USD, uncertainty, failures, and unachieved targets. Do not extrapolate an unmeasured curve or retune against evaluation results.
- Facts: `validity_pass`, `equivalence_pass`, `performance_pass`, `equal_cost` flags; `speedup_published`, `speedup_tuned`, `cost_ratio`, `prediction_ratio` (published speedup/sealed expectation) ratios; `curve_points` count. Gate: all three checks pass; performance meets sealed gain/confidence rules against both controls. Missing measurements are VOID, never PASS.
- Failed validity exits 4; failed equivalence/performance exits 5. Preserve separate verdicts: performance cannot repair invalidity. Continue only safe diagnostics permitted by seal; compute/infra failures retain exit 3/2 and partial results.
- Cost: 0 tokens normally, 8–32 GPU-hours; comparisons/scorers/curve fitting are scripts. Failure still proceeds to takeaways.

### 8. Takeaways and close

- In: operator path reads only validated `S/signatures.jsonl`; research path reads private seal/results. Reuse `measure/operator_takeaway.py` with a signatures-input adapter and fixed m5 columns, not a model call or recursive content scan.
- Out: `S/OPERATOR_TAKEAWAY.md` (gates, blockers, vote share, verdicts, spend, realised/predicted ratios where safely available); `A/RESEARCH_TAKEAWAY.md` (one call, optionally a second skeptic, explaining outcome and limits against sealed predictions).
- Facts: `operator_written`, `research_written`, `teardown_confirmed` flags. Gate: schema/leak check and confirmed box termination; skipped/failed stages still yield both takeaways with unavailable claims marked. Close-record verdict concerns completion, not scientific success.
- Cost: 3–6k tokens, 0 workload GPU-hours. Charge serving/idle/teardown time through confirmed termination; repeated teardown polling remains script-owned.

## Implementation units, in order

Each unit is its own build/test/commit: a separate test agent sees its contract and public fixtures, never implementation; operator reruns tests, inspects pipeline diffs, and performs the stated live check before commit. Private scientific diffs remain outside operator view.

1. Add v2 envelope validator/emitter and explicit manifests; test malformed fields, plausible-ID secret sentinels, missing telemetry, atomic failure records, v1 compatibility.
2. Add m5 model-policy config, disabled-family validation, and quota fail-fast handling; test private Codex is allowed, Claude is blocked on every override/fallback/repair/panel/resume path, and narrow/long chains resolve correctly; make one harmless live allowed-model call.
3. Add explicit m5 stage/run-root support to `launch.js` and bounded `m5/pipeline.js` prompts; stub stage transitions/early stops and verify no experiment/default-path dependency.
4. Add dev lifecycle adapter with receipts and allocation billing; replay partial fetch, idle stop, and mode changes; live stock-box up/command/down.
5. Add ONBOX wrapper/guard adapter; replay time/price changes, capabilities, SSH loss, partial outputs, every exit trap and injectable command; live detached dry run.
6. Add intake extraction contract and bounded search; fixture brief/not-found/licence/data cases, verify exactly one intake envelope and no content in operator files.
7. Add reproduction/control runner and tuner packet; recorded real fixtures test anchor scoring, representative scale, immutable baseline and hard anchor stop.
8. Add profiler summarisation; replay overlapping CPU/GPU events, missing counters and coverage gaps; live baseline trace with critical-path reconciliation.
9. Add seal writer/verifier; test canonical hashes, ordering before build, tampering, baseline/protocol changes, and preservation of previous seals.
10. Add proposal/vote aggregation; stub five ballots, abstentions, failures, menu rejection and threshold boundaries; live one narrow Lambda vote.
11. Add restricted method/test views and single review/repair orchestration; sentinel access tests verify neither author can read the other's code or transcripts; live public smoke.
12. Add independent validity/equivalence scorers; fixtures catch wrong pairing, dropped rows, false equivalence, and anchor failure without conflating verdicts.
13. Add performance/curve script; replay unequal cost, noisy timing, missing targets and false speedup claims; live public paired timing.
14. Add signature-input takeaway adapter and close path; replay double-counting, failure exits, missing stages, research-call bounds and termination billing.
15. Add public shakedown manifest and integration fixtures; run all stages plus injected failures below before private intake is enabled.

## Public shakedown before private content

These are proposed stock-CUDA-image workloads, not claimed measured timings. Pin commits/toolchains, confirm source licences in intake, and run stage 2 before accepting either. Generated inputs avoid private/external data dependencies.

- **CFD: NPB-GPU BT**, Class S anchor, then W/A for representative timing. Known class-specific residual/error verification; batch independent solver inputs or pipeline transfers, retaining each class's numerical protocol. GCC/make/nvcc, no dataset download; native `timer.flag` supports profiling. Estimated full shakedown: 1–3 GPU-hours. [GPU implementation/build instructions](https://github.com/GMAP/NPB-GPU), [CFD benchmark origin](https://github.com/LLNL/NPB).
- **Computational finance: NVIDIA MonteCarloMultiGPU**, generated European options; analytic Black–Scholes reference and upstream average-reserve >1.0 check. Start published one-GPU configuration (8,192 options, 262,144 paths), batch independent option sets; use fixed strong-scaling inputs for multi-GPU comparisons and error-vs-path-count for outcome/compute. Stock CUDA/cuRAND/CMake; estimated 1–3 GPU-hours. Upstream sample timings are not a performance standard: m5 measures its own end-to-end protocol. [Source/reference checks and workload constants](https://github.com/NVIDIA/cuda-samples/blob/master/cpp/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp).

Select one, run all eight stages under USD 100, and permit full operator inspection of this public run. Inject anchor, seal, privacy-sentinel and cost-guard failures; verify stop records, independent verdicts, both takeaways and teardown. Private intake unlocks only after these checks pass; its content remains inaccessible to the operator.

m5 does not need card/question-tree generation, directive regeneration/gate addenda, per-build reviews, repeated tests authors, open-ended ask/fixer agents, exhaustive redesign/build loops, a 39-call post, or m4 ledger/post machinery. Keep one gate, one launch review, upstream tests plus missing contract tests, and one or two research takeaway calls.

## Lean cut (operator, 2026-10-26): build these 7 units, not the 15 above
Agents for m5 v1: Codex only (allowed for private content), with OpenCode Go as fallback. Lambda narrow calls are deferred, because the serve box and the dev box cannot coexist under one state file. No Claude.
1. DONE 2026-10-26. Runtime guard: `understudy.disabled_families` and the `--disable-family` flag; quota errors skip the repair turn; a run whose families are all disabled exits 2. Codex implemented; tools/test_disabled_families.js by a separate agent; all suites pass.
2. Signatures v2 (`facts` per stage, fixed keys) and the operator-takeaway adapter.
3. `m5/pipeline.js` skeleton with an explicit run root (`launch.js` support), stub stages, early stops, and SKIPPED records.
4. A dev-box stage runner: run a declared command detached on the dev box under a timeout, fetch its outputs to `A/`, and write a receipt (reusing `box.sh`; no new lifecycle layer).
5. Intake, reproduce, profile and seal. The harness scripts per benchmark are written by Codex agents, with an independent test author.
6. Propose with 5 Codex votes, implement with a separate test author, then evaluate (validity, equivalence, performance) with scorer scripts.
7. Shakedown on MonteCarloMultiGPU (analytic reference; simplest), fix what breaks, then the private run.
Dropped for v1: separate ONBOX and dev-lifecycle adapters, allocation billing (lambda_serve.sh status gives USD), Lambda model roles.
