Records support roughly **5.2 hours for docking and pose production**, extrapolated from five completed cases. Complete anchors runtime, including DockQ evaluation, remains **unknown**. Remaining-time timeout would remove observed outer-budget blocker, but cannot establish enough time for a complete retry. Existing inner 1,100-second cap also needs removal. Profile repeats full workload; CPU-only baseline faces a separate GPU-profile gate problem.

Diagnosis used local records and source only. No workloads, builds, installations, box access, network, commits or pushes. Writes confined to `run8_diag2/`. No credential files, `.keys` files or files under `~/.codex/` read. Prior [REPORT.md](../run8_diag/REPORT.md) and [status.json](../run8_diag/status.json) read; timing sums independently recalculated from anchors logs.

**1. Expected anchors runtime and evidence.**

Canonical [run_command.sh](../run8/agent/harness/run_command.sh), lines 6–14 and 94–151, runs 93 cases sequentially, eight MPI ranks per case, 100 poses per case, then published DockQ evaluator with eight workers. CUDA visibility is empty; GPU count is zero. [Probe record](../run8/agent/results/probe/probe.json) reports one H100 and 26 available processors. This is CPU/MPI runtime on an H100 host, not H100 computation. A100-host runtime cannot be predicted from GPU model; comparable CPU allocation/performance would be required.

Both later attempts completed the same first five sorted IDs:

| Case prefix | Attempt 0056 seconds | Attempt 0058 seconds |
| --- | ---: | ---: |
| 1a19 | 41.175 | 39.866 |
| 1aua | 244.492 | 243.864 |
| 1ax2 | 261.128 | 261.525 |
| 1dtd | 182.451 | 181.593 |
| 1dv1 | 286.793 | 286.065 |
| Sum | **1,016.038** | **1,012.914** |

Evidence: [0056 log](../run8/agent/results/reproduce/0056-anchors.log) and [0058 log](../run8/agent/results/reproduce/0058-anchors.log), `CASE_WALL` lines 1076, 2545, 3581, 4548 and 5547. Formula `93 * sum / 5` gives **18,898 s (5.250 h)** and **18,840 s (5.233 h)**. These are docking/pose-production projections, before evaluator and process/parser overhead. Sixth case remained in docking at 1,200-second outer timeout in 0056; 0058 stopped at 1,100-second inner timeout. Neither produced `MEASUREMENT`.

These are five distinct cases repeated twice, not ten independent samples or a representative timing sample. Per-case variation is large. Even projecting their median instead of mean gives approximately **6.3 hours before evaluation**. Remaining 88 case durations and evaluation of 9,300 poses are unmeasured. Script's reported summary `wall_s` sums case timers and excludes subsequent evaluation; it would not establish complete command wall time either ([run_command.sh](../run8/agent/harness/run_command.sh), lines 143–162).

No applicable published full-workload timing found in requested records. [EXECUTION.json](../run8/agent/intake/EXECUTION.json), lines 38–50, records null runtime evidence and prospective budgets. Mirror [README](../run8/agent/intake/frodock_frodock3_linux64__README), lines 77–86, gives about 10 minutes on four old CPU cores, or 40 minutes sequentially, for an unrelated antigen/antibody example. It cannot establish runtime of these 93 cases. [Brief](../intake_mirror/BRIEF_run5.md), opening scientific instructions, asks for calibration and supplies no runtime.

Thus planning evidence is **partial_progress**. Several hours is supported; a complete anchors run cannot defensibly be assigned one requested interval, especially across the 6-hour boundary. `anchors_runtime: unknown` preserves that distinction rather than presenting the 5.2-hour docking projection as measured or complete anchors timing.

**2. Same workload, profiler cost and concurrency cost.**

**Yes.** [Pipeline](../../../../dut/pipeline/m5/pipeline.js), lines 429–453, passes `harness/run_command.sh` to both fixed profiler and concurrency probe. [Profiler](../../../../dut/pipeline/m5/profile_nsys.sh), lines 114–141, invokes that file once through `bash`, under `nsys profile --trace=cuda,nvtx,osrt --sample=none`, then exports/summarizes reports. DockQ evaluation is inside that same command. Profiler installation, finalization, export and fetching add stage wall time beyond its reported command timer. No profiler slowdown measurement exists: run8 [profile stage record](../run8/control/stages/profile.json) is SKIPPED.

If profile gate passes, [concurrency probe](../../../../dut/pipeline/m5/concurrency_probe.py), lines 59–90 and 99–145, runs three complete copies serially, then potentially two copies together and four copies together, each with fresh output. No Nsight on probe copies. With `T` as one complete command duration, no MPS retry and both batches admitted, total profile-stage work has approximate wall:

`T_profiled + 3*T + T_batch2 + T_batch4 + installation/export/transport`.

Assuming profiled run approximately `T`, ideal overlap gives about **6*T**, fully serialized contention about **10*T**; these are scenarios, not measured bounds. At the docking-only 5.2-hour projection, that means roughly **31–52 hours**, before unmeasured additions. Batches may be skipped: admission requires `n*T1 <= 0.9*budget - elapsed`. Three singles alone take about **15.7 docking hours**. With less than 12 hours available, probe cannot finish those three at this projected rate, let alone useful batches. MPS startup/client-verification failure may also cause fallback and repeated work. See [SCHEMAS.md](../../../../dut/pipeline/m5/SCHEMAS.md), lines 85–98.

