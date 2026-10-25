# m5 data contracts (what test authors may rely on; implementers keep this file current)

## A/intake/ (written by the intake agent; checked by the pipeline)
- benchmark.json, data.json: non-empty JSON objects.
- anchors.json: an array; each item has a unique non-empty string `id`, non-empty `quantity` and `source`, finite numeric `published_value`, and `tolerance`. Its length must equal facts.anchors_count. Zero is a valid published value or tolerance.
  - `tolerance` is a finite nonnegative number (absolute tolerance), or an object with exactly one key: `{"abs": x}` or `{"rel": x}`, where `x` is finite and nonnegative. Relative tolerance resolves to `x * abs(published_value)`; a zero reference therefore requires exact agreement. An anchor passes when `abs(measured_value - published_value) <= resolved_absolute_tolerance`.
- baseline.json: non-empty repo, build_commands, run_commands and published_configuration, plus commit or pin.
- EXECUTION.json: non-empty representative_scale, inputs, outputs and timing_scope. Optional `timeout_s` sets the common script timeout (default 3600 seconds); optional `timeouts` object has `setup`, `run_anchors`, and/or `profile` to override individual script timeouts. Each supplied timeout is an integer in [1, 999999999] seconds. The setup timeout also applies to each harness upload and the one allowed setup retry.
- The intake passes only when the files are complete and found is true, anchors_count >= 1, data is "available", licence is "permitted", and stock_environment is not false.

## A/harness/ (written by the harness agent)
- `setup.sh`, `run_anchors.sh`, `profile.sh` are bash scripts. The pipeline invokes them as `bash harness/<name>` from one fresh `/tmp/m5-<uuid>` directory on the already-running operator-managed box. They share that directory across reproduce and profile. No dev lifecycle commands are issued. `BOX` and `FETCH` are inherited unchanged by `boxrun.sh`, including injected executables.
- `setup.sh` installs/builds the exact published baseline in the stock image; sudo is allowed only for apt. Published source/configuration stays under `baseline-published/`; inputs stay under `data/`. Setup must tolerate one retry in the same directory. Tuning is deferred.
- `run_anchors.sh` runs the published protocol at the intake's representative scale and writes `out/anchors_measured.json` as an object mapping each intake anchor ID to a finite measured number. Every anchor must have a measurement. Additional numeric measurements are ignored for scoring. Booleans and nonfinite values are invalid.
- `profile.sh` runs the baseline once at representative scale, with stage wall timers and `nvidia-smi` sampling. It writes `out/profile/stages.json`, `out/profile/total_wall_s.json`, and raw telemetry under `out/profile/`. Unavailable GPU timings remain null; scripts must not substitute allocated GPU time.
- There is one initial agent call (`harness`, `ls-writer`, `sonnet`). Only a nonzero setup exit permits one repair call (`harness-repair`, same role/model), given at most the last 200 setup-log lines. Only `setup.sh` is recopied; setup runs once more. A second failure stops reproduction.

## A/results/reproduce/ and deterministic anchor scoring
- Every reproduce box command fetches remote `out/` into `A/results/reproduce/out/`, and its `<receipt-id>.log` into `A/results/reproduce/`. Logs remain in the agent view. The local fetched `out/` is cleared before each command to prevent stale measurements. The final copy contains the anchor run's outputs.
- `python3 m5/score_anchors.py <anchors.json> <measured.json> <out.json>` writes an atomic JSON object with exact keys `anchors`, `anchors_passed`, `anchors_total`, `all_passed`.
  - `anchors` preserves intake order and contains `{id, published_value, measured_value, tolerance, passed}` for every anchor. `tolerance` preserves its input form; `passed` is boolean.
  - `anchors_passed` and `anchors_total` are nonnegative integer counts; `all_passed` is boolean. Empty anchor arrays, duplicate IDs, missing measurements, invalid numbers/tolerances, and nonfinite calculated differences/tolerances are parse errors.
  - Exit 0 means every anchor passed; exit 4 means a tolerance mismatch; exit 1 means invalid/missing input or an output write failure. Invalid input does not produce a new score file. Diagnostics contain no input content.
- The pipeline writes the score to `A/results/reproduce/anchors_scored.json`.
- Reproduce facts are `{anchors_passed, anchors_total, stock_verified, tuned_control_valid}` plus common `tokens_known` and `gpu_busy_known`. Counts remain null until scoring succeeds; `stock_verified` is true only after setup exits 0; `tuned_control_valid` remains null. The gate passes only when stock is verified and every anchor passes. `run_valid` is true/false when anchor scoring passes/fails.

