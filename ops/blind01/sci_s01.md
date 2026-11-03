
## Step s01 (first step; no network)
Your step folder is `experiments/blind-02/science/s01/`. No earlier science steps exist. The next test you choose should normally be a tree run; choose `stop` only with a stated reason.

Answer in `ASSESSMENT.md`, in this order:
A. The owner's impression, checked against run2's evidence. What run2 established about the workload (measured, with numbers), what it established only about m5's fixed menu, and which parts of the seed's question remain open. Say where the impression is right, where it needs qualifying, and where it is wrong.
B. The seed's question split into parts P1..Pn (each a separately answerable comparison or conclusion), each with: what run2 or blind-01 already measured about it, and what remains.
C. Candidate experiments, each addressing named parts: what it compares (arms, cases, metric, tolerance), which mechanism could run it (tree card then measure calibration; an m5 option; neither), its cheapest distinguishing measurement (what it measures, on which box, projected box hours and USD from run2's receipts, what result would rule the candidate in or out), and the risk that the measurement is uninformative. Rank them by information per dollar.
D. The tree run you propose: the fixed root question(s), any seed ideas (candidates you want carded for certain rather than left to the branches), picks per branch, budget, and why. State what a tree card can and cannot carry for each candidate (PLAN arms, anchor, decision_rule and noise_rule are carried in the card; the compiled measure route checks only GUESS/PROXY inputs).
E. Contract gaps: each comparison a candidate needs that no existing mechanism expresses, as file, section, and what is missing. Distinguish gaps that block calibration from gaps that block only the final experiment.
F. Your chosen next test and why it is the most informative one now.

Write `tree_args.json` (if the next action is `tree`) with only the keys the tree reads: `seed`, `fixed_roots` (1 to 3), optional `seed_ideas` (at most 4), `picks_per_branch` (1 or 2), optional `pool_k`, `require_compute_lever`, `deepen_on_signal`, `budget_usd` (at most 1000), `budget_covers_storage`, `budget_covers_tax`. The tree's agents see the root questions and seed ideas, so write them self-contained, in plain words, with whatever materials pointers the agents need (they can read files and fetch web pages).

Predictions for the tree run: for example whether each seed idea reaches a PASS card, how many cards end `calibration_required`, whether the inputs to calibrate are measurable under USD 20 each, and whether a card's decision rule addresses a part of the seed's question that run2 left open.

`status.json`: one JSON object with exactly these keys, each taking only the listed values:
- `"impression"`: `"supported"`, `"partly_supported"`, `"not_supported"`, `"unknown"`
- `"run2_workload_finding"`: `"menu_negative_only"`, `"workload_measured_and_menu_negative"`, `"other"`, `"unknown"`
- `"question_open"`: `"yes"`, `"partly"`, `"no"`, `"unknown"`
- `"parts_count"`: `"one"`, `"two"`, `"three"`, `"four_or_more"`
- `"parts_open"`: `"all"`, `"most"`, `"some"`, `"none"`
- `"candidates_count"`: `"none"`, `"one"`, `"two"`, `"three"`, `"four_or_more"`
- `"candidates_tree_expressible"`: `"all"`, `"some"`, `"none"`
- `"candidates_calibratable_existing"`: `"all"`, `"some"`, `"none"` (an existing mechanism can run its distinguishing measurement)
- `"cheapest_measurement_usd"`: `"under_5"`, `"5_to_20"`, `"over_20"`, `"unknown"`
- `"narrowing"`: `"none"`, `"explicit"`
- `"contract_gaps"`: `"none"`, `"one"`, `"two_or_more"`
- `"gap_blocks"`: `"none"`, `"calibration"`, `"final_experiment_only"`, `"both"`
- `"gap_location"`: `"none"`, `"tree"`, `"measure"`, `"m5"`, `"multiple"`
- `"next_action"`: `"tree"`, `"measure"`, `"m5"`, `"stop"`
- `"tree_roots"`: `"none"`, `"one"`, `"two"`, `"three"`
- `"seed_ideas"`: `"none"`, `"one"`, `"two"`, `"three"`, `"four"`
- `"prediction_count"`: `"none"`, `"1_to_5"`, `"6_to_10"`, `"11_to_20"`

No other keys and no free text. Finish within 40 minutes.
