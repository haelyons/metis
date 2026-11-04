# Sealed operator predictions: shakedown-m5 run20 (isolation re-probe after the second fix round)

Written and committed before launch. Public, non-blind. run20 re-runs run17's design (`cmp20/design.json` is byte-identical to `cmp17/design.json`) on the code of the second U57/U58 fix round (contract f0edeb93 and the fix commit after it), with the probe harness `cmp20/harness/` changed from `cmp17/harness/` after run17's result, as follows (every check run17 had is kept unless named here):
- `command_files_readable` now covers every box command file of the evaluate stage (`NNNN-<name>.sh|log|gpu|rc` numbered after `reproduce-freeze`), not only names holding "comparison"; run17 found the `comparison-users` files readable in every part.
- The arm's `read_writable_list` control and `unlisted_writable_dirs` check are removed (the writable list is not readable by part users, so both failed in run17 as probe artefacts). In their place each part records the directories it can write (`writable_dirs`, info), plants its residue file in every one of them, and the residue checks search the whole box (`/`, `/tmp`, `/var/tmp`, `/dev/shm`, `/dev/mqueue`, `/run`) by name instead of three directories.
- New: `schedule_cron` and `schedule_at` (a part installs a crontab or an at job; success is a leak), `scheduled_residue` (files such a job would create), `scheduling_tools` (info).
- Parts also leave a message queue and a semaphore array, besides the shared-memory segment; the IPC residue check lists all three kinds.

## Predictions (probabilities mine; intervals 80%)
| Item | Prediction |
|---|---|
| intake, reproduce, evaluate | PASS 0.85, 0.85, 0.8 |
| invocation status | p1 and p2 `ok`, every p3 `invalid` with the evaluator skipped, 0.85 |
| `command_files_readable` | none in every part 0.85 |
| `schedule_cron`, `schedule_at` | denied in every part 0.85 (crontab present on the image 0.8; at absent 0.6) |
| residue checks (arm, eval, scheduled) | none in every part 0.75; if not, the most likely cause is a writable directory on a mount the cleanup's list covers but `find -delete` cannot clear (`/dev/mqueue`) |
| positive controls | none failed 0.8 |
| every recorded leak count 0 on ok invocations | 0.6; a probe artefact 0.25; a true leak 0.15 |
| K6, K7 (leaks vs 0) | p1, p2 supported 0.6; p3 void |
| K1, K4 | void (p3 missing) 0.85 |
| overhead per invocation outside the parts' walls | median 31 s, interval [20, 60] (run17: 31 s) |
| box | USD 0.3 to 1.5 (run17: USD 0.42) |

## What would change my mind
- Any true leak: fix and repeat before the fixture run (s27).
- Everything clean: the comparison mechanism is ready for the fixture run, subject to the narrow Codex check of the second fix round.
