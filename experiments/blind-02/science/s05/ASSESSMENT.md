# s05 assessment — 2026-11-03

**Scope of this step.** This was an offline review of the records only. I used no network, contacted no box, ran no git commands and read no credentials. I wrote only into s05. I read s01–s04 before run5; for s01–s03 I relied mainly on s04's consolidated record.

**Abbreviations.** Paths are relative to the repository root.
- **R5** = `experiments/blind-02/m5/run5`
- **R4** = `experiments/blind-02/m5/run4`
- **R3** = `experiments/blind-02/m5/run3`
- **S4** = `experiments/blind-02/science/s04`
- **D** = `dut/pipeline`

## 0. Why intake failed: `intake_failure_cause = no_file_access`

**Classification.** This was not a refusal and not a decline. The understudy model was never able to open the brief. The cause is a defect in the pipeline.

**What the evidence shows:**

1. **Codex hit its usage limit, so the call went to the understudy.** The Codex primary failed within about 1 s of starting. The error was `"runner error: usage limit"` with "try again at Nov 7th, 2026 11:30 PM" (`R5/agent/wf/agents/0001-intake/meta.json:17–21`; `codex-1.jsonl:15–16`). The workflow then handed the call to `claude/opus` with `"kind":"runner"` (`R5/agent/wf/journal.jsonl:3`).

2. **The understudy tried to read the brief and was denied.** Its transcript records exactly one permission denial: `"permission_denials":[{"tool_name":"Read", ... "file_path":"/home/hal/dev/interp/metis/experiments/blind-02/science/s04/CALIBRATION_BRIEF.md"}]` (`R5/agent/wf/agents/0001-intake/understudy/claude-1.json:1`).
   - Other fields in the same record: `"is_error":false`, `"subtype":"success"`, `"num_turns":3`.
   - The workflow logged `refusals 0` (`R5/agent/wf/UNDERSTUDY.md:9`) and `"kind": "none"` (`understudy/meta.json:18`).

3. **The agent then reported the restriction accurately rather than refusing.** It wrote all five intake files, each giving the same reason: "Brief … could not be read: file tools are restricted to the agent working directory; restriction not circumvented. No benchmark extracted or substituted." (`R5/agent/intake/benchmark.json:3`, `data.json:3`, `EXECUTION.json:2–6`).
   - It returned `found:false, data:"unknown", licence_basis:"unreachable"` (`understudy/reply.txt:1`).
   - That is what the intake prompt instructs when a brief cannot be read: "if unreadable or unsupported, report found=false" (`R5/agent/wf/agents/0001-intake/prompt.md:2`).

4. **The low input-token count does not mean the prompt went unread.** The "6 input tokens" figure counts uncached tokens only. The same record shows `cache_creation_input_tokens 6416` and `cache_read_input_tokens 24884` (`claude-1.json:1`), so the prompt reached the model. The agent did not read the *materials* because the Read was denied, not because it skipped them.

**Why the Read was denied.** These are the file references for the mechanism:

- The Claude runner runs with `--restricted` and `--permission-mode dontAsk`. The comment says "file tools confined to the working directories". Directories are added only through `--add-dir` (`D/idea/claude_cli.js:15–21`).
- The workflow passes `addDirs: [ARGS.base, ARGS.cwd, ...ARGS.add_dirs]` (`D/idea/wf.js:128`). For run5 these are `base = R5/agent/wf/work` and `cwd = R5/agent`; no `add_dirs` were set (`R5/agent/wf/run.json:16–18`).
- The brief path is `experiments/blind-02/science/s04/CALIBRATION_BRIEF.md` (`R5/args.json:3`). That is outside both directories.
- The m5 intake prompt names the brief by its absolute path. It neither copies the brief into the run nor adds its directory (`D/m5/pipeline.js:85–92`).
- The prompt's own line "Never read experiments/" (`pipeline.js:92`) also conflicts with a brief stored under `experiments/`.

**Comparison with run4 (Codex, a brief of the same kind and location).**

- R4's brief was `experiments/blind-02/science/s03/CALIBRATION_BRIEF.md` (`R4/args.json:3`), with the same prompt text (`R4/agent/wf/agents/0001-intake/prompt.md:2–3`).
- Codex ran for 121,381 ms with 8 tool calls and 360,753 input tokens (`R4/.../0001-intake/meta.json:7–16`).
- It copied the brief to `R4/agent/intake/brief.md`, which exists, and intake passed.
- Codex's sandbox (`workspaceWrite`) limits only *writes*, to `wf/work` (`R5/.../codex-1.jsonl:3`, `"sandbox":{"type":"workspaceWrite","writableRoots":[…/agent/wf/work]}`). Reads are not limited.
- Run3 (also Codex) read its s02 brief from the same kind of location.

**The defect.** Briefs outside the run root are readable by the Codex primary but not by its Claude understudy. Yet `D/m5/SCHEMAS.md:12–13` states that `claude/opus` covers Codex authors when Codex fails ("Opus covers Codex authors when Codex fails"). For a brief stored outside the run, that coverage cannot work.

