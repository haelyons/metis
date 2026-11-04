# runs 17 to 20: outcome against sealed predictions (predictions/run17-19.md 94d926b6, predictions/run20.md 97d0189e)

Sealed comparison isolation probe (public, non-blind). runs 17 to 19 on code 3895bf5f (first U57/U58 fix round); run20 on e3ebd33c (second fix round). Every pipeline exited 0, every box was torn down, every push verified. Box spend for the four runs USD 1.67 (blind-02 ledger), against USD 5 to 11 predicted for runs 17 to 19 and USD 0.3 to 1.5 for run20.

## run17 (commit 7b676faf): evaluator, 3 inputs, 18 invocations
| Prediction | Outcome | Hit |
|---|---|---|
| intake, reproduce PASS 0.85 each | PASS, PASS | yes |
| comparison-users passes 0.75 | passed | yes |
| evaluate PASS 0.65 | PASS | yes |
| p1, p2 ok 0.85; every p3 invalid, eval skipped 0.85 | as predicted | yes |
| every leak count 0 on ok invocations 0.65 | **no**: `command_files_readable` in all 18 arm and 12 evaluator parts (the `comparison-users` command's own `.sh`, `.log`, `.gpu`); a true leak, also found by the Codex re-review (its finding 5) | no |
| no positive control failed 0.8 | **no**: arm `read_writable_list` and `unlisted_writable_dirs` failed (PermissionError on `profiler/cmp_writable.json`, not readable by part users); a probe artefact | no |
| K1 void 0.7 | void | yes |
| K2 p1, p2 supported 0.85 | supported | yes |
| K3 p1, p2 not supported or inconclusive 0.6; p3 not supported (missing_values) 0.85 | p1, p2 supported (estimate about 0.02 s against margin 7.3); p3 not supported, missing_values | p1, p2 no; p3 yes |
| K4 void 0.7 | void | yes |
| K5 p1, p2 supported 0.8 | supported | yes |
| K6, K7 p1, p2 supported 0.65 | not supported (leaks 1) | no |
| overhead median 45 s [25, 90] | 31 s (comparison-job median 7 s, comparison median 28 s, inside-part walls median 3.85 s) | yes |
| box USD 2 to 5 | USD 0.42 | no: below |

## run18 (commit 158355c0): no evaluator, p1 and p3, 8 invocations
| Prediction | Outcome | Hit |
|---|---|---|
| comparison-users creates `cmp-arm` only, passes 0.8 | as predicted | yes |
| arm parts as `cmp-arm`, `command_files_readable` none 0.85 | `cmp-arm`, sudo and job listing denied, no protected writes; `command_files_readable` leak as in run17 | no |
| p1 ok, p3 invalid 0.85 | as predicted | yes |
| evaluate PASS 0.75 | PASS | yes |
| box USD 1.5 to 3.5 | USD 0.37 | no: below |

## run19 (commit 4a8c47f6): setup leaves a copy of the private file in the shared run directory
| Prediction | Outcome | Hit |
|---|---|---|
| reproduce PASS 0.85 | PASS | yes |
| evaluate FAIL infra at comparison-users step 7, before any invocation 0.85 | FAIL infra at `comparison-users` (rc 1, "a copy of private data lies outside cmp-private"), no invocation | yes |
| box USD 1 to 2.5 | USD 0.39 | no: below |

## run20 (commit 1de276bf): re-probe after the second fix round, 18 invocations, 30 probe files
| Prediction | Outcome | Hit |
|---|---|---|
| intake, reproduce, evaluate PASS 0.85, 0.85, 0.8 | PASS, PASS, PASS | yes |
| p1, p2 ok; every p3 invalid, eval skipped 0.85 | 6 + 6 ok; 6 invalid, eval skipped | yes |
| `command_files_readable` none 0.85 | none in all 30 | yes |
| `schedule_cron`, `schedule_at` denied 0.85; crontab present 0.8; at absent 0.6 | denied in all 30 (crontab refused; `at` not installed) | yes |
| residue (arm, eval, scheduled) none 0.75 | none in all 30 | yes |
| no positive control failed 0.8 | none failed | yes |
| every leak count 0 on ok invocations 0.6 | 0 | yes |
| K6, K7 p1, p2 supported 0.6; p3 void | as predicted | yes |
| K1, K4 void 0.85 | void | yes |
| overhead median 31 s [20, 60] | 30.3 s (comparison-job median 8.0 s, comparison median 29.5 s, inside-part walls median 7.2 s) | yes |
| box USD 0.3 to 1.5 | USD 0.49 | yes |

Totals run20: supported 12, not supported 1 (K3 p3, missing_values), void 6.

## Reading
- The one true leak (run17, run18) is closed on the box in run20; the stray-copy check (run19) works.
- Box spend was overestimated four times out of four (short parts; one box per run under 15 minutes).
- A narrow Codex check of the second fix round (review57c) confirmed every earlier finding fixed and found two defects in its diff, neither exercised on a fresh box: an existing `cron.allow` or `at.allow` would override the deny lists, with scheduled jobs removed only after the kill; and the users step's mode-600 exemption matched any top-level `[0-9]*-*` file. Contract 2151b52b; third fix round follows.
