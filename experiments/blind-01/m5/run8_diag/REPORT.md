Run8 anchors failed first on runner control flow, then twice on insufficient execution time. CPU/MPI baseline made progress: five complete docking cases per later attempt, no complete 93-case run, no anchor measurements. Smallest recovery unit: runtime-based anchors budget, propagated into wrapper timeout. Full runtime and eventual scientific score remain **unknown**.

Diagnosis used saved local records and cached archive bytes only. No workloads, builds, package installs, box access, network, commits or pushes. Writes confined to `run8_diag/`. No credential files, `.keys` files or files under `~/.codex/` read. Historical records mention such paths; none followed.

**1. Failure point of each attempt.**

| Attempt | Receipt | Failure point | Classification |
| --- | --- | --- | --- |
| 1 | `0054-anchors`: rc 1, 39 s | First case, first VdW grid: generated Python runner treats legacy success-path exit 1 as fatal | `script_error` |
| 2 | `0056-anchors`: rc 124, 1,751 s receipt wall | Five cases complete; sixth case docking still running when outer 1,200 s timeout fires | `workload_too_long` |
| 3 | `0058-anchors`: rc 1, 2,170 s receipt wall | Same five cases complete; sixth case docking interrupted by newly added 1,100 s inner timeout | `workload_too_long` |

Attempt 1 decisive [log](../run8/agent/results/reproduce/0054-anchors.log), lines 53, 63, 66–70:

```text
Written output potential (VdW or Electrostatic) map: receptor_W.mrc
  Exit code:    1
  File "/tmp/m5-929bafad-0547-42d4-95e5-7844238cebb2/baseline-published/run_baseline.py", line 44, in <module>
    subprocess.run(command,cwd=work,check=True)
```

Final exception states grid command `returned non-zero exit status 1`. Fatal behavior belongs to generated [run_baseline.py](evidence/0054-run_baseline.py), line 44, invoked by [run_command.sh](evidence/0054-run_command.sh), line 14. `set -euo pipefail` propagates exception through `tee`; anchor parser never starts.

Why `script_error`: cached FroDock grid source explicitly calls `exit(1)` after writing VdW/electrostatic maps and finalizing MPI, source lines 269, 309, 320; see [numbered excerpt](evidence/native-grid-exit-excerpt.txt). Published PINDER [adapter](../run8/agent/intake/src__pinder-methods__pinder__methods__run__frodock__predict.py), line 142, uses `subprocess.run(cmd, shell=True)` without `check=True`. First map has complete 61×59×55 float32 payload: 792,804 bytes, matching MRC header. Later repaired runs consume same case successfully. Native program did return 1; evidence identifies runner's interpretation of documented-in-source behavior as stopping defect, rather than a failed docking computation. Initial `aa 4IN not found` warnings precede map write; warnings alone do not establish corrupt materials or explain unconditional success-path exit.

Attempt 2 decisive [log](../run8/agent/results/reproduce/0056-anchors.log), lines 5547, 5618–5619, 5624:

```text
CASE_WALL {"id": "1dv1__A1_P24182--1dv1__B1_P24182", "wall_s": 286.79252167799996}
Written ASA potential map: ligand_DS.mrc
STAGE_STATUS {"stage": "grid-ligand-DS", "returncode": 0}
COMMAND ["/usr/bin/mpirun", "-np", "8", "--use-hwthread-cpus", "../../../../baseline-published/frodock3_linux64/bin/frodock_mpi_gcc", "receptor_ASA.pdb", "ligand_ASA.pdb", "-w", "receptor_W.mrc", "-e", "receptor_E.mrc", "--th", "10", "-d", "receptor_DS.mrc,ligand_DS.mrc", "-t", "A", "-o", "dock.dat", "-s", "../../../../baseline-published/frodock3_linux64/bin/soap.bin"]
```

No following docking completion or traceback. [Receipt](../run8/control/receipts/0056-anchors.json): `"rc":124`, `"timed_out":true`, `"budget_s":1200`. Sixth scratch directory identifies case `1glj__A1_P0A6F3--1glj__B1_P0A6F3`; `dock.dat` remains zero bytes. [Reconstructed wrapper](evidence/0056-run_anchors.sh), line 7, directly invokes command with no internal timeout.

Attempt 3 [log](../run8/agent/results/reproduce/0058-anchors.log) ends at identical sixth-case docking command, then line 5625:

