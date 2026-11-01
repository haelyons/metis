Run9 finished-run diagnosis, 2026-11-01 UTC. Local evidence only; no workloads, box access, network requests, git commands, or changes outside `run9_diag/`. Large trees measured through metadata; no scientific datasets, decoy trees, SQLite database, or binary traces read wholesale. Paths below relative to `experiments/blind-01/m5/`, except `dut/...`, relative to repository root. Actual repository-root path from working directory is `../../..`, rather than prompt's two-level description.

1. Fixed profiler's summariser caused rc 1.

[Profile receipt](../run9/control/receipts/0119-profile.json) records `rc:1`, `timed_out:false`, `overrun:false`, `fetched:true`, wall 9,728 s, budget 13,022 s. [Stage receipt](../run9/control/stages/profile.json) records FAIL/parse. This classification identifies pipeline branch, not scientific workload failure.

Direct evidence establishes successful shared command:

- [Profile command log](../run9/agent/results/profile/out/run_command/run_command.log), lines 11115–11117: `Success! Finished docking 16 systems` at 12:18:25.028, `PREDICT_EXIT=0`, `CHAIN_LABELS_RESTORED models=100 atoms=2700`.
- Same log, lines 16192–16201: scoring finishes at about 12:19:41, then `EVAL_EXIT=0`. Final [run_command.sh](../run9/agent/harness/run_command.sh), lines 183–185, checks this status and exits 0.
- [baseline.log](../run9/agent/results/profile/out/profile/baseline.log) tail confirms `EVAL_EXIT=0`, then Nsight collection and generated `baseline.nsys-rep`. Report exists, 102,508,216 bytes; SQLite export exists, 1,271,185,408 bytes.
- [stats.log](../run9/agent/results/profile/out/profile/stats.log), lines 2–12, reports three `PROCESSED (EMPTY RESULTS)` reports and explicit skips: no CUDA kernel data, GPU memory data, or CUDA trace data. All three `stats_*.csv` files exist but contain **zero bytes**.
- [Top-level profile log](../run9/agent/results/profile/0119-profile.log), line 25, ends `invalid profiler output`. No `infra.json` found under run9.

Exact source path to failure: `dut/pipeline/m5/profile_summarise.py:57` consumes kernel report through `report_rows`. Lines 22–27 recognize absent activity only when CSV **does not exist**. Here CSV exists but is empty. Lines 28–43 find no header; lines 45–46 find no `SKIPPED` inside empty CSV and raise `ValueError("missing CSV header")`. Lines 105–107 suppress exception details, print observed generic message, return 1. `profile_nsys.sh:139–141` deliberately disables ERR infrastructure trap before calling summariser, so rc 1 propagates without infra marker. Collection/export had already succeeded.

Additional compatibility defect: missing-file guard expects `CUDA memory data` and `CUDA API data`, while installed Nsight 2025.3.1 says `GPU memory data` and `CUDA trace data`. Fix must cover actual empty-file behavior and actual skip wording, not only change file-existence test.

CPU-only execution explains missing CUDA activity. Harness lines 22–27 expose zero GPUs and fix FroDock CPU/MPI parameters. All 39,680 profiler telemetry samples report 0% GPU utilization. Earlier logging `TypeError` messages and evaluator missing-system ERROR messages are nonfatal here: both subprocesses subsequently return 0. Initial apt package lookup failure at profile-log line 6 also recovered: lines 7–12 install pinned fallback Nsight package successfully.

Resource exhaustion unsupported as cause. [Box probe](../run9/agent/results/probe/probe.json) reports 1,038,620,045,312 available home-disk bytes, 231,924,764 kB memory, 26 CPUs, one H100. These are initial inventory, not peak-use measurements; peak disk/RAM remain unknown. Successful command/export and deterministic parser failure establish proximate cause without inferring peak resources. Fetch succeeded and happened after remote rc was written (`boxrun.sh:67–90`); it cannot explain remote rc 1.

