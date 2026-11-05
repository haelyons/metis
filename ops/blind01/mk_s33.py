import json, os
B = os.path.expanduser("~/.cache/blind01")
s = """## Step s33 (bookkeeping only: carry s32's main comparison forward unchanged; no network)
Your step folder is `experiments/blind-02/science/s33/`. Read `science/s32/` (its NEXT.json, design file, brief, PREDICTIONS.md, predictions.json and status.json). s32 repaired s31's main comparison so that no sealed number appears in what the run's agents see (the operator's check now gives 0 matches), but its `outcomes.json` was `{"items": []}`, while the route requires one item for every prediction id of the previous step's `predictions.json`, with `outcome` true, false or null. The operator's prompt for s32 was at fault, not s32's science.

Do exactly this and nothing else:
1. Copy into this folder, byte for byte, s32's design file (the one its NEXT.json names), s32's brief (the one its NEXT.json names), `PREDICTIONS.md`, `predictions.json` and `NARROWING.md`, under the same file names. Change no byte. Check with `python3 -c` (hashlib) that each copy's SHA-256 equals its source's.
2. Write `outcomes.json`: `{"items": [{"id": "<id>", "outcome": null}, ...]}`, one item for every prediction id in s32's `predictions.json`, all `null` (the run they predict has not happened).
3. Write `NEXT.json`: s32's NEXT.json with the brief and design file names pointing at the copies in this folder (the same names).
4. Write `ASSESSMENT.md`: one paragraph saying this step copies s32 unchanged and why, and listing each file with its SHA-256.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"copies_identical"`: `"yes"`, `"no"`
- `"next_action"`: `"m5"`, `"stop"`
- `"stop_reason"`: `"none"`, `"no_justified_test"`, `"needs_owner"`, `"contract_gap"`, `"limits"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 15 minutes."""
open(f"{B}/sci_s33.md", "w").write(s)
keys = {}
for line in s.splitlines():
    if line.startswith('- `"') and '`: ' in line:
        k = line.split('`"', 1)[1].split('"`', 1)[0]
        keys[k] = [v.strip('`"') for v in line.split("`: ", 1)[1].split(", ")]
json.dump({"enums": keys, "actions": ["m5", "stop"]}, open(f"{B}/sci_s33.enums.json", "w"), indent=1)
print("ok", len(keys))