**Sealed rule applied.** The reply was not a refusal or decline, so the refusal branch does not apply. The cause is a pipeline defect, so I name it as a contract gap (gap 7, section E).

**Can an existing mechanism avoid it?** I checked three options; none works within this route:
- `ARGS.add_dirs` (`wf.js:128`) would avoid it, but it is not among the m5 flags this step may request.
- A brief written in my own step folder is also outside the run root, so it would fail the same way.
- Waiting for Codex to come back (after 2026-11-07 23:30 UTC) would avoid the understudy path. But `NEXT.json` cannot express a deferred launch, and an understudy hand-off at intake would fail again the same way.

So I stop with `contract_gap`.

## A. What the run did instead, and why

**What s04 asked for.** A timing-only calibration of all three configurations (CPU standard, GPU standard, GPU dense) across the four cases: one warmup block plus three retained blocks, no native access. It was to report the production wall W, the docking process wall D, the printed Elapsed P and the reconstruction wall R per job, plus a GPU-telemetry block (S4 D; `S4/CALIBRATION_BRIEF.md`).

**What happened.** None of this ran.

- Intake FAILED after 14.85 s (`R5/control/stages/intake.json:1`, `"blockers":["data_unavailable"]`).
- Reproduce, profile, seal, propose, implement and evaluate were all SKIPPED (`R5/pipeline.log:1–8`).
- No harness was authored and no box command ran. `agent/harness/` and `agent/results/` do not exist in R5.
- A box was allocated: `gpu_1x_h100_pcie`, us-west-3, USD 3.29/h, started 03:22:19Z (`R5/control/box.json:1`). It stayed idle.

**Why.** Intake could not read the brief (section 0), so it reported the benchmark as not found and the data availability as unknown. The pipeline's gate maps `data:"unknown"` to `data_unavailable` (`D/m5/pipeline.js:79`). Intake and the harness therefore never interpreted the request at all.

**Measured values.** There is no measured value, unit, spread, configuration or case.

## B. What it supports and what it does not

**Supports:** only an operational finding. When Codex is unavailable, m5 intake cannot read a brief stored outside the run root.

**Does not support** anything about MEGADOCK's runtime, the dense-to-standard ratio rho, the padding check, acceleration, agreement or quality. Run5 is recorded as a **failed intake and an uninformative calibration**.

**Card comparison.** I cannot compare against the card's GUESS or refutation band: nothing was measured.
- The CPU-standard evaluator value from run4 (2.573 s against `eval_runtime_s` = 60 GUESS, band [20, 180]) is unchanged.
- The production-wall inputs that s04 targeted remain unmeasured.

**s04 predictions** (definitions in `S4/PREDICTIONS.md:22–35`; also in `outcomes.json`):

| ID | p | Outcome | Evidence |
|---|---:|---|---|
| Q1 | 0.85 | **false** | Intake completed with FAIL and `data:"unknown"`. The rule says "False if intake completes with FAIL or another data value". I applied it literally, even though the cause was infrastructure. |
| Q2 | 0.75 | null | `out/timing_calibration.json` is missing ("Null if the file is missing"). |
| Q3 | 0.85 | null | No GPU-arm logs and no anchors receipt exist. |
| Q4–Q11 | — | null | No job records exist; every input is missing. |
| Q12 | 0.85 | **true** | The takeaway's Totals usd is 0.014070233333333333 ≤ 5.00 (`R5/operator/OPERATOR_TAKEAWAY.md:24`). It is true only because nothing ran. |

## C. Candidates against s04's decision rule

s04's rule says: "An incomplete calibration means unknown. No reruns beyond the schedule." (S4 D). Every quantity the rule depends on (rho, the padding check, the acceleration ratio) is therefore **unknown**, and no rule branch fires.

- **Kept (two):**
  - **C2** (`seed:idea:2`), provisionally.
  - **The physical branch** (`R1:physical:P1`).
  - Both are in the same state as after s04.
- **Dropped:** none.
- **Unchanged:** C1 and C3 stay REJECT, I2 stays halted, and C4 stays a reserve diagnostic.

## D. Next test

**Stop with `contract_gap`.**

**Why not relaunch.** The single most informative next measurement is still s04's timing calibration. s04 projected about USD 4 all-in, with a hard stop at USD 10 or 2 h. Its outcomes decide which physical tiers dense may enter, and whether C2's affordability and acceleration components survive.

That calibration is ready and unchanged. But launching it now through m5 would route intake to the Claude understudy again: Codex stays at its usage limit until 2026-11-07 23:30 UTC. It would fail the same way and still pay for an idle box: run5's allocation ran from 03:22:19Z to the workflow's end at 03:33:23.893Z (`R5/agent/wf/run.json:321`), 664.9 s, about USD 0.61. No flag available to this step changes the understudy's readable directories, and no location I can write to is inside them.

