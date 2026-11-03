
## Step s08 (contract gap register for the owner and the operator; no network; no new test)
Your step folder is `experiments/blind-02/science/s08/`. Read `science/s01/` to `science/s07/` first. s07 stopped the route with `contract_gap`. This step runs no test: it turns the final contract gap list into a register the blind operator can act on without reading content.

Write `GAPS.json`: `{"items": [...]}` with one item per gap (at most 8), each exactly these keys:
- `"id"`: `"G1"`, `"G2"`, ... in order of importance.
- `"file"`: the repository path, relative to `/home/hal/dev/interp/metis`, of the contract or code file where the change belongs. It must be an existing file under `dut/`.
- `"section"`: a heading line copied exactly from that file (for a `.md` file, a line starting with `#`, without the leading `#` characters and the space; for a code file, a comment line copied exactly, without the comment marker and the space). The operator checks that it occurs verbatim in the file. Never put seed or record content here.
- `"kind"`: one of `"comparison_arms"` (the mechanism cannot hold the configurations or cases the question compares), `"quality_metric"` (it cannot score the outcome the question needs), `"tolerance_equivalence"` (it cannot judge equivalence or tolerance the question needs), `"route_execution"` (a route exists on paper but has no runnable chain), `"record_carryover"` (a later stage drops fields an earlier one recorded), `"agent_access"`, `"other"`.
- `"blocks"`: `"calibration"`, `"final_experiment"`, `"both"`.
- `"parts_blocked"`: how many of your parts P1..Pn it blocks: `"one"`, `"two"`, `"three_or_more"`.
- `"change_size"`: `"small"` (one rule or field), `"medium"` (one stage's contract and code), `"large"` (a new route or stage).
- `"existing_workaround"`: `"none"`, `"partial"`, `"full"`.

Also write `ASSESSMENT.md` for the owner: each gap in prose (what it cannot express, which parts it blocks, the smallest change, what that change would risk), the order you would close them in, and what the owner must decide. Write `NARROWING.md` ("No narrowing." with the reason, or what changed), `PREDICTIONS.md` ("No test; no predictions."), `predictions.json` `{"items": []}`, `outcomes.json` `{"items": []}` (s07 sealed none), and `NEXT.json` `{"action": "stop", "reason": "contract_gap"}`.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"gap_count"`: `"one"`, `"two"`, `"three"`, `"four_or_more"`
- `"gaps_blocking_calibration"`: `"none"`, `"one"`, `"two_or_more"`
- `"largest_change"`: `"small"`, `"medium"`, `"large"`
- `"first_gap_change_size"`: `"small"`, `"medium"`, `"large"`
- `"owner_decision"`: `"approve_contract_change"`, `"choose_between_gaps"`, `"accept_partial_answer"`, `"other"`
- `"next_action"`: `"stop"`
- `"stop_reason"`: `"contract_gap"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`

No other keys and no free text. Finish within 30 minutes.
