# run7 failure cause: report for the owner (2026-11-04)

Scope: read-only. I read `run7/args.json`, `run7/control/comparison.json` and the receipts, `run7/agent/harness/`, `run7/agent/results/evaluate/comparison_compute.json`, all 13 `wrap.json` files and their evaluator logs, `../science/s28/` (assessment, design and brief section), the pinder source in the fetched venv tree, and `dut/pipeline/m5/cmp_wrap.py` and `SCHEMAS.md`. I ran nothing on a box, used no network and no git, and wrote only into this directory. Paths below are relative to `experiments/blind-02/m5/` unless they are absolute or start with `dut/`. `w1/` is short for `run7/agent/results/evaluate/comparison/w1/`.

## Summary

- **The arm part of every invocation succeeded.** For all 13, `status` is `ok`, `adapter_rc` is 0, and both commands have `rc` 0. Each `out/` holds `docking.out` and `model_1..50.pdb`.
- **The evaluator part of every invocation hung until it was killed** (`eval_status` `timeout`, `eval_rc` null).
- **Cause:** the harness's `evaluate.sh` runs the evaluator's Python from standard input. PINDER's `BiotiteDockQ` starts a `spawn` multiprocessing pool by default. Each spawned worker tries to re-import the main program from the path `<stdin>`, dies with `FileNotFoundError`, and is replaced. The pool never finishes.
- **Where the defect is:** the harness script that the harness agent wrote. It is not in the comparison mechanism, the box, or the arm commands.
- **The comparison mechanism did its job.** The users, private data, permissions and the GPU access by `cmp-arm` all worked.
- **s28's design names the exact cause and requires the fix.** At run7's measured per-invocation cost it does not fit its budget. With the fix in place and the evaluator's own cost (never measured on this route) under about 80 s per invocation, it fits on both an A10 and an H100.
- **A rerun as s28 designed it can succeed without a pipeline fix.** Two pipeline guards are recommended but not required (§D).

## A. Why each invocation failed

The design schedules 7 rounds (1 warmup and 6 replicates) × 4 arms × 4 inputs = 112 invocations. Only 13 ran, all in the warmup round, and the other 99 are `not_run` (`comparison_compute.json:3-171` against `172-1458`). Figures come from each `w1/<arm>/<input>/wrap.json`. "cmd1" is megadock and "cmd2" is the decoygen/assembly loop. Walls are in seconds.

| k | arm | input | status | adapter_rc | cmd1 rc / wall | cmd2 rc / wall | eval_status | eval_rc | eval_wall_s |
|---|---|---|---|---|---|---|---|---|---|
| 1 | A2 | f1glj | ok | 0 | 0 / 19.15 | 0 / 0.77 | timeout | null | 901.05 |
| 2 | A0 | f1glj | ok | 0 | 0 / 18.95 | 0 / 0.92 | timeout | null | 901.04 |
| 3 | A1 | f1a19 | ok | 0 | 0 / 1.17 | 0 / 0.37 | timeout | null | 901.05 |
| 4 | A0 | f1ht8 | ok | 0 | 0 / 38.12 | 0 / 0.87 | timeout | null | 901.02 |
| 5 | A1 | f1dtd | ok | 0 | 0 / 2.12 | 0 / 0.21 | timeout | null | 901.03 |
| 6 | A0 | f1dtd | ok | 0 | 0 / 9.55 | 0 / 0.21 | timeout | null | 901.02 |
| 7 | A2 | f1dtd | ok | 0 | 0 / 9.55 | 0 / 0.21 | timeout | null | 901.03 |
| 8 | A1 | f1ht8 | ok | 0 | 0 / 5.88 | 0 / 0.51 | timeout | null | 901.03 |
| 9 | A1 | f1glj | ok | 0 | 0 / 2.77 | 0 / 0.51 | timeout | null | 901.03 |
| 10 | A2 | f1a19 | ok | 0 | 0 / 2.28 | 0 / 0.21 | timeout | null | 901.03 |
| 11 | A3 | f1ht8 | ok | 0 | 0 / 5.88 | 0 / 0.51 | timeout | null | 901.03 |
| 12 | A3 | f1glj | ok | 0 | 0 / 2.77 | 0 / 0.46 | timeout | null | 901.02 |
| 13 | A2 | f1ht8 | ok | 0 | 0 / 21.49 | 0 / 0.51 | timeout | null | 665.79 |

- **Invocations 1 to 12:** the evaluator ran into the design's `evaluator.timeout_s` of 900 (`run7/control/comparison.json:385`).
- **Invocation 13:** its evaluator was cut at 665.8 s by `left_s`, the budget remaining (`cmp_wrap.py:113,285`). After that, `budget_s` 12,600 (`comparison.json:391`) was spent and the remaining 99 were `not_run`.
- **Where the time went:** arm walls total about 146 s and evaluator walls about 11,478 s (`comparison_compute.json:1502-1506`).
- **Both stdout and stderr of the evaluator are empty** (`w1/*/log/evaluator.{stdout,stderr}`). This is expected, because `evaluate.sh:11` sends all output to `eval/evaluator.log`.

