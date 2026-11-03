# s06 assessment — 2026-11-03

**Scope.** This step was offline only. I used no network, contacted no box, ran no git commands and read no credentials. I wrote only into s06. I read s01–s05; for s01–s03 I relied mainly on the consolidated records in s04 and s05.

**Shell.** No shell was available in this session; every Bash call was denied. So nothing was hashed or executed. I also could not read `~/.cache/blind01/new_run.py`, because it is outside this session's readable folders.

**Abbreviations.** Paths are relative to the repository root.
- **D** = `dut/pipeline`
- **R5** = `experiments/blind-02/m5/run5`
- **S4** = `science/s04`
- **S5** = `science/s05`

## 0. The operator's finding, checked against the code

**1. Claude agents can read only the folders passed to them.**
- `D/idea/wf.js:128` builds `addDirs` for every non-opencode family. Without isolation it is `[ARGS.base, ...(ARGS.cwd ? [ARGS.cwd] : []), ...(ARGS.add_dirs || [])]`.
- `D/idea/claude_cli.js:21` turns each entry into `--add-dir`.
- This matches the operator's description.

**2. `args.add_dirs` reaches that line in m5 runs.**
- m5 hands its args object to `wf.js` unchanged. R5's `agent/wf/run.json:6–18` shows `args.base` and `args.cwd` as the workflow ARGS, read directly from the run's args.
- So an `add_dirs` key in the run's args lands in `ARGS.add_dirs` at `wf.js:128`. No pipeline change is needed.

**3. Codex is not affected.**
- `D/idea/codex_cli.js:217` maps `addDirs` to *writable* roots only. Reads stay unrestricted, which is consistent with run3 and run4 reading briefs in `science/`.

**4. What I could not verify: which brief path intake is told to read.**
- The intake prompt reads `input.brief` by absolute path (`D/m5/pipeline.js:85–90`).
- If `new_run.py --brief-from` passes `<run_root>/brief/` in `add_dirs` but leaves `args.brief` pointing at `science/s06/CALIBRATION_BRIEF.md`, the Claude agent is denied again. The original's folder would not be among the readable ones.
- The operator says the copied folder is passed "so a Claude understudy can read it", which implies `args.brief` names the copy. Commit 437be48f is titled "new_run --brief-from passes the brief folder in args.add_dirs". I could not read `new_run.py` to confirm either point.
- **Precondition for the operator:** `args.brief` in the new run's `args.json` must name a file inside one of `args.add_dirs`, `args.base` or `args.cwd`.
- Q13 in `PREDICTIONS.md` checks this from the run's records.

**5. A remaining wording conflict.**
- The intake prompt still says "Never read experiments/, operator/, or control/" (`D/m5/pipeline.js:92`). `<run_root>/brief/` sits under `experiments/blind-02/m5/runN/`.
- In run5 the Claude agent ignored this line and tried the Read anyway; the tool denied it, not the agent (S5 §0 point 2).
- Run3 and run4 (Codex) read briefs under `experiments/` despite the line.
- I judge the risk that the agent refuses on this wording to be low, and I lowered Q1 slightly to reflect it. It is a hardening item, not a gap; see §E.

## 1. Does s05's contract gap still stand? `closed_by_add_dirs`

S5 classed gap 7 as a contract gap because "`ARGS.add_dirs` (`wf.js:128`) would avoid it, but it is not among the m5 flags this step may request" (S5 §0).

The contracts could already express the needed access. What was missing was a launcher that used the existing input. Now that `new_run.py --brief-from` passes the brief's folder in `args.add_dirs`, the fallback promised in `D/m5/SCHEMAS.md:12–13` ("Opus covers Codex authors when Codex fails") can read a staged brief.

I therefore record gap 7 as **closed by `add_dirs`** for this route. This is subject to the precondition in §0 point 4 and to Q13.

Two residual defects remain. Neither stops the calibration, so I carry them as hardening notes, not gaps:
- (a) `pipeline.js` does not stage the brief or check that it is readable by every family that may author intake. Without the launcher's help, the same failure recurs for any brief outside the run.
- (b) The "Never read experiments/" wording conflicts with a brief staged under the run root.

## 2. Is s04's calibration still the most informative next test? Yes, unchanged

Nothing scientific has changed since s04:
- Run5 measured nothing (S5 §A–B).
- The two kept candidates, the physical branch `R1:physical:P1` and C2 `seed:idea:2`, still both require this timing screen as their calibration phase (S4 §D; brief "Purpose").
- Its outcomes still decide the per-case physical budget tiers that dense may enter (rho thresholds 1.5 and 2.0). They also decide whether C2's affordability and acceleration components survive (the padding check, and the acceleration screen at 1.05).

The alternatives add no measurement:
- A tree run produces cards, not data.
- The measure route still has no execution controller (gap 3).
- Waiting for Codex (after 2026-11-07 23:30 UTC) cannot be expressed in `NEXT.json`, and with read access fixed it is no longer necessary.

**Choice:** `{"action": "m5", "brief": "CALIBRATION_BRIEF.md", "new_run_flags": ["--stop-after-reproduce"]}`.

**The brief is unchanged.**
- `CALIBRATION_BRIEF.md` is intended to be a byte-for-byte copy of `S4/CALIBRATION_BRIEF.md`. It keeps the heading "Calibration request (science step s04)" because the request is s04's.
- Without a shell I wrote the copy by reading the file and writing it back. Grep checks match on:
  - line count (431 in both);
  - the combined count of curly-apostrophe, blank and trailing-space lines (158 in both);
  - the whitespace-sensitive command and indentation lines (6 in both);
  - trailing spaces (none in s04).