There is an earlier workload-specific obstacle. [Summarizer](../../../../dut/pipeline/m5/profile_summarise.py), lines 57–80, assigns CUDA kernel/memory/API totals to four rows and residual to `other host time`. For this CPU-only command, absent CUDA activity would put approximately all wall into residual. [Profile gate](../../../../dut/pipeline/m5/pipeline.js), lines 419–445, rejects any row within 2% of total wall as a process wrapper. It would therefore likely fail numerically after one full profiled execution, before optional concurrency starts. This is source-based inference, not an observed run8 profile result. Longer timeout does not solve that gate mismatch.

Consequently unconditional **profile-stage wall factor is unknown**. `over_5x` describes a successful, fully admitted probe scenario; it does not describe demonstrated execution of this CPU workload under the actual gate and ceiling. Profiler overhead alone is also unknown.

**3. Would remaining 12-hour allowance fit anchors and a repair?**

**A single corrected attempt is plausible; a complete repair-and-rerun allowance is unestablished.** Run starts at `2026-10-31T21:59:28.315Z` in [workflow status](../run8/agent/wf/status.json). [0056 receipt](../run8/control/receipts/0056-anchors.json) starts 1,431.685 s later, leaving **41,768 s (11.60 h)** of a 43,200-second ceiling. That comfortably exceeds the 5.25-hour docking projection, leaving about 6.35 hours for evaluation and other work if projection holds.

For a failure near completion followed by a fresh full run, two projected docking passes consume **37,797 s (10.50 h)**. After observed pre-attempt elapsed time, only about **3,972 s (1.10 h)** remains for both evaluations, repair authoring/upload, result collection and other overhead. Median-based docking projection already exceeds 12 hours for two passes. An early failure like observed first grid error leaves much more repair headroom: [0054 receipt](../run8/control/receipts/0054-anchors.json) lasted 39 s. A first attempt that exhausts all remaining ceiling time leaves no repair time at all; remaining-time policy reserves none.

Collection matters. 0056 receipt wall was 1,751 s for a 1,200-second timed-out command; 0058 was 2,170 s around a 1,100-second inner cap ([receipt](../run8/control/receipts/0058-anchors.json)). Differences include transport/polling/fetch, not additional docking. Prior diagnosis records 284,313,310 bytes per partial attempt and 571,053,189 bytes cumulatively across fetched `out/` ([checks](../run8_diag/evidence/checks.json)). Complete-output transfer cost is unknown and cannot be treated as zero. Per-command timeout also does not itself cap subsequent fetch wall; [SCHEMAS.md](../../../../dut/pipeline/m5/SCHEMAS.md), lines 100–104, describes receipt scope.

Literal replay of current harness still fails: [run_anchors.sh](../run8/agent/harness/run_anchors.sh), line 13, hard-codes 1,100 s. Raised outer timeout must reach regenerated/repaired wrapper too. Current pipeline also captures setup/anchors budgets before setup (lines 298–301), reuses original timeout across repairs (lines 246–284), and resolves profile timeout once for upload, profile and probe (lines 429–453). Intended remaining-time policy needs fresh deadline calculation for each actual command, including retries, plus consistent script prompts/internal caps. Current intake-over-args precedence is documented at [SCHEMAS.md](../../../../dut/pipeline/m5/SCHEMAS.md), lines 24–25; operator's proposed args precedence is a change.

Policy addresses observed outer budget error and may permit a reproduction-only result. Evidence supports neither rejecting a single attempt as inevitably too long nor certifying `yes_with_repair`. `ceiling_fits_anchors: unknown` reflects unmeasured full runtime and retry headroom. Successful runtime completion would still need valid output and anchor scoring; no scientific pass is established.

**4. Published scale or reduced scale?**

**Published paired-apo case scale: all 93 cases.** Published local [PINDER README](../run8/agent/intake/README.md), line 255, identifies 250 PINDER-S complexes, of which 93 have paired apo structures. [Brief](../intake_mirror/BRIEF_run5.md), opening paragraphs, prioritizes exactly those 93. [EXECUTION.json](../run8/agent/intake/EXECUTION.json), lines 2–8, fixes all 93 sorted cases; [setup.sh](../run8/agent/harness/setup.sh), lines 124–132, selects the entire paired-apo subset and checks count. No runtime-driven case reduction occurred. This is the full published paired-apo subset, not all 250 holo cases.

Candidate count has a separate qualification: **100 poses per case is intake's preregistered design choice**, not an established published fixed count. EXECUTION.json explicitly says so; [baseline.json](../run8/agent/intake/baseline.json), lines 40–48, records published `n_solutions` as null, and [published adapter](../run8/agent/intake/src__pinder-methods__pinder__methods__run__frodock__predict.py), lines 16–39, accepts it as a parameter. Whether 100 is reduced relative to any original study setting is unknown. `scale: published` denotes established 93-case benchmark coverage, not proof that every configuration field or mirror byte matches an original study.
