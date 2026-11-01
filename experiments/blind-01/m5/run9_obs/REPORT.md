Run9 observation, 2026-11-01 UTC. Run still active. Evidence read locally; no workloads, box access, network requests or git commands performed. Writes confined to `run9_obs/`. Paths below relative to `experiments/blind-01/m5/` unless prefixed `dut/`; repository root resolves to `../../..` from this checkout, despite prompt's two-level description.

1. All intake items measured; scored anchor comfortably exceeds threshold.

| Intake item | Published criterion/value | Measured | Interpretation |
| --- | ---: | ---: | --- |
| `dockq_acceptable_threshold` | DockQ ≥ 0.23 | 0.9775788581560528 | Pass; margin +0.7475788581560529 |
| `pinder_s_system_count` | 250; no tolerance | 250 | Exact agreement; difference 0 |
| `pinder_s_apo_paired_count` | 93; no tolerance | 93 | Exact agreement; difference 0 |

Evidence: [intake items](../run9/agent/intake/anchors.json), [scored items](../run9/agent/results/reproduce/anchors_scored.json), [measured output](../run9/agent/results/reproduce/out/anchors_measured.json), [details](../run9/agent/results/reproduce/out/anchors_details.json). Scoring records one passed anchor, one total anchor, two references. References have `passed: null`, correctly. [Reproduce stage](../run9/control/stages/reproduce.json) records PASS and `run_valid: true`.

Threshold is acceptance convention, not independently published FroDock performance value. Harness reports maximum DockQ across all 800 poses: best of 50 per job, then best across 16 jobs. Maximum comes from `1nr5__A1_P07547--1nr5__A2_P07547`, holo, `model_1`, rank 1; Fnat 0.9809523809523809, iRMS 0.31775161623954773 Å, LRMS 0.6186391711235046 Å. Direct read of [metrics CSV](../run9/agent/results/reproduce/out/results/frodock_metrics.csv) confirms value and exactly 800 selected PINDER-S rows, 16 jobs, 50 rows per job.

Comfortable margin applies to this scored maximum. Other jobs vary: 10/16 top-ranked poses and 15/16 best-of-50 poses meet threshold. `1dtd` apo best DockQ is 0.048648813108013854; `1aua` apo top-ranked DockQ is 0.22771144932822177, slightly below threshold. Passing anchor therefore establishes existence of acceptable poses within selected workload; it establishes neither universal recovery nor benchmark-wide performance reproduction.

2. Published quantity measured; benchmark scale reduced.

[Harness command](../run9/agent/harness/run_command.sh), lines 85–120 and 176–184, invokes FroDock prediction through PINDER runner, then published `pinder_eval`; actual pose scores supply DockQ, Fnat, iRMS and LRMS. Counts come from full release index, filtering `pinder_s` and paired `apo_R`/`apo_L` flags. [Anchor parser](../run9/agent/harness/run_anchors.sh), lines 95–160, derives reported values from command log and metrics, rather than copying intake values. Thus quantities match intake definitions, with maximum-over-poses interpretation above.

[EXECUTION.json](../run9/agent/intake/EXECUTION.json) fixes first eight lexicographically sorted paired-apo systems, both holo and apo: 16 jobs, 50 poses each, eight MPI ranks, CPU execution, zero exposed GPUs. Full benchmark contains 250 systems, including 93 paired-apo; workload covers 8/93 paired-apo systems (8.60%), or 8/250 benchmark systems (3.20%). Reference counts inspect full index; docking does not cover full benchmark. AAV redocking cases 6IHB/6JCQ/6JCS excluded explicitly. Brief permits small initial calibration, so reduction is disclosed calibration scope; it cannot support full-benchmark claims. `scale: reduced` refers to scientific workload coverage, not resized molecules.

[Baseline record](../run9/agent/intake/baseline.json), `published_configuration`, says `n_solutions` has no published default: 50 is preregistered experiment choice, not independently published scale. No published numerical FroDock benchmark score was located during intake. Executed source also includes recorded adapter repairs in [patch](../run9/agent/harness/pinder_frodock_fixes.patch): enum/API fixes, input staging/path resolution, binary-path joining and output glob copying. Final harness additionally restores blank ligand HETATM chain labels before scoring. Calling executed code byte-for-byte unchanged published source would be inaccurate.