2. Failure occurred late in remote command: final summarisation, after docking, scoring, collection and export. Fetch consumed approximately 40% of receipt wall.

| Evidence / phase | UTC or duration |
| --- | --- |
| Profile upload receipt 0118 | 10:01:19–10:46:42; 2,723 s, separate from 9,728 s |
| Profile receipt 0119 | 10:46:42–13:28:50; 9,728 s |
| First docking job | 10:47:05.978 |
| Docking complete | 12:18:25.028 |
| Last scoring message, then EVAL_EXIT=0 | 12:19:41.341 |
| Inner command measured wall | 5,621.4601993279975 s |
| Local fresh fetched `out/` directory birth | 12:24:04.956158848 |
| Last root file `out/probe.json` write completes | 13:28:47.721642612 |
| Operation log fetch completes | 13:28:50.594592666 |

Inner wall comes directly from [raw_wall_s.json](../run9/agent/results/profile/out/profile/raw_wall_s.json), which excludes installation, Nsight finalization, CSV export and fetch (`profile_nsys.sh:114–130`). Profiler sampler spans monotonic 30265.174156576–36042.922147891: 5,777.748 s. Last sample falls 154.051 s after inner command ends, consistent with report finalization. Exact summariser failure timestamp is **unknown**; it occurred after successful export and before local fetch began, approximately 12:23–12:24. `late` describes final phase of remote command, not position within receipt including subsequent fetch.

Fetch timing independently recoverable from local filesystem metadata: `stat` reports fresh local `out/` birth at 12:24:04.956 and final root-file completion at 13:28:47.722. Pipeline clears destination before command (`pipeline.js:189–195`); boxrun serially waits for remote rc, fetches `out/`, then fetches command log (`boxrun.sh:73–90`). Observed `out/` retrieval interval therefore **3,882.765 s / 9,728 = 39.913%**. Through receipt end: about 3,885.044 s, 39.937%, including final log/transport overhead. No explicit transfer-phase timer exists; exact network-only time and retry count remain unknown. Metadata and serial control flow securely place share in **25–50%** bucket. Remaining pre-fetch interval is about 5,842.956 s, including command plus profiler/setup/export/polling overhead. Treating all 9,728 s as workload runtime would overstate runtime substantially.

Metadata measurements: profile `out/` has 5,951 regular files; `du -B1 -s` gives 4,448,432,128 allocated bytes and `du -B1 --apparent-size -s` gives 4,435,111,079 bytes. `du -h -d 2` shows roughly 1.6 GiB temporary products, 1009 MiB command/history outputs, 330 MiB current results, 1.3 GiB profile artifacts. Whole-out fetch adds substantial cost. It remains separate from failure source.

3. Shared command succeeded before profiling; anchors use identical scale.

[Successful anchors log](../run9/agent/results/reproduce/0116-anchors.log), lines 11116–11118, records docking success, prediction exit 0 and chain restoration. Lines 16202–16203 explicitly record `EVAL_EXIT=0` and `== run_command.sh exit status 0`. Anchors finish 08:30:56. [0116 receipt](../run9/control/receipts/0116-anchors.json) records rc 0; [reproduce stage](../run9/control/stages/reproduce.json) records PASS and `run_valid:true`.

[run_anchors.sh](../run9/agent/harness/run_anchors.sh), lines 31–37, directly invokes `bash harness/run_command.sh`, propagates failure, then parses saved measurements. Fixed profiler invokes same file through launcher (`profile_nsys.sh:116–130`), from same working directory, with no workload/environment rewriting. Final harness fixes eight selected systems, holo and apo, 16 jobs, 50 poses each, eight MPI ranks, eight scoring workers, GPU count zero (`run_command.sh:9–30,99–107`). Anchors log line 5 and profile baseline log line 7 print matching configuration. Both measure 800 decoys. This is same reduced benchmark scale, not full 250-system docking.