**Decisive log lines.** Every `w1/*/eval/evaluator.log` consists entirely of this block, repeated (`w1/A2/f1ht8/eval/evaluator.log:1-15`, identical to the fetched `cmp-fetch/eval/evaluator.log`):

```
  File "/usr/lib/python3.10/multiprocessing/spawn.py", line 236, in prepare
    _fixup_main_from_path(data['init_main_from_path'])
  ...
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/m5-259707aa-3568-4ed2-8ca5-ffc495eeeb34/<stdin>'
```

The count of `FileNotFoundError` lines per log ranges from 492,963 (`A0/f1glj`) to 842,748 (`A2/f1dtd`), and is 610,821 for the 665 s invocation 13. That count reflects a worker pool respawning dead workers without pause until it is killed. It does not look like one failure. No log holds any other error, and no `eval/` holds a `dockq.json`.

**The mechanism of the hang:**
1. `run7/agent/harness/evaluate.sh:11` runs `"$VPY" - <<'PY' ... PY`, so the evaluator's code is read from standard input and `__main__.__file__` is `<stdin>`.
2. `evaluate.sh:30-32` builds `BiotiteDockQ(...)` without `parallel_io`, so it defaults to `True` (`pinder-src/src/pinder-eval/pinder/eval/dockq/biotite_dockq.py:226`).
3. The parallel reader uses `multiprocessing.get_context("spawn").Pool(...)` (`pinder-src/src/pinder-core/pinder/core/utils/process.py:17,33`).
4. A spawn worker re-runs the parent's main module from `ORIGINAL_DIR/<__file__>`, here `/tmp/m5-…/<stdin>`. No such file exists, so each worker dies at start-up. `Pool` replaces dead workers indefinitely and the submitted map never completes.

**Everything before `calculate()` worked.** The pool starts only inside `calculate()` (`evaluate.sh:30-32`), so lines 15-29 completed in every invocation. That means:
- `cmp-eval` read the native from `CMP_PRIVATE`, and its size and SHA-256 matched;
- it parsed the native's chains;
- it found all 50 `model_<r>.pdb` files under `CMP_ARM_OUT`.

**Why nothing caught this earlier:** `evaluate.sh` had never run before evaluate.
- In comparison mode, reproduce runs only `run_anchors.sh` for A0 (`run7/agent/harness/run_anchors.sh:6-37`), which never calls the evaluator. `SCHEMAS.md:159` says so.
- The non-comparison path `run_evaluation.sh:41` would also call `evaluate.sh`, and it would hang the same way.

## B. Where the cause lies

**In the harness.** The defect is `run7/agent/harness/evaluate.sh:11` (code given to Python on standard input) combined with `evaluate.sh:30-32` (`BiotiteDockQ` left at `parallel_io=True`). The harness agent wrote this file. It is sealed in `control/arms_seal.json` as harness, not pipeline code.

**Not in the design.**
- The arm commands, inputs and arm timeouts were fine: every arm command exited 0 within 1.2 to 39 s.
- s27's `evaluator.spec` (`comparison.json:373-385`) did not say how to invoke the evaluator, and it did not need to.
- The 900 s evaluator timeout only set how much time each hang cost. It did not cause the hangs.

**Not in the comparison mechanism.**
- `cmp_wrap.py:284-285` runs `bash <shared>/harness/evaluate.sh` as `cmp-eval` with working directory set to the shared run directory. `SCHEMAS.md:176` (step 3) requires exactly that. The working directory only supplies the `/tmp/m5-…/` prefix of the missing path. No working directory contains a file named `<stdin>`, so the failure does not depend on the part user, `env -i`, `HOME` (`ehome/`), `TMPDIR` (set by `evaluate.sh:9` itself), the network rule or permissions.
- Every mechanism step the arm and evaluator needed was evidently working:
  - `comparison-users` returned rc 0 (`control/receipts/0009-comparison-users.json`);
  - private data was readable by `cmp-eval` with a matching checksum (as shown above);
  - arm outputs were readable by `cmp-eval`;
  - `cmp-arm` reached the GPU: A1 and A3 recorded `gpu_busy_s` 0.56 to 4.85 (`comparison_compute.json:35,61,100,113,139,152`);
  - the wrapper killed the hung pool on each timeout, and the next invocation started normally;
  - `comparison-private-remove` returned rc 0 (`0037`).
- No line of `cmp_wrap.py` does anything the arm or the evaluator needed done differently. I found no mechanism defect.

**Not in the box.** The same code fails the same way on any box. The A10 only affects arm walls, and those were short.