```text
Missing complete workload output: fixed 93-case baseline exceeded 1100-second execution allowance within the 1200-second anchors budget. Scale and published configuration preserved; see out/baseline.log and out/run-*/scratch/*/*.log.
```

[Final wrapper](evidence/0058-run_anchors.sh), lines 13–17, introduces `timeout --signal=TERM --kill-after=15s 1100s` and converts timeout status into exit 1. Thus [receipt](../run8/control/receipts/0058-anchors.json) has `timed_out:false`, despite actual workload interruption by inner timeout. Pipeline reports final `error_class:anchor` because wrapper exits 1; this is no numerical anchor rejection. See pipeline lines 347–365.

**2. Did baseline start and finish on GPU?**

No GPU workload launched. Every log's `CONFIG` reports `"gpu_count":0`, `"CUDA_VISIBLE_DEVICES":""`, `"mpi_np":8`, `"OMP_NUM_THREADS":"1"`. Intake [benchmark](../run8/agent/intake/benchmark.json), line 97, explicitly describes CPU/MPI FroDock. All three receipts report known GPU busy time 0. H100 availability and CUDA path checks do not establish GPU execution.

CPU baseline starts in all three attempts. Attempt 1 finishes first grid only. Attempts 2 and 3 each finish first five docking/pose-generation cases, including 100 merged `model_*.pdb` files per case: 500 models per attempt. Neither finishes sixth case, remaining 87 cases, or subsequent DockQ evaluation. Enum `workload_completed:partly` records completed CPU case items, not partial GPU execution or complete benchmark evaluation.

**3. Representative runtime, budget fit, budget source.**

[Named brief](../intake_mirror/BRIEF_run5.md), initial scientific instructions, prioritizes 93 paired-apo cases and asks for calibration; it supplies no numerical runtime for this workload. Materials section also establishes no docking runtime. [EXECUTION.json](../run8/agent/intake/EXECUTION.json) fixes 93 sorted cases, eight MPI ranks, 100 candidates per case; lines 38–39 explicitly set `runtime_evidence:null` because intake ran no workload. README's “around 10 minutes” on four CPU cores and “around 40 minutes” sequential concern unrelated antigen/antibody example, not 93-case PINDER-S run; [README](../run8/agent/intake/frodock_frodock3_linux64__README), lines 76–86. Intake line 50 expressly rejects treating that example as measured benchmark runtime.

Measured per-case times, from both logs at lines 1076, 2545, 3581, 4548, 5547:

| Case prefix | Attempt 2 seconds | Attempt 3 seconds |
| --- | ---: | ---: |
| `1a19` | 41.175 | 39.866 |
| `1aua` | 244.492 | 243.864 |
| `1ax2` | 261.128 | 261.525 |
| `1dtd` | 182.451 | 181.593 |
| `1dv1` | 286.793 | 286.065 |
| Five-case sum | **1,016.038** | **1,012.914** |

Five cases alone consume about 17 minutes, before evaluator. Attempt 2 empirically exceeds 1,200 s with sixth case unfinished. Budget therefore **too small**. Full 93-case runtime **unknown**. Mechanical five-case-average extrapolation gives roughly 5.2 hours before evaluation; this is a rough planning illustration, not representative full-run measurement, published runtime, or guaranteed sufficient timeout. Cases are first five sorted IDs, not a calibrated runtime sample.

Effective budget source is **intake_execution**: `EXECUTION.json.stage_budgets_s.anchors=1200`, line 43. [Pipeline](../../../../dut/pipeline/m5/pipeline.js) `executionTimeout`, lines 159–167, resolves intake override first, args second, defaults last. Pipeline default happens to equal 1,200; explicit intake entry wins. Intake calls caps prospective, not measured, and requires abort/report rather than reducing scale. [Schema](../../../../dut/pipeline/m5/SCHEMAS.md) lines 24–25 matches implementation. Repair retries keep original budget; adding repairs alone cannot make unchanged workload fit.

**4. Measured anchor values.**

**None.** No attempt log contains `MEASUREMENT`; fetched tree contains no `anchors_measured.json`, metrics CSV or leaderboard CSV; no `anchors_scored.json` exists. Initial parser is unreachable after exception. Later parser runs only after canonical command exits successfully, which never happens. Attempt 3 also removes stale measurement file before execution.

