You are an independent reviewer (a different model family from the author) of units U54, U55 and U56 in this worktree, branch `units`. Read-only: change nothing. Never read anything under experiments/.

The contract is fixed and was written before the code: `dut/pipeline/m5/SCHEMAS.md`, sections "Card calibration (U54)" and "Card write-back and re-judging (U56)", and in `dut/pipeline/CONTRACT.md` the PLAN field `band?` and the bullet beginning "`calibration` in the return (2026-10-21)" (U55). The contract is in commits 69e9194d and 901968ad (the second states five points explicitly after your first review). The implementation and its tests are the last commit (`git show --stat HEAD`, `git show HEAD`). Claude wrote both the code and the tests, in separate sessions, the test author without access to the code.

This is your second review. Your first review (below, between the lines) found five implementation defects and six test gaps; a fix round followed. First check each of the eleven items: fixed, partly fixed, or not fixed, with the evidence. Then review the whole change against the contract again, as before: report, most severe first, each place where the code does not do what the contract says or does something it forbids: a wrong or missing rule, a behaviour change without `args.card`, a card value, band, gate threshold, prediction or anchor value an agent of the run could read, a seal that does not cover what it must, a test that would pass on a wrong implementation of a contract rule, or a contract rule no test checks. For each, give the file and line, the contract sentence, and a concrete case that shows the defect. Do not report style. If you find nothing, say so. For the U54 half of item 8, the operator's evidence is that the m5 suites written before U54 (`tools/test_m5_reproduce.js`, `tools/test_m5_units_check.js`, `tools/test_m5_units_probe_pipeline.js`) changed only by adding the four null card facts to their exact fact sets and still pass; check that claim in the diff and say whether it suffices. `tools/test_m5_reproduce.js` fails intermittently with `concurrency receipt missing` or a profile ENOENT on main before these units as well (a fixture race under load); it is not part of this review.

-----
HEAD is contract commit `69e9194d`; reviewed uncommitted implementation/tests against that contract. Nothing changed. Nothing under `experiments/` read. Verification used read-only inspection and in-memory probes; test suites were not run because they write files.

1. **Hidden launch bands remain agent-readable.**  
   Locations: `dut/pipeline/idea/wf.js:71–78`; `dut/pipeline/m5/pipeline.js:98–109`; test omission at `dut/pipeline/tools/test_m5_card_pipeline.js:338`.  
   Contract: “no agent of the run sees the card’s values, bands, gate thresholds, predictions or anchor value”; “Agents see only `A/card_inputs.json`.”  
   Case: launch with `card.bands = {mem_gb: {abs: 500}}` and workflow output `agent/wf`, as the pipeline tests do. `wf.js` writes those raw arguments into `agent/wf/run.json`. An agent can read the launch band inside its own folder without reading `control/`. The same file reveals the original result path. Tests inspect prompts and `card_inputs.json`, overlooking this copy.

2. **Valid input ID `anchor` breaks scoring or substitutes the anchor measurement.**  
   Locations: `dut/pipeline/m5/score_card.py:49–63,169–174`.  
   Contract: extraction contains “one rule per `inputs` entry in order, then one rule with id `"anchor"` when `anchor` is non-null”; “The anchor never decides an input.”  
   Case: required input `{id:"anchor", basis:"GUESS", value:10}` is valid. Without a published anchor, line 174 mistakes its input rule for an anchor rule and fails. With a published anchor, `dict(zip(ids, rules))` overwrites the input rule with the final anchor rule. If input output is 10 and anchor output is 100, the input is incorrectly measured as 100 and refuted. Both cases confirmed in memory; neither is tested.

3. **Write-back accepts invalid scored files and measurements belonging to another card.**  
   Location: `dut/pipeline/m5/card_resolve.js:53–62`.  
   Contract: “a missing or invalid file … exits 1 and writes nothing.”  
   Case: `card_scored.json` containing only `rows` with an input ID, rule, measurement and `"decision":"holds"` passes validation despite lacking required identity, hashes and totals. It can mark the card calibrated. A scored file explicitly naming key `B` and an incorrect `card_sha256` is also accepted for sealed card `A`. Both cases confirmed with an in-memory filesystem. Tests at `tools/test_m5_card_resolve.js:383–405` cover malformed JSON, but not malformed scored schemas or mismatched scored identity.

