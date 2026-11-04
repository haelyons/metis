# s29 assessment: run8's fetch failure, run7's evaluator hangs, and the revised fixture run (2026-11-04)

**Scope.** Offline step: no network, no box, no git, no credentials. I wrote only into `science/s29/`.
- **Read:** s28 (assessment, design, brief section, predictions), s27 (`TOLERANCE_RULE.md`, assessment §E), `m5/run8/` (args, harness, receipts, stage records, operator takeaway, setup log), the two reader reports `m5/run7_failcause/REPORT.md` and `m5/run8_fetchfail/REPORT.md`, `dut/pipeline/m5/SCHEMAS.md:115-203` and `dut/pipeline/m5/pipeline.js` (harness prompt, upload list, repair restore). For s01 to s26 I relied on the summaries that s27 and s28 carry, as s28 did; I did not reread them in this step.
- **Tool limits.** Bash was allowed for a few reads and then denied, including for writing files. I wrote every file with the file tool. I checked byte equality once, before the denial: `m5/b01_materials/BRIEF_run1.md`'s first 1,714 bytes equal `m5/BRIEF.md`, and s28's brief begins with all 39,538 bytes of `BRIEF_run1.md`. `FIXTURE_BRIEF.md` here was retyped from the read text, so I could not hash it. **The operator should verify, before sealing, that `FIXTURE_BRIEF.md` = `BRIEF_run1.md` (39,538 bytes) followed by `_section.md`.** `_section.md` holds only the brief's new section and exists for that check; it holds no design content. A heading/apostrophe count matches: 17 occurrences of `^## |’` in `BRIEF_run1.md`, 18 in `FIXTURE_BRIEF.md` (the one added heading).

**Verdict.**
- **run8:** the sealed `fetch_private.sh` read a harness data file that the pipeline never uploads.
- **run7:** the evaluator ran from standard input, which hung PINDER's spawn pool.
- Both are harness-script defects. The brief and design let them happen.
- **Next:** a revised fixture rerun (m5) that keeps s28's run and adds a self-containment rule. s27's tolerance rule stays unchanged.

## A. Why run8 failed and why run7's invocations failed

### run8: `fetch_private.sh` exited 1 before any invocation

**What happened, from the records:**
- `control/receipts/0012-comparison-users.json` has `rc` 1 and `wall_s` 32. Its whole log is `comparison users: fetch_private.sh exited 1` (run8_fetchfail §A).
- `control/stages/evaluate.json:1`: FAIL, `infra`, `wall_s` 42.4.
- The script's output was discarded by design (`cmp_users.sh:126-128`, per the reader). So the traceback is inferred from the code, not read from a log.

**The script and why it failed.** `run8/agent/harness/fetch_private.sh`:
- line 4 resolves its own directory, `harness/`;
- line 5 runs `python3 - "$script_dir/inputs.json"`;
- line 9 reads that file first: `json.loads(Path(sys.argv[1]).read_text())`.

`harness/inputs.json` never reaches the box:
- The upload list is fixed: `setup.sh`, `run_anchors.sh`, `run_command.sh`, the optional `run_evaluation.sh`/`run_units.sh`/`units.json` (`pipeline.js:834-836`), and `comparisonFiles()` (`pipeline.js:342-343`), which returns `arms/*.sh`, `cmp_files.json`, `cmp_extract.json`, `versions.sh`, `fetch_private.sh` and `evaluate.sh`.
- `FileNotFoundError` under `set -e` gives rc 1.

**The same defect was waiting in the evaluator:**
- `run8/agent/harness/evaluate.sh:8` executes `harness/evaluate_dockq.py`, which is not uploaded.
- `evaluate_dockq.py:16` reads `inputs.json`.

**The same pattern appeared twice in setup, but repairs could fix those:**
- setup rc 2: `prepare_inputs.py` missing (`0004-setup.log:267`);
- setup rc 1: `published.json` missing (`0006-setup.log:32`).
- The repairs inlined the data (`setup.sh:80`: "Keep setup self-contained: auxiliary harness files may not be staged").
- Sealed comparison files are never repaired (`SCHEMAS.md:157`; `pipeline.js:789`), so this one stopped the run.

**What let it happen:**
1. **s28's brief, `s28/FIXTURE_BRIEF.md:349`,** told the harness agent to keep the evaluator's Python "as a regular file in `harness/` (for example `harness/evaluate_dockq.py`, uploaded with the harness)". That premise is false for any file outside the upload list. It invited exactly the multi-file layout run8 used, and the data file `inputs.json` came with it.
2. **s28's design text** said the same in the view: `evaluator.spec.invocation`, "a regular file kept in the harness" (`s28/fixture_design.json`, evaluator spec).
3. **The harness agent's instructions:**
   - `pipeline.js:774` asks for "three self-contained bash scripts" (setup, anchors, command).
   - The comparison files at `pipeline.js:783-789`, and `SCHEMAS.md:150-156`, are not called self-contained. Nor does any text tell the agent which harness files reach the box.
   - `fetch_private.sh` is told to fetch "every input data.json marks", but `data.json` is an intake file that is not on the box either.