[Owner-approved materials brief](../intake_mirror/BRIEF_run5.md), opening scientific scope and Materials section, preserves FroDock provenance `unverified_mirror`. Passing score threshold and matching composition counts do not authenticate software/scoring bytes against original distribution. Claims about original remain conditional on unresolved identity.

3. Attempts failed after full docking, for two different reasons.

| Attempt / evidence | Docking interval, UTC | Docking elapsed | Receipt wall | Failure/result |
| --- | --- | ---: | ---: | --- |
| [0112 log](../run9/agent/results/reproduce/0112-anchors.log), [receipt](../run9/control/receipts/0112-anchors.json) | 03:26:27.199–04:41:48.107 | 4,520.908 s | 5,091 s | Output-format failure in evaluator |
| [0114 log](../run9/agent/results/reproduce/0114-anchors.log), [receipt](../run9/control/receipts/0114-anchors.json) | 05:02:47.080–06:17:42.186 | 4,495.106 s | 6,159 s | Repair's atom-count assertion failed |
| [0116 log](../run9/agent/results/reproduce/0116-anchors.log), [receipt](../run9/control/receipts/0116-anchors.json) | 07:13:52.222–08:29:28.603 | 4,536.381 s | 7,347 s | Scoring succeeds; anchors finish 08:30:56 |

Every log contains 16 `Running FroDock (50 solutions)` starts, `Success! Finished docking 16 systems`, and `PREDICT_EXIT=0`. Thus both reruns repeated full docking workload. First two attempts did not finish scoring; third did. Current command moves earlier results into history and creates fresh results before prediction (lines 50–82), preventing `force: false` from reusing existing poses.

Attempt 1: `pinder_eval` raises `ExpectedChainsNotFoundError`, reporting `_L_R != R_L`: blank-chain ligand HETATM records create third chain. Docking itself completed successfully. First repair restores blank ligand HETATM chain fields while preserving original decoys. Attempt 2: added validation assumes parsed output atom count equals input receptor plus ligand counts; aborts at `1dtd` apo `model_1.pdb`, before evaluator. Second repair removes unsupported count/boundary assumption and locates ligand suffix using existing L labels. Comments identify alternate-location handling as possible reason counts differ; exact biological/file-reader reason remains unknown from inspected evidence.

Repair evidence: [first call record](../run9/agent/wf/agents/0006-anchors-repair/codex-1.jsonl), completed file changes at JSONL lines 187 and 202; [second call record](../run9/agent/wf/agents/0007-anchors-repair/codex-1.jsonl), file change at line 105, saved-output validation at line 170; accompanying [first reply](../run9/agent/wf/agents/0006-anchors-repair/reply.txt) and [second reply](../run9/agent/wf/agents/0007-anchors-repair/reply.txt). Final successful log reports `CHAIN_LABELS_RESTORED models=100 atoms=2700` and `EVAL_EXIT=0`. Failure classification therefore `mixed`: output format, then script error; no evidence these two failures came from docking computation.

4. Full output fetch explains long uploads and freeze.

Local frozen copy measured during observation: `run9/agent/results/reproduce/out/` contains **2,152,814,259 regular-file bytes**, **4,238 regular files**; 2.153 decimal GB / 2.005 GiB. `du -B1 -s` reports **2,162,319,360 allocated bytes**. `du -B1 --apparent-size -s` reports **2,152,814,259 bytes**. File-size sum independently matches apparent size. File count from `find ... -type f | wc -l` independently matches metadata traversal. Size bucket: `1gb_to_10gb`.

| Subdirectory | Regular-file bytes | Files |
| --- | ---: | ---: |
| `out/tmp/` | 1,104,887,340 | 1,792 |
| `out/run_command/` | 697,738,676 | 1,611 |
| `out/results/` | 344,225,500 | 803 |
| `out/anchors_logs/` | 3,341,275 | 5 |
| `out/setup/` | 1,791,278 | 23 |

Four loose root files complete total. `out/run_command/history/` retains two earlier results trees; `out/tmp/` retains temporary docking products from reruns. First anchors repair introduced `TMPDIR=$PWD/out/tmp` and preservation of whole prior results tree; these changes explain growing fetch payload, beyond final 800 poses. Remote `reproduce-out/` freeze is separate sibling, not nested in fetched `out/`, so freeze does not itself double fetched payload.