**What would unblock it.** Either of these:
- (a) Close gap 7 (smallest change in E).
- (b) Have the operator or owner relaunch the unchanged s04 brief after Codex's limit resets. Run4 shows Codex reads such a brief.

Either way, the relaunch needs fresh sealed predictions from the step that requests it (`PREDICTIONS.md`).

**Calibration runs so far.** Two USD figures are given for each run:
- **Stage-wall:** the operator total, computed as receipt and stage walls × 3.29/h.
- **Allocation span:** from box start to the end of the workflow or the last receipt, × 3.29/h, before termination lag.

No invoice is on record for any of them.

| Run | Step | Result | Stage-wall USD | Allocation span |
|---|---|---|---:|---|
| run3 | s02 | intake FAIL (Codex; historical evidence not in brief) | 0.131 (`R3/operator/OPERATOR_TAKEAWAY.md:24`) | 01:59:51Z → 02:09:13.7Z = 562.7 s ≈ 0.51 |
| run4 | s03 | reproduce PASS; evaluator max 2.573 s | 0.810 | ≈ 1.28 (S4 A) |
| run5 | s04 | intake FAIL (Claude understudy; no file access) | 0.014 | 664.9 s ≈ 0.61 |

Totals: about USD 0.96 stage-wall and about USD 2.40 allocation span. That is far below the pilot cap. Model cost for run5's understudy was USD 0.0797 at list price (`understudy/meta.json:8`).

## E. Contract gaps (final list for the owner)

Gaps 1–6 are carried over from `S4/ASSESSMENT.md:150–179`, unchanged.

1. **m5 cannot express named-arm ordered comparisons.**
   - Where: `D/m5/SCHEMAS.md` (PREDICTIONS, Propose, Evaluate); `D/m5/pipeline.js:1037–1038`.
   - Blocks: the final comparison.
   - Fix: an optional named-arm comparison mode with sealed agreement and quality metrics.
2. **The handoff from tree PLAN to measure loses arms and decision rules.**
   - Where: `D/CONTRACT.md` §2.5 and §5; `D/src/main.js:468–478`; `D/launch.js:71–96`.
   - Blocks: calibration on the measure route, and the final experiment.
   - Fix: an immutable handoff of the full PLAN.
3. **The measure route has no execution controller.**
   - Where: `D/launch.js:45–47, 83–107, 141–153`.
   - Blocks: calibration on that route.
   - Fix: a validated chain of stage arguments.
4. **The cost queue cannot represent scientific readiness (tolerances).**
   - Where: `D/src/cost.js:154–163`; `D/CONTRACT.md` §5.
   - Blocks: moving from calibration to the agreement and quality study.
   - Fix: typed required-evidence records.
5. **There is no route for authorised local evidence.**
   - Where: `D/src/prompts.js:107–110`, `D/src/gates.js`, `D/m5/pipeline.js:89–108`.
   - Blocks: reproducible calibration identity across steps.
   - Fix: a hashed, owner-authorised evidence bundle.
6. **Cost accounting uses stage walls, not allocation span.**
   - Where: `D/m5/pipeline.js:1007–1008`.
   - Blocks: billed-cost reporting in the final experiment. Run5 adds a fresh example: stage-wall USD 0.014 against an allocation span of about USD 0.61.
   - Fix: report the allocation span and the invoice.
7. **New: the m5 intake understudy cannot read a brief outside the run root.**
   - Where:
     - `D/m5/pipeline.js:85–92` (intake prompt: the brief is passed by absolute path and never staged into the run; "Never read experiments/" contradicts the brief's location);
     - `D/idea/wf.js:128` (the Claude understudy gets `addDirs` = base, cwd and `add_dirs` only);
     - `D/idea/claude_cli.js:15–21` (`--restricted` confines file tools to those directories);
     - the contract promise `D/m5/SCHEMAS.md:12–13` ("Opus covers Codex authors when Codex fails").
   - What it cannot express: the fallback the contract promises, for any brief stored outside the run root. That covers every science-step brief, because they live under `experiments/blind-02/science/sNN/`.
   - Blocks: every calibration on m5 while Codex is unavailable. It would equally block the final experiment's intake under the same fallback.
   - Smallest change: before intake, have `pipeline.js` copy the brief into the run (for example `A/intake/source_brief.md`, recording its SHA-256) and name that copy in the prompt. Alternatively, pass `path.dirname(briefPath)` as a read-only `add_dirs` entry for the intake call. Either way, reword "Never read experiments/" to exempt the named brief.

**Aggregate.** Gaps 2, 3 and 7 block calibration; gap 7 is the one blocking now. Gaps 1, 2, 4, 6 and 7 block the final experiment. `gap_blocks = both`.

## F. Narrowing

**Unchanged: no narrowing** (`NARROWING.md`). Run5 measured nothing, and a pipeline defect gives no grounds to change the question.