## A/results/profile/ and A/profile-packet.json
- Profile fetches remote `out/` to `A/results/profile/out/`; logs are `A/results/profile/<receipt-id>.log`. Its timing inputs are therefore under `A/results/profile/out/profile/`.
- `stages.json` is a non-empty array of `{stage, wall_s, gpu_s}`. `stage` is a non-empty string; `wall_s` is finite nonnegative seconds; `gpu_s` is finite nonnegative seconds or null and must be present. Stage wall times must describe critical-path coverage without double-counting overlap. Extra input fields are not copied to the packet.
- `total_wall_s.json` is an object with finite positive numeric `total_wall_s` in seconds. The sum of stage wall times must also be finite.
- The deterministic pipeline writes `A/profile-packet.json` with exact keys:
  - `stages`: the validated timing rows, each augmented with `wall_fraction = min(1, wall_s / total_wall_s)`;
  - `total_wall_s`: the measured total;
  - `timed_fraction = min(1, sum(stage.wall_s) / total_wall_s)`;
  - `gpu_telemetry`: true if any stage has non-null `gpu_s`, including zero.
- Profile facts are `{profile_complete, timed_fraction, gpu_telemetry}` plus common `tokens_known` and `gpu_busy_known`. `profile_complete` is true when the command exits 0 and both timing inputs validate, even when coverage is below 90%. The gate requires `profile_complete` and `timed_fraction >= 0.9`. Low coverage preserves the packet and fails the gate.

## C/receipts/ and stage failure signatures
- Every box command (uploads, setup attempts, anchor execution, profiling) runs through `m5/boxrun.sh`; every receipt is `C/receipts/NNNN-<operation>.json`. Operations are `upload`, `setup`, `anchors`, `profile`; numbering continues across existing receipts. Receipt/log IDs contain no benchmark labels.
- Receipts use the existing boxrun format: `{name, rc, timed_out, wall_s, fetched, started_utc, ended_utc}`. `name` is the receipt ID; `rc` is an integer remote exit code or null; `timed_out` and `fetched` are booleans; `wall_s` is nonnegative integer elapsed seconds; timestamps are UTC strings. Remote `out/` is fetched using the unchanged boxrun interface. Receipt contents stay in control; runtime logs stay in agent results.
- Failed reproduce/profile signatures have fixed `error_class`: `infra` for unavailable box execution/receipts, failed upload, or failed fetch after a successful command; `install` for failed setup after the bounded repair; `anchor` for an anchor-run failure or tolerance mismatch; `parse` for missing/invalid output files, unavailable harness files, or incomplete profile coverage. Exit codes are 4 for anchor failures and 2 for the other failures. `infra` is added to the shared v1 error-class enum so the v2 envelope remains v1-valid. Box/fetch stdout and stderr are never copied into operator signatures.
- Numeric ratio facts accept finite JSON numbers, including integer spellings such as `0` and `1`; booleans remain invalid. This permits fully timed profiles to emit the capped fraction `1`.
- Reproduce/profile common facts `tokens_known` and `gpu_busy_known` remain false: these stages do not yet aggregate model usage or measured GPU-busy time. Stage GPU telemetry is reported separately. Downstream scientific stages are skipped after either failed gate; takeaways still runs.

## A/PREDICTIONS.json (written by the seal agent; checked, then sealed)
- `predictions`: an array, one item per feasible method, with unique methods taken from the menu ["data-parallel over inputs", "batching", "multi-GPU", "ensembles", "pipelining"]. Each item has:
  - `expected_speedup_interval` {low > 0, high >= low};
  - `outcome_vs_compute_points`, holding for every value in compute_budgets one {compute_budget, predicted_outcome, uncertainty}, all non-empty.
- Required non-empty keys: equivalence_metrics, paired_seed_tests, sample_sizes, confidence_rule, hardware_cost_basis, timing_scope, minimum_worthwhile_gain (a number > 1), evaluation_inputs, splits, compute_budgets (at least 3 distinct positive numbers), repetitions (an integer >= 5), warmup, scheduling_order and equal_outcome_target.
- Seal: C/seals/NNNN.json {sha256, path, utc}. The sha256 is over the canonical JSON: keys sorted recursively, array order kept, compact separators, UTF-8. Numbering continues; nothing is overwritten.