| Command / receipt | UTC interval | Wall |
| --- | --- | ---: |
| [0113 upload](../run9/control/receipts/0113-upload.json) | 04:53:37–05:02:38 | 541 s |
| [0115 upload](../run9/control/receipts/0115-upload.json) | 06:46:34–07:13:41 | 1,627 s |
| [0117 reproduce-freeze](../run9/control/receipts/0117-reproduce-freeze.json) | 09:16:08–10:01:18 | 2,710 s |
| [0118 profile upload](../run9/control/receipts/0118-upload.json) | 10:01:19–10:46:42 | 2,723 s |

All receipts report rc 0 and fetched true. `dut/pipeline/m5/pipeline.js`, lines 178–235, passes `--fetch out` for every box command, including tiny script uploads; clears local destination before each fetch. `boxrun.sh`, lines 9–36 and 51–90, measures wall through command, polling, telemetry and recursive fetch, then writes receipt. Default fetch uses `scp -r`; up to five fetch attempts permitted. Exact transfer-only time, retry count and network bottleneck are unknown because receipts contain no phase timing.

Fetch dominance for these uploads/freeze is strong inference: commands upload small script content or copy 2.15 GB locally on box; two successive operations against same large output take almost identical 2,710/2,723 s, versus 11–24 s uploads before docking. Successful anchors script ends at 08:30:56, while receipt ends 09:16:08: **2,712 s after script completion**, consistent with next two fetch-heavy commands. Thus these delays represent output retrieval overhead, not another docking search. This does not mean fetch dominates anchors invocation itself: third attempt spends about 4,633 s executing script versus 2,712 s afterward. Effective whole-fetch rate using current size and 2,723 s is about 0.79 MB/s; rate conflates bytes, per-file overhead, polling and possible retries, and is not measured link bandwidth.

5. Profiler command likely fits alone; full profile plus concurrency does not.

From [0118 receipt](../run9/control/receipts/0118-upload.json): upload starts with 15,745 s budget and consumes 2,723 s. Profiler starts about **30,178 s** into run, leaving **13,022 s**. Receipt budget/timestamps imply pipeline start about 02:23:44 UTC and ceiling about **14:23:44 UTC**, within whole-second resolution. U47 budget resolution appears in `pipeline.js`, lines 160–174, and `SCHEMAS.md`, Finish-first timing section. Intake's 7,200 s profile estimate does not set actual timeout.

Measured successful shared command costs roughly **4,600–4,650 s** (16 docking jobs plus scoring); docking alone consistently costs 4,495–4,536 s. Fixed `profile_nsys.sh` runs same `harness/run_command.sh` once under Nsight, then exports/summarizes. One comparable run plus unchanged fetch cost is about **7,350 s**, leaving roughly 5,670 s. Actual output grows again because command preserves prior results and adds another set of temporary products; proportional extrapolation from current bytes/files suggests fetch around **3,800–4,000 s**, hence total around **8,400–8,700 s** before unknown installation/finalization overhead. Profiler command including fetch therefore likely fits 13,022 s under observed runtime, but no completion is established.

Concurrency probe requires **three serial full command runs** before its optional 2- and 4-copy batches (`concurrency_probe.py`, lines 115–135). Three singles alone need roughly **13,900 s**, already exceeding time available at profiler start, before profiler execution or any fetch. After profiler/fetch, likely only 4,300–5,700 s remain: enough for approximately one single, not three. Batch budget guard does not skip required singles. CPU baseline also cannot supply expected CUDA MPS client connections; MPS fallback could add another full invocation. Even with no MPS and both batches skipped, complete calibration unlikely to fit. `profile_fits_time_left: no` describes full sequence; profiler invocation alone likely fits.

Independent gate issue may prevent probe from starting: CPU-only command exposes no GPUs and receipts show zero GPU busy time. Fixed summarizer assigns unaccounted time to `other host time`; if CUDA activity remains negligible, row approaches 100% of wall. `pipeline.js`, profile validator around lines 448–452, rejects any row within 2% of total wall as process wrapper; probe runs only after validation passes. Thus profiler can finish within budget yet profile fail numeric gate, with no probe. This is source-based prediction, not observed outcome.

At final local check, profile directory contains only empty `0118-upload.log`; no profiler or concurrency receipt exists. Live remote progress, eventual profiler overhead, final profile validity and actual probe outcome remain **unknown**. No missing receipt treated as failure or completion.