- **The operator must confirm that `sha256(s06/CALIBRATION_BRIEF.md) == sha256(s04/CALIBRATION_BRIEF.md)` before launch.** If they differ, the copy is in error: the s04 file is authoritative, and the run should not launch with a differing s06 copy.

I considered and rejected changes:
- The cost projection (about USD 4 all-in; hard stop at USD 10 or 2 h; new science stops at 75 min) still holds.
- Run5's idle allocation (664.9 s, about USD 0.61, S5 §D) is a sunk cost of a different run.
- The Claude-authored harness may take longer to write than Codex took in run4. The 75-minute science stop and the USD 10 hard stop already bound that, so no change is justified.

**Models for this run.** Intake, harness authoring and harness repairs will run on the **Claude Opus understudy** until Codex resets (2026-11-07 23:30 UTC). Run4's harness was Codex-authored. Run2's GPU build commands are embedded in the brief, and the `megadock -h` exit-255 rule is stated there, so a Claude author starts from the same evidence. Q2 and Q14 carry the added harness risk.

**Projected cost:** under USD 5. **Decision value:** medium. It decides budget tiers and screens C2's components; it does not resolve tolerances.

## 3. Predictions

There are 14 fresh sealed predictions (`PREDICTIONS.md`, `predictions.json`):
- Q1–Q12 repeat s04's statements and resolution rules. Q1, Q2 and Q3 have lower probabilities because of the Claude authorship.
- Q13 is new: intake read access.
- Q14 is new: harness repairs.

s05 sealed no predictions, so `outcomes.json` is `{"items": []}`.

## 4. Candidates

The candidates are unchanged from S5 §C.
- **Kept (two):** C2 (`seed:idea:2`), provisionally, and the physical branch (`R1:physical:P1`).
- **Unchanged:** C1 and C3 stay REJECT, I2 stays halted, and C4 stays a reserve diagnostic.

## 5. Narrowing

None (`NARROWING.md`).

## E. Contract gaps (final list for the owner)

| # | Gap | Where | What it cannot express | Blocks | Smallest change |
|---|---|---|---|---|---|
| 1 | m5 has no named-arm ordered comparisons | `D/m5/SCHEMAS.md` (PREDICTIONS 178–188, Propose 211–215, Evaluate 281–299); `D/m5/pipeline.js:1037–1038` | CPU/GPU agreement gating a dense-quality comparison, with per-case rank1/best50 at common budgets, outside the fixed method menu | the seed's agreement and quality parts (final experiment) | an optional named-arm comparison mode with sealed agreement/quality metrics, ordered prerequisites and unavailable-arm outcomes |
| 2 | The PLAN→measure handoff loses the protocol | `D/CONTRACT.md` §2.5, §5 calibration; `D/src/main.js:468–478`; `D/launch.js:71–96` | arms, decision rules, tiers and held-fixed settings; only scalar GUESS/PROXY ratio bands survive | calibration on the measure route, and the final experiment | an immutable full PLAN handoff, with scientific decisions kept separate from price bands |
| 3 | The measure route has no execution controller | `D/launch.js:45–47, 83–107, 141–153` | a chained design→post stage run (m4's `measure.sh` is absent) | calibration on the measure route | a validated stage-argument chain with watchdog and ledger ingestion |
| 4 | The cost queue cannot represent scientific readiness | `D/src/cost.js:154–163`; `D/src/main.js:470–478`; `D/CONTRACT.md` §5 | unresolved tolerances (atol, rtol, eps) as required evidence; cards show `no_unmeasured_input` while blocked | the seed's "justified tolerances before comparative results" (moving from calibration to the agreement study) | typed required-evidence records, separate from numeric cost inputs |
| 5 | No route for authorised local evidence | `D/src/prompts.js:107–110`; `D/src/gates.js:313–327, 373–388`; `D/m5/pipeline.js:89–108` | intake following owner-authorised pointers to prior records; every brief must embed history by hand | reproducible calibration identity across steps | a hashed, owner-authorised evidence bundle carried through the contracts |
| 6 | Cost accounting uses stage walls | `D/m5/pipeline.js:1007–1008` | the seed's "billed allocation cost": the takeaway omits allocation before intake and after the last receipt (run5: USD 0.014 stage-wall against about USD 0.61 allocation span) | cost reporting in the final experiment | report the allocation span (existing `runBoxUSD`, `pipeline.js:62–68`) and the invoice |
| 7 | **Closed by `add_dirs` (s06).** The understudy could not read briefs outside the run | `D/m5/pipeline.js:85–92`; `D/idea/wf.js:128`; `D/idea/claude_cli.js:21` | — (expressible through the existing `args.add_dirs`; the launcher now uses it) | nothing, once the §0 point 4 precondition holds | hardening only: have `pipeline.js` stage the brief into the run and name the copy; reword "Never read experiments/" to exempt the named brief |

**Aggregate.** Six gaps are open (1–6).
- Gaps 2 and 3 block calibration on the tree's own measure route.
- Gaps 1, 2, 4 and 6 block the final experiment.
- m5 reproduce-only stays usable for calibration once gap 7 is closed.
- Therefore `gap_blocks = both`.

**What will need the owner after this test** (unchanged from S4 §D): justified CPU/GPU numerical tolerances. Neither route can produce them (gap 4).