Intake [anchors.json](../run8/agent/intake/anchors.json) has one scored threshold (`dockq-acceptable`, DockQ ≥ 0.23) and two references (250 PINDER-S cases; 93 paired-apo cases). Partial poses, `CASE_WALL` timings and setup counts are not written anchor measurements. No evidence any item passed or failed numerically. Pipeline exits before scoring, leaving counts null as schema specifies.

**5. Fetched output size and receipt wall time.**

Final `run8/agent/results/reproduce/out/`: **571,053,189 regular-file bytes, 2,220 files** (544.599 MiB). Sum uses logical file lengths, excludes directory allocation and numbered logs outside `out/`. [Checks](evidence/checks.json) preserve exact groups:

| Subtree | Bytes | Files |
| --- | ---: | ---: |
| Attempt 1, `run-1793485237586031601` | 909,444 | 3 |
| Attempt 2, `run-1793485402501382269` | 284,313,310 | 1,104 |
| Attempt 3, `run-1793487733552881707` | 284,313,310 | 1,104 |
| Shared setup/probe/baseline/anchor logs and records | 1,517,125 | 9 |
| **Total** | **571,053,189** | **2,220** |

PDBs dominate bytes: 443,900,634 bytes across 2,050 files. Grids add 92,778,532 bytes across 49 files. Remote `out/` accumulates attempts; each box command clears local fetched snapshot, then fetches complete remote tree. Consequently final size is cumulative, not three independently preserved fetch sizes. Exact earlier fetch snapshots and network bytes **unknown**.

Fetching is substantial, but **does not dominate combined anchors receipt wall time** under majority-of-total meaning. [boxrun.sh](../../../../dut/pipeline/m5/boxrun.sh) starts receipt clock before launch, executes remote command under `timeout`, polls completion, reads optional telemetry, fetches `out/` and numbered log, then writes receipt. No transfer-phase timings exist.

| Attempt | Receipt wall | Command-time evidence | Remaining time, including all transport/polling overhead |
| --- | ---: | --- | --- |
| 1 | 39 s | Command ends on exception; exact duration unknown | Unknown portion of 39 s |
| 2 | 1,751 s | Remote 1,200 s timeout reached | At most about 551 s |
| 3 | 2,170 s | Inner 1,100 s timeout reached | At most about 1,070 s, slightly less with termination/startup |

Attempts 2 and 3 therefore spend at least about 2,300 of combined 3,921 s executing commands. Across all three receipts, all non-command overhead combined is at most about 1,660 of 3,960 s, below half. Fetch alone is smaller still. Attempt 1's individual split **unknown**. Attempt 3 overhead is nearly half, so describing fetch cost as negligible would also be wrong.

[0057-upload receipt](../run8/control/receipts/0057-upload.json) lasts 535 s despite short script upload; uploader also fetches accumulated `out/`. This supports substantial transfer cost, but does not independently measure fetch-only duration. Exact fetch seconds and any retry contribution remain **unknown**. Receipt overruns cannot be interpreted as equivalent command overruns.

**6. Mirror/materials causation.**

**No observed evidence of wrong, missing or corrupt inputs causing these failures.** Intake brief exactly matches named brief. All 3,602 intake URL/SHA-256 pairs match [HASHES.tsv](../intake_mirror/HASHES.tsv); its historical refetch-match fields are all true. Current read-only SHA-256 check of cached FroDock archive matches `91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4`; archived `bin/soap.bin` matches recorded `791f31ec8ef1ef1466092b425638e926755519c9626f5678ca675ef6c76234fc`. No current network fetch performed.

Run8 setup completes ([0053 log](../run8/agent/results/reproduce/0053-setup.log), line 6193); first grid payload is complete; later runs repeatedly produce complete poses for same first case and four further cases. First failure matches explicit native success-path exit; later failures match elapsed execution caps. No missing-file exception, digest mismatch or invalid-map exception appears in anchors logs.

These findings identify observed execution blockers. They do not authenticate mirror against original study distribution or establish scientific accuracy of generated poses. Original identity remains **unknown**, exactly as owner-approved brief requires. `materials_issue:no` means no observed materials cause, not verified equivalence to original.

**7. Repair visibility, targeting, and overrun framing.**

Both repair contexts expose decisive failure. [Reconstruction checks](evidence/checks.json) verify first supplied tail equals all 70 lines of attempt 1, second equals last 200 lines of attempt 2.