4. **The pipeline itself** seals and uploads the named files without checking what they reference. The failure therefore first appears on the box (reader's hardening note, run8_fetchfail §B).

**What was not the cause** (run8_fetchfail §A-C):
- the seal check (step 1 passed);
- permissions or network;
- the private-data source (URLs, bytes and SHA-256 match run7's);
- the mechanism;
- the repairs (they touched only `setup.sh`).

**s28's other correction did work.**
- `run8/agent/harness/setup.sh:59,72` reads `compute_cap` and checks with `cuobjdump`.
- `0008-setup.log:24-25` lists `sm_90` cubins on the H100.
- run8's evaluator code also used `parallel_io=False` (`evaluate_dockq.py`, `BiotiteDockQ(... parallel_io=False)`).

### run7: every evaluator part hung to its cap

**The cause** (run7_failcause §A):
- `run7/agent/harness/evaluate.sh:11` ran the evaluator as `"$VPY" - <<'PY'`.
- `evaluate.sh:30-32` left `BiotiteDockQ` at its default `parallel_io=True` (`pinder/eval/dockq/biotite_dockq.py:226`).
- The parallel reader uses a `spawn` pool (`pinder/core/utils/process.py:17,33`). Each worker re-imports `__main__` from `/tmp/m5-…/<stdin>` and dies with `FileNotFoundError` (`w1/*/eval/evaluator.log:1-15`, repeated 492,963 to 842,748 times per log).

**The cost:**
- All 13 executed invocations (warmup round) hit the 900 s evaluator cap (`run7/control/comparison.json:385`); invocation 13 was cut at 665.8 s.
- `budget_s` 12,600 was spent and 99 of 112 invocations were `not_run` (`comparison_compute.json:3-171` against `172-1458`).
- Every arm command exited 0 in 1.2 to 39 s.

**What let it happen:**
- s27's brief and design said nothing about how to invoke the evaluator.
- The harness prompt does not either.
- The contract runs no evaluator before evaluate in comparison mode (`SCHEMAS.md:159`: reproduce runs only A0's anchors).
- There is no early stop on repeated evaluator timeouts (`SCHEMAS.md:181`).

So the first evaluator call happened inside the paid comparison, and each hang cost the full cap.

## B. The revised fixture run

**What I change, in the run's own terms.**

*Brief* (`FIXTURE_BRIEF.md`, section `## Comparison request (science step s29)`):
1. **A new subsection, "Which harness files reach the box (correction)".**
   - It lists exactly the files the pipeline uploads (as `pipeline.js:342-343,834-836` define them).
   - It says that any other file under `harness/` never reaches the box, and that sealed comparison files are never repaired.
2. **Every uploaded script is self-contained.** It reads no file under `harness/` except itself, and carries its data and program in its own text or takes them from the pipeline's `CMP_*` variables. No other file is written under `harness/`.
3. **`fetch_private.sh`** carries, for each of the four inputs, the native complex's name, URL, byte count and SHA-256 as `spec.reference` gives them in the view. It checks each download against them. (run7's script had this form and passed.)
4. **`evaluate.sh`:**
   - It takes the reference's name, bytes and SHA-256 from `CMP_INPUT_SPEC`.
   - It carries the Python program in its own text, writes it to a regular file under `CMP_EVAL_OUT` at each call, and runs `"$VPY" <that file>`. It never uses standard input and never uses a file under `harness/`.
   - `parallel_io=False` is kept.
   - This replaces s28's line 349, whose "uploaded with the harness" was false.
5. **`setup.sh` checks that the evaluator's interpreter imports `BiotiteDockQ`** (no private data, no scoring) and stops setup otherwise. Today this is the only evaluator check possible before evaluate within the contract. It catches install defects before box time is spent on invocations. It cannot catch a defect in `evaluate.sh` itself.
6. `setup.sh` carries the fixture URLs, bytes, SHA-256 values and prepared paths in its own text. That is what its repairs converged on in run8.

*Design* (`fixture_design.json`, exact schema of `SCHEMAS.md:117-141`):
- `evaluator.spec.private_data`, `reads` and `invocation` are reworded to the self-contained form above.
- `order_seed` is 29291 and `bootstrap_seed` is 29292.
- Everything else equals s28's design byte for byte in content: arms, commands, env, inputs, outputs (`name`, `format`, `select`), metrics, comparisons, `replicates` 6, `warmup` 0, `timeout_s` 300, `evaluator.timeout_s` 180, `budget_s` 16200.
- The view text (`what`, `spec`, `select`, `commands`, `env`) states no margin, threshold, confidence, reference value, expected result or tolerance rule. The only numbers in the view are the published sources' byte counts and hashes and the program's arguments, as in s27 and s28.

**Kept from s28:**
- the GPU build for the box's own compute capability, with the `cuobjdump` stop (it worked in run8);
- `parallel_io=False` and no standard-input program;
- `warmup` 0;
- the caps and budget;
- every boundary.

**Tolerance rule.**
- **s27's rule governs, unchanged.** I seal no new rule. The arms, outputs, comparisons and F-K ids are unchanged, and the rule reads replicate pairs only. So it applies to this run verbatim, as s28 established for its run.
- One consequence for the main run: rule §3 step 2 requires the main design to reuse "the evaluator `spec`, apart from the private data's source" byte for byte. The main design must therefore copy this design's `spec` (with only `private_data` and the reference names changed).

**Does the change address both causes?** Yes.
- run7's cause (standard-input program with `parallel_io=True`) was addressed by s28 and is kept. run8 shows the agent followed it.
- run8's cause (non-uploaded helper files) is addressed now, in both the brief and the view.

**Residual risks:**
- Nothing in the pipeline enforces self-containment before the box.
- The evaluator's program has never run to completion on this route.

## C. s28's predictions scored (`outcomes.json`)

**Evidence from run8:**
- `control/stages/evaluate.json:1`: FAIL, `wall_s` 42.44.
- reproduce PASS (operator takeaway line 8).
- No invocation ran.
- Neither `control/comparison_scored.json` (S) nor `agent/results/evaluate/comparison_compute.json` (Y) exists. The run8 file listing has no such files.

I applied s28's own resolution conventions (`s28/PREDICTIONS.md`): null when the file is absent for a reason other than the predicted outcome, or when a "every present …" statement has none present.

| id | outcome | evidence |
|---|---|---|
| Q1 | false | evaluate FAIL; S not written |
| Q2 | null | no invocation exists, so no `ok` invocation (vacuous) |
| Q3 | false | none of the 96 scheduled invocations ran; Y absent because evaluate failed before invocations |
| Q4 | false | S absent; no present pair, so Z cannot hold (s27 rule: V0 fails) |
| Q5 | null | no present pair |
| Q6 | null | no present pair |
| Q7 | null | no present pair |
| Q8 | null | no present pair |
| Q9 | false | V0 fails, so M3 is indefensible (`fixture_run_failed`) |
| Q10 | false | M2 indefensible, same reason |
| Q11 | false | M4 indefensible, same reason |
| Q12 | false | none of M2 to M4 is defensible |
| Q13 | null | Y absent for a reason unrelated to cost. For information only, not as resolution: the operator reports run box USD 0.73 |
| Q14 | null | Y absent. For information only: the operator metadata names `gpu_1x_h100_pcie` |
| Q15 | null | no `ok` evaluator invocation |
| Q16 | true | evaluate `wall_s` 42.44 ≤ 14,400 |
| Q17 | null | no present F-K4 pair |

**Resolved: 8 of 17** (1 true, 7 false). Unresolved: 9.

## D. The next test: the revised fixture rerun (m5)

**Why.**
- The margins still have no fixture data. Without them the main comparison can claim no tolerance (s27 rule §3 step 3).
- Both failures were harness-script defects that the brief and design can prevent within the existing contract, so this is not a `contract_gap`.
- The run is cheap and under the USD 20 rule.

**Weaknesses I record but that do not block:**
- `SCHEMAS.md:157` / `pipeline.js:342-343,783-789` neither require nor check that sealed comparison files reference only uploaded files.
- `SCHEMAS.md:159-181` has no evaluator smoke test before the first invocation and no early stop on repeated evaluator timeouts.
- `SCHEMAS.md:166` (step 5) discards `fetch_private.sh`'s output, so a fetch failure is diagnosed only by inference.

These are hardening items for the owner, not preconditions.

**Sizing, from measured costs.** I take run7's comparison receipts of about 960 s apart (s28 §A table and run7_failcause §C):
- **evaluator part:** about 901 s, a hang at the cap;
- **arm part:** 1.6 to 39 s;
- **fixed cost outside the parts:** about 40 to 49 s of wrapper overhead plus a 23 to 31 s `comparison-job` receipt, so 63 to 80 s.

The 960 s is therefore not the cost of a working invocation. Per invocation:

| case | fixed | arm (mean) | evaluator | per invocation | 96 invocations |
|---|---|---|---|---|---|
| expected | 72 | 10 | 10 | 92 s | 8,830 s |
| pessimistic | 80 | 16 | 30 | 126 s | 12,100 s |
| evaluator hangs again (cap 180) | 80 | 16 | 181 | 277 s | budget-bound: about 58 run in 16,200 s |
| run7 as measured (cap 900) | — | — | — | about 960 s | about 17 run in 16,200 s |

**Settings:**
- **`budget_s` 16,200** (4.5 h) holds all 96 invocations in the pessimistic case, with 1.34× headroom, plus about 93 s of users and versions.
- With `replicates` 6, rounds run in order. Z needs only 4 present pairs per fixture, so Z can still hold if the budget ends after round 4 (64 invocations ≈ 8,100 s even at the pessimistic rate).
- **`timeout_s` 300** is about 7.7× the largest arm wall measured (39 s on the A10).
- **`evaluator.timeout_s` 180** is about 70× run4's evaluator wall. It caps a repeat hang at about 280 s per invocation, against run7's 960 s.
- **`warmup` 0:** run7's warmup bought nothing for exact-agreement outputs.

**One allocation inside the 6 h limit:**
- Pre-evaluate time is about 0.35 h: run7 took 18:10:08 to its users receipt at 18:28:56; run8's intake + reproduce took 759 s.
- Post-evaluate time is about 0.05 h.
- `args.run_ceiling_s` 19,800 exceeds `budget_s` + pre-evaluate time (16,200 + 1,260 = 17,460 s).

| case | hours | A10 (USD 1.29/h) | H100 (USD 3.29/h) |
|---|---|---|---|
| expected | 0.35 + 2.48 + 0.05 ≈ 2.9 | 3.7 | 9.5 |
| pessimistic | 0.35 + 3.39 + 0.05 ≈ 3.8 | 4.9 | 12.5 |
| worst (budget exhausted) | 0.35 + 4.5 + 0.05 ≈ 4.9 | 6.3 | 16.1 |

- **On an A10:** the arm walls were measured on that box (run7).
- **On an H100:** the arm walls are similar or shorter (run6 CPU walls 9.0 to 14.5 s on seed cases, per s28), and the fixed cost is wrapper/SSH time that does not depend on the box.
- Both boxes stay under 6 h and under USD 20 in the worst case.
- **Projection:** about 2.9 h expected, 3.8 to 4.9 h at most, and USD 3.7 to 16.1 depending on box. On run8's H100 it is USD 9.5 to 16.1.

**What each result decides** (as sealed in s27 §E and s28 §D, unchanged):
- **M2 to M4 defensible:** the next step writes the main agreement design, with the margins per rule §3.
- **G_T true:** `needs_owner` on the exact transform gate.
- **Some margin indefensible:** `needs_owner` on whether dependent comparisons proceed.
- **V0 or Z fails again, from a harness defect in a sealed file despite this brief:** I would count that as evidence of a contract gap. The instruction alone is then demonstrably insufficient, and the gap is that `SCHEMAS.md` "Sealed comparison" has no pre-upload check of what the sealed files reference and no evaluator check before evaluate. The next step should then stop with `contract_gap`, or use `args.harness_from` with a vetted harness, rather than retry blind.

**Box identity for the main run:**
- Rule §3 step 4 makes margins not applicable when the GPU name, driver or executables differ from the fixture run's.
- With a per-box build target, the main run must land on the same GPU type as this run.
- Whether to pin it is the owner's decision before the main run (raised in s28 §D, still open). It does not block this step.

## E. Do the main runs fit the USD 91.62 left after the next step?

- **After this run, worst case:** 91.62 − 16.1 = **USD 75.52**. The expected case on an H100 leaves 82.1.
- **Main agreement run** (A0 and A1 on the four seed cases, 6 replicates, 48 invocations): 48 × ~95 s ≈ 1.3 h + 0.4 h ≈ 1.7 h, or about **USD 5.6** on an H100.
- **Physical card's planned study:** **USD 49.48** (`s13/ASSESSMENT.md:86`, as quoted in s27 §E and s28 §E).
- **Left:** 75.52 − 5.6 − 49.48 = **USD 20.44**. So **yes**.
- **Caveats:**
  - run7 measured about 70 s of fixed cost per invocation. If the card's plan assumed less, each 100 extra invocations add about 1.2 h, or about USD 4.1 on an H100.
  - One more failed fixture run at worst case (USD 16.1) would leave about USD 4.3 of reserve after both main runs. A second repeat failure would therefore also bear on `limits`.

## F. Narrowing

Unchanged: no narrowing (`NARROWING.md`).

## Predictions

19 predictions for the rerun are written in `PREDICTIONS.md` and `predictions.json`. The operator seals them by committing before launch.
