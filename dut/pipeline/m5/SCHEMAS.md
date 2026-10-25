# m5 data contracts (what test authors may rely on; implementers keep this file current)

## A/intake/ (written by the intake agent; checked by the pipeline)
- benchmark.json, data.json: non-empty JSON objects.
- anchors.json: an array; each item has non-empty id, quantity, published_value, tolerance and source. Its length must equal facts.anchors_count.
- baseline.json: non-empty repo, build_commands, run_commands and published_configuration, plus commit or pin.
- EXECUTION.json: non-empty representative_scale, inputs, outputs and timing_scope.
- The intake passes only when the files are complete and found is true, anchors_count >= 1, data is "available", licence is "permitted", and stock_environment is not false.

## A/PREDICTIONS.json (written by the seal agent; checked, then sealed)
- `predictions`: an array, one item per feasible method, with unique methods taken from the menu ["data-parallel over inputs", "batching", "multi-GPU", "ensembles", "pipelining"]. Each item has:
  - `expected_speedup_interval` {low > 0, high >= low};
  - `outcome_vs_compute_points`, holding for every value in compute_budgets one {compute_budget, predicted_outcome, uncertainty}, all non-empty.
- Required non-empty keys: equivalence_metrics, paired_seed_tests, sample_sizes, confidence_rule, hardware_cost_basis, timing_scope, minimum_worthwhile_gain (a number > 1), evaluation_inputs, splits, compute_budgets (at least 3 distinct positive numbers), repetitions (an integer >= 5), warmup, scheduling_order and equal_outcome_target.
- Seal: C/seals/NNNN.json {sha256, path, utc}. The sha256 is over the canonical JSON: keys sorted recursively, array order kept, compact separators, UTF-8. Numbering continues; nothing is overwritten.