| Repair | Evidence seen | Actual change and outcome |
| --- | --- | --- |
| `0005-anchors-repair` | Map-write line and complete `CalledProcessError` in tail | Replaces fatal status checking with fresh-output validation, validates MRC header/payload, preserves stage logs and fixed workload; next run clears first blocker |
| `0006-anchors-repair` | Header explicitly says `rc 124, output gate: timeout`; tail ends at sixth-case docking and includes last completed case timing | Recognizes inadequate budget; adds earlier 1,100 s abort/report and stale-measurement cleanup; cannot complete workload or produce values |

Sources: first [prompt](../run8/agent/wf/agents/0005-anchors-repair/prompt.md), [reply](../run8/agent/wf/agents/0005-anchors-repair/reply.txt); second [prompt](../run8/agent/wf/agents/0006-anchors-repair/prompt.md), [reply](../run8/agent/wf/agents/0006-anchors-repair/reply.txt), and [recorded diff](evidence/repair2.recorded.diff). Second tail contains no standalone timeout line because external timeout emits none; header supplies exit diagnosis. Full five-case sum is outside tail, but repair reads full logs (`codex-1.jsonl:47`). No concealed later traceback established.

`tail_had_cause:all` denotes actionable cause visibility in both delivered repair contexts, including explicit timeout header. `repairs_targeted_cause:some` distinguishes successful root-cause correction from abort-only handling: first changes faulty control flow; second does not correct insufficient runtime allocation. Second repair correctly understands problem, but permitted scope excludes intake/pipeline budget edits. Its reply says:

```text
Fixed scale requires all 93 cases. Log shows first five consumed 1,016 seconds before DockQ evaluation; 1,200-second cap leaves insufficient evidence for successful completion.
```

Second prompt labels `1751s` as measured elapsed and `551s` as measured overrun. Pipeline lines 266–267 calculate this from receipt wall; transfer/polling therefore contaminate alleged script overrun. Nevertheless **no observed indication this misled repair**: reply uses actual `CASE_WALL` sum, identifies fixed-scale mismatch, and never claims 1,751 s of workload execution or 551 s of continued computation past outer timeout. Its bounded abort follows intake's explicit instruction. Enum `overrun_misled:no` describes observed diagnosis/actions, not access to author's private reasoning. First prompt's overrun is zero.

**8. Smallest likely recovery change.**

Choose **anchors_budget**: give unchanged representative workload an execution allowance based on measured or published runtime, with explicit headroom for complete workload plus evaluator/parser. Existing resolution already supports intake's `stage_budgets_s.anchors`; immediate configuration lever is that value. Pipeline policy should require runtime evidence for that selection and allow budget correction when actual fixed workload disproves prospective cap, rather than spending script-repair attempts on an impossible time constraint.

For current repaired harness, raising outer timeout alone is insufficient: final wrapper hard-codes **1,100 s**. Propagate corrected allowance through budget prompt and regenerate/repair wrapper to remove or update inner cap. Preserve corrected output validation from first repair. No change to 93 cases, eight ranks, 100 candidates, published pin, scoring input, measured-output requirements, DockQ threshold or reference treatment needed.

Full-run sufficient numeric budget remains **unknown**. Observed times establish failure of 1,200 s, not a guaranteed sufficient replacement. Several-hour scale is plausible from partial evidence; full completion and eventual threshold score remain untested. Runtime allocation permits measurements and scoring; it cannot guarantee scientific pass.

Extra anchors repairs under unchanged cap cannot solve this. Transfer-aware timing in repair prompts would improve precision but would not make CPU workload fit. Keeping bulky scratch/pose outputs outside routinely fetched `out/`, while retaining required measurements, logs and scientific artifacts through suitable storage, would reduce transfer expense; that also cannot resolve observed execution timeout. Neither materials replacement nor weaker checks is supported by evidence.

Evidence reconstruction: [reconstruct_records.py](reconstruct_records.py) parses saved tool commands as data, reverses recorded second-repair diff, and compares complete pre-repair snapshots. Six reconstructed scripts under [evidence/](evidence/) cover both requested scripts for all attempts. Original harness creation independently matches first snapshot; first-repair creation plus final small edit matches second snapshot; current command is identical across attempts 2 and 3. [checks.json](evidence/checks.json) records provenance lines, script hashes, exact supplied-tail comparisons, case times, output counts and material checks. No reconstructed script executed.