4. **An oversized JSON number fails the stage instead of becoming unmeasured.**  
   Locations: `dut/pipeline/m5/score_card.py:22,80–86,203`.  
   Contract: applying extraction rules to “a value that is not a finite number gives null.”  
   Case: output `{"x": <400-digit integer>}`, extracted through `/x`, causes `math.isfinite()` to raise `OverflowError`. `measure()` does not catch it; the outer handler exits 1, causing reproduce to fail with `parse`. It should produce a null measurement. Confirmed in memory. Tests cover overflowing floating-point notation, but not this integer case.

5. **Failed standalone scoring can leave an earlier successful output in place.**  
   Locations: `dut/pipeline/m5/score_card.py:164–185,201–205`.  
   Contract: “Exit 1 for invalid or missing input, a seal mismatch or a failed write, with no output file.”  
   Case: score successfully, alter `card.json` without updating its seal, then invoke the scorer again. The second invocation exits 1 but leaves the previous `card_scored.json`. Pipeline-side removal protects its normal invocation, but the script’s specified behavior remains wrong. Tests at `tools/test_m5_card_score.py:302–305` always start without an existing scored file.

6. **Re-judging tests do not verify deterministic gate results or remaining uncertainty.**  
   Location: `dut/pipeline/tools/test_m5_card_resolve.js:334–339`.  
   Contract: “`gate_action` and `gate_reasons` are `gate_plan`’s `action` and `reasons`; `uncertain_after` lists the ids of the new evaluation’s `uncertain`.”  
   Wrong implementation that passes: return `"gate_action":"ok"`, `"gate_reasons":[]` and `"uncertain_after":[]` for every run. Assertions accept any allowed action, any reasons array and any uncertainty array lacking measured IDs. They never compare the required results.

7. **U55 tests do not establish that `judged` contains the actual evaluation arguments.**  
   Location: `dut/pipeline/tools/test_tree_calibration_u55.js:191–206`.  
   Contract: `judged` contains “the plan the record’s `plan_usd` was evaluated from, the pick, and the `given` and `args` objects that `cost_eval_plan` and `gate_plan` received.”  
   Wrong implementation that passes: preserve plan number IDs and title, but change their values; emit `pick:{}`, `gate_args:{}`, and an incorrect numeric budget in `given`. Current checks verify object shapes, selected plan fields, the price sheet and budget type—not the actual arguments.

8. **Compatibility tests compare the changed implementation with itself.**  
   Locations: `dut/pipeline/tools/test_tree_calibration_u55.js:213–231`; `dut/pipeline/tools/test_m5_card_pipeline.js:520–531`.  
   Contract: U55 “changes no prompt and no other output” and resumes an earlier run; U54 says “Without `args.card`, every stage is unchanged.”  
   Wrong implementation that passes: change every producer prompt before both U55 test runs. The second run still finds the first run’s changed prompts in cache. Likewise, the no-card pipeline cases establish current behavior, without comparing pre-change behavior. Neither test establishes the required backward compatibility.

9. **U56 tests leave replacement order and merged provenance unchecked.**  
   Location: `dut/pipeline/tools/test_m5_card_resolve.js:310–355`.  
   Contract: replacement removes `rests_on`, `source_id`, `quote` and `page_setting`; provenance comes from the latest measured entry; “`measured_ids` lists the replaced ids in `required` order.”  
   Wrong implementations that pass: retain the forbidden fields in the evaluated plan, use earliest provenance when merging, or sort `measured_ids` alphabetically. Re-judging fixtures contain only one required ID; assertions check emitted per-run provenance, not provenance merged into the re-evaluated plan.

10. **U55 invalid-band coverage tests only one invalid form.**  
    Location: `dut/pipeline/tools/test_tree_calibration_u55.js:54–72`.  
    Contract: “a `band` that is not `{abs: x}` with finite `x > 0` counts as absent.”  
    Wrong implementation that passes: reject `{abs:0}` but accept `{abs:-5}` or `{abs:"wide"}`. `INVALID_BANDS.find(...)` selects only the first schema-accepted invalid form, so the remaining listed invalid forms never exercise calibration output.

11. **New signature facts lack validation and compatibility tests.**  
    Locations: `dut/pipeline/m5/signatures.py:74–76`; missing coverage beside reproduce-extension tests in `dut/pipeline/tools/test_m5_signatures.py:669`.  
    Contract: the four card totals are optional “nonnegative integers”; “records without them stay valid.”  
    Wrong implementation that passes current new tests: accept negative, fractional or boolean card totals, or require these fields on older signatures. Pipeline tests exercise generated nonnegative totals and nulls; they do not test these validator requirements.

VERDICT: defects
-----

Write the report to the file named by the `-o` option. End with one line exactly `VERDICT: clean`, `VERDICT: minor` (only defects that change no result) or `VERDICT: defects`.