Call records support repair history: [0006 reply](../run9/agent/wf/agents/0006-anchors-repair/reply.txt) describes restoring blank ligand HETATM chain labels; [0007 reply](../run9/agent/wf/agents/0007-anchors-repair/reply.txt) removes erroneous atom-count assumption and reports validation across 800 saved decoys. [0007 prompt](../run9/agent/wf/agents/0007-anchors-repair/prompt.md) documents second and final anchors repair and scope. Journal lines 19–22 record those calls; lines 24–25 record profile phase and failure with no intervening repair call. Earlier command failures were repaired before successful 0116; they do not explain later profiler rc 1.

4. Top-level log tail does not expose specific cause; harness repair would not fix it.

The **25-line top-level profile log** supplies only generic `invalid profiler output`, without traceback, CSV filename, or skip messages. Accordingly `log_tail_has_cause:no` means this operation-log tail does not reveal empty-CSV parser defect. Locally fetched detailed `out/profile/stats.log` plus summariser source do reveal cause. Baseline tail shows successful workload and generated report, rather than harness error.

Setup/anchors repair path reads last 200 lines of operation log and permits changes only to scoped harness scripts (`pipeline.js:260–298`). A comparable repair restricted to `run_command.sh` would neither repair trusted `report_rows` nor change profile gate. Adding GPU work, fake stage timings, or profiler-output rewriting to harness would violate canonical-command rules (`pipeline.js:238`). Fixed profiler needs correction; extra harness repair or prompt rule does not address observed defect.

5. Smallest coherent fix: trusted profiler compatibility fix plus narrowly consistent profile gate.

First fix `profile_summarise.py` to recognize **explicit Nsight absent-activity skips for existing empty CSVs as well as missing CSVs**, matching report-specific wording above. Return zero only with corresponding explicit skip evidence; malformed/empty reports without such evidence must still fail. Include useful parser reason/report name in failure log. This removes observed rc 1 without rerunning or altering scientific workload; saved artifacts suffice for corrected postprocessing. No such processing or patch applied during this diagnosis.

**Parser-only patch would not finish profile PASS.** With three confirmed absent CUDA reports, current summariser produces four zero-duration CUDA rows and `other host time = 5,621.4601993279975 s` (`profile_summarise.py:57–80`). `pipeline.js:432–435` rejects any stage within 2% of total wall as process wrapper. Host remainder equals 100%, so next outcome would be numeric FAIL. `SCHEMAS.md:73–84` documents both remainder construction and contradictory wrapper gate. Nonempty zero-util telemetry is valid (`SCHEMAS.md:76`); GPU utilization itself is not failing condition.

Smallest finish-capable change therefore also makes validator accept trusted, explicitly evidenced no-CUDA host remainder for CPU-only command, retaining honest `kind:other`, GPU seconds null, zero CUDA durations and measured total wall. Keep wrapper rejection for actual process-wrapper rows and unsupported timing claims. Validate no-activity provenance rather than accepting arbitrary full-wall rows by name. Do not split host remainder into invented phases or label it measured GPU compute. If policy requires internal CPU phase timings, fixed profiler must instead collect real CPU phases; larger change than narrow no-CUDA support.

Thus status `smallest_fix:profiler_fix` denotes trusted profiling/postprocessing path plus matching validator behavior. `profile_repair`, `harness_prompt_rule`, `fetch_scope`, and `resources` cannot resolve both demonstrated blockers alone. Narrowing fetch scope would save wall time, but is separate improvement.

After successful validation, optional concurrency calibration can still lack budget: observed receipt leaves 3,294 s of its supplied budget, shorter than previous successful shared run (roughly 4,600–4,650 s). Current pipeline treats ordinary optional-probe timeout/failure as unavailable concurrency and can still return profile PASS (`pipeline.js:458–476`; `SCHEMAS.md:99`), except explicit zero-budget branch. No successful concurrency measurement or later scientific-stage completion can be inferred. Recommended change concerns finishing profile honestly, not guaranteeing remaining experiment finishes.