**A secondary harness issue that did not cause the failures.** `run7/agent/harness/setup.sh:50-51` builds `megadock-gpu` with `-arch=sm_90`, following the seed brief, which prescribes `SM_VERSIONS=sm_90` (`science/s28/FIXTURE_BRIEF.md:338`). The box was an A10, which is sm_86. The GPU arms still exited 0, but s28 found their scores differing from the CPU arms and from each other (`science/s28/ASSESSMENT.md:76-83`). I did not verify whether the kernels failed silently. This issue would make A1 and A3 values suspect. It did not cause any timeout.

**A weakness in the pipeline contract, not a defect.** `SCHEMAS.md:159-181` runs no evaluator check before the first invocation and has no early stop on repeated evaluator timeouts. The pipeline therefore spent the whole budget on 13 identical hangs. The code behaves as the contract says. The gap made the failure expensive but did not cause it.

## C. Does s28's design change the cause, and does it fit its budget?

**The cause: yes, s28 targets it directly.** s28's `fixture_design.json:136` adds `evaluator.spec.invocation`: construct `BiotiteDockQ` with `parallel_io=False`, and run the evaluator from a regular file rather than standard input. s28's brief section repeats this (`FIXTURE_BRIEF.md:313` ff.) and adds a GPU build for the box's own compute capability. Either change alone removes the hang.

Two residual risks remain:
1. The fix depends on the next harness agent following the spec text. Nothing in the pipeline checks it.
2. The evaluator has never run to completion on this route, so later lines (`evaluate.sh:33-38`, for example the `model_name` reindex) are untested here.

s28 also lowers `evaluator.timeout_s` to 180 and `timeout_s` to 300, and sets `warmup` 0 (`fixture_design.json:139-145`). Those settings limit the cost of a repeated hang but do not prevent one.

**The budget.** s28 plans 6 × 4 × 4 = 96 invocations with `budget_s` 16,200. run7's measured costs (receipts `0011`-`0036`, `0009`, `0010`):
- **Fixed cost outside the parts:** each `comparison-job` takes 23 to 31 s. Each `comparison` command adds about 41 to 49 s beyond its arm and evaluator walls (for example `0012`: 961 s against 921.0 s of parts). Together that is about 66 to 80 s per invocation.
- **Arm walls:** CPU arms (A0, A2) 2.5 to 39 s, GPU arms (A1, A3) 1.6 to 6.4 s, mean about 10 s.
- **Before the first invocation:** users and versions together take about 93 s of budget (`0009` 49 s, `0010` 44 s).

The fit depends on what the evaluator costs:

| scenario | per invocation | 96 invocations | fits 16,200 s? |
|---|---|---|---|
| run7's measured cost (evaluator hangs to 900 s) | about 970 to 1,020 s | about 95,000 s | **no**, about 16 fit |
| hang recurs, s28's 180 s cap | about 75 + 10 + 181 ≈ 265 s | about 25,500 s | **no**, about 60 fit |
| fix works, evaluator about 3 s (run4's figure, per s28; I did not recheck it) | about 88 s, at most about 122 s | about 8,500 s, at most about 11,700 s | yes |
| fix works, evaluator `e` s | about 85 + `e` | | yes while mean `e` is below about 82 s |

- **On an A10:** the arm walls above were measured on this A10.
- **On an H100:** the fixed cost is wrapper and SSH time and does not depend on the box. CPU arm walls are similar (s28 cites 9.0 to 14.5 s for run6 on an H100) and GPU walls are no longer. The table therefore holds for both boxes. The cost is about USD 3.6 expected and USD 6.3 worst on an A10, against USD 9.2 and USD 16.1 on an H100 (s28 §D). I did not recompute those prices.

**Verdict: at risk.** At run7's measured invocation cost the plan does not fit. It fits with room only if the evaluator fix holds and the evaluator's unmeasured wall averages below about 80 s.

## D. Can a rerun succeed as s28 designed it?

**Yes, without a pipeline fix.**
- The cause is a harness defect.
- The comparison mechanism showed no defect.
- s28's design and brief require the exact correction, and also correct the GPU build target.

The rerun succeeds if the regenerated `evaluate.sh` runs the evaluator from a file with `parallel_io=False`, and fails again if it does not.

**Recommended for the operator, not required:**
1. **Before launch:** confirm that the s28 brief's lines 1-310 are byte-identical to the seed brief, as s28 itself asks (`ASSESSMENT.md:148`).
2. **After the harness is generated and before box time is spent:** check that the new `evaluate.sh` has no `python -` or heredoc form and does pass `parallel_io=False`. The sealed harness bytes are in `A/harness/` and `C/arms_seal.json`, so this is a quick read.
3. **Pipeline guards for later:** these are improvements to the contract (`SCHEMAS.md:159-181`), not preconditions for this rerun:
   - an evaluator smoke run on A0's reproduce output;
   - an early stop after N consecutive evaluator timeouts.
4. **Main run:** pin the box type to the one the fixture run lands on, because of the per-box GPU build (s28 §D, "Box-identity constraint").
