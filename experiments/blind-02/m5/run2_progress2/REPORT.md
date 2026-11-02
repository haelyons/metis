# blind-02 m5 run2: progress check 2 (read-only)

Reader: authorized reader agent. Read-only: I changed nothing under `run2/`, ran no workloads, contacted no box, and used no network or git. Paths are relative to `experiments/blind-02/m5/` unless they start with `m5/`, which means `dut/pipeline/m5/`.

Limitation: shell access was denied in this session. I had only file read, glob and grep, so I **could not measure directory sizes, count files, or read the current clock**. The sizes and file counts below (745 MB / 2,517 files; 884 MB / 2,965 files) come from the operator's metadata. Everything else comes from reading the files.

---

## A. Where the run is, and what each stage has produced

**Current step: the profile command (receipt 0010-profile not written yet). Its workload has already finished on the box, and the pipeline is now fetching `out/`.**

- `run2/pipeline.log:1-2`: `intake: PASS`, `reproduce: PASS`. `run2/agent/wf/journal.jsonl:9`: phase `profile` began 2026-11-02T17:35:22.922Z. `run2/agent/wf/status.json:5` shows `"stage": "profile"`.
- The receipts stop at `run2/control/receipts/0009-upload.json`, the profiler-script upload (17:35:22 to 17:59:06, 1424 s). There is no `0010-profile.json` yet.
- The profile command (`m5/pipeline.js:601-602`) runs `profiler/profile_nsys.sh harness/run_command.sh out/profile`. Its workload has completed on the box. The fetched tree contains a second run directory, `run2/agent/results/profile/out/runs/run.QxKYR5zO/`, and its `command.log` has all 12 MEGADOCK jobs through the last one (`gpu_dense/1nr5…`, `Elapsed time = 22.15 sec.`, line 768).
- The fetch is still in progress. `results/profile/out/latest-run/` holds only 10 of the 12 `docking.out` files so far, and there is no local `out/profile/` (nsys outputs, `stages.json`, `total_wall_s.json`, `gpu_util.json`) yet. Because I could not read the clock, I cannot say how far the fetch has got.
- After this: the concurrency probe (`m5/pipeline.js:609-621`), then seal, propose, implement, evaluate, and takeaways (still a stub, `m5/pipeline.js:983`).

What each stage has produced so far:

| Stage | Products |
|---|---|
| intake (PASS, `run2/control/stages/intake.json`) | `run2/agent/intake/{baseline,EXECUTION,benchmark,data,anchors}.json` and MEGADOCK/PINDER readme, licence and tag captures. Gate values (`journal.jsonl:3`): `found=true`, `anchors_count=0`, `data=available`, `licence=unknown`, `size=unknown`. MEGADOCK pinned at commit `9575280c…` / tag 4.1.4 (`intake/baseline.json:3-4`). |
| reproduce (PASS, `run2/control/stages/reproduce.json`: wall 3472.6 s, gpu_s 49.64, usd 2.92) | Harness `run2/agent/harness/{setup,run_command,run_anchors,run_evaluation}.sh`. Box probe (`results/probe/probe.json`). Setup (receipt 0006, 145 s), anchors run (0007, 1571 s), freeze `cp -a out reproduce-out` (0008, 1402 s). Scored anchors: 0 of 0 (`results/reproduce/anchors_scored.json`). One complete 12-job run, `out/runs/run.NoFdwlTC/`, with `summary.json` (DockQ rank-1 and best-of-50, elapsed times, CPU/GPU deltas). |
| profile (in progress) | Script upload (0009, 1424 s). The profiled run `run.QxKYR5zO` has finished on the box and is being fetched. No profile packet or receipt yet. |

## B. Baseline configurations and cases run by reproduce

**All three seed configurations, on all four seed cases. That is 12 docking jobs × 50 poses, run as a single baseline command.**

- `run2/agent/harness/run_command.sh:16-43` loops over `cpu_standard` (`megadock`, `-r 3600`), `gpu_standard` (`megadock-gpu`, `-r 3600`) and `gpu_dense` (`megadock-gpu`, `-D` = 54,000 rotations) × 1aua, 1ax2, 1dv1 and 1nr5. Every job uses `-N 50 -t 1 -v 1.2 -e 1.0 -d 1.0 -a -45.0 -b 1.0 -f 3`. decoygen then writes ranks 1-50.
- `run2/agent/results/reproduce/out/anchors.log` confirms all 12 jobs ran: `0 GPUs` for CPU (line 19); `NVIDIA H100 PCIe`, `1 GPUs` for GPU (lines 236, 246); `Set 54,000 rotational angles` for dense (line 513). Lines 776-798 print per-case and per-configuration DockQ.
- The pipeline therefore treats one "baseline" as a bundle of all three configurations. Every later baseline run (profile, concurrency, implement, evaluate) repeats CPU, GPU and dense together.
- For the owner: the measured values are already visible in `anchors.log:776-798`. At identical settings, CPU and GPU standard give identical DockQ in all four cases, and rank-1 scores differ by ≤ 0.02. The binary prints `MEGADOCK ver. 4.1.3 … lastupdated 26 March, 2019` (`anchors.log:8-9`) while the pin is tag 4.1.4. Whether that is only a stale version string is not established.

## C. What dominates box wall time

**Fetching `out/` dominates. It takes about 1,400 s per command at the current out/ size, while the workload itself takes about 3 minutes. Each fetch resends unchanged outputs, and the latest run is sent twice.**

Evidence:
1. Every box command runs `boxrun.sh … --fetch out` (`m5/pipeline.js:194-196`). The fetch is `scp -r` of the whole remote `out/` (`m5/boxrun.sh:55-56, 87-90`). Before each command the pipeline deletes the local `out/` (`m5/pipeline.js:191`), so nothing is reused. scp has no delta or skip of unchanged files.
2. **Commands with almost no workload still take about 1,400 s.** The freeze command is only `cp -a out reproduce-out` (`m5/pipeline.js:519`), and it took 1402 s (receipt 0008). The upload of two small scripts took 1424 s (receipt 0009). Setup, which ran while `out/` was still small, took only 145 s (0006), and that includes the MEGADOCK CPU and GPU builds and the venv install. The receipt `wall_s` runs from launch through fetch (`m5/boxrun.sh:9, 31`), so it includes the fetch.
3. **Unchanged outputs are resent.** `run.NoFdwlTC` from reproduce was fetched by 0007, again by 0008 and 0009, and appears again in the current profile fetch (`results/profile/out/runs/run.NoFdwlTC/`). Its content has not changed since 0007.
4. **The latest run is sent twice.** `run_command.sh:12-13` creates `out/runs/run.XXXX` and the symlink `out/latest-run`. `scp -r` follows symlinks, so `latest-run` arrives as a full second copy (`results/reproduce/out/latest-run/gpu_dense/…/apo_decoys/model_50.pdb` exists as a real file beside `out/runs/run.NoFdwlTC/…`). This matches the operator's 2,517 files ≈ 2 × (12 jobs × 104 files) + setup/log files.
5. `out/` grows with every baseline invocation, because each `run_command.sh` adds a new `runs/run.*` (about 370 MB, about 1,250 files). The profile fetch carries run.NoFdwlTC, run.QxKYR5zO, the duplicated `latest-run` and the nsys outputs.

**Estimate of the workload's own run time:**
- Docking-only elapsed times from `anchors.log` (reproduce):
  - CPU: 9.11 + 7.28 + 11.81 + 11.87 = 40.1 s
  - GPU standard: 1.66 + 1.38 + 1.88 + 1.93 = 6.9 s
  - GPU dense: 16.60 + 13.88 + 19.38 + 19.52 = 69.4 s
  - Total: about 116 s
- In the profiled run under nsys (`results/profile/out/runs/run.QxKYR5zO/command.log`): about 155 s (CPU 45.1, GPU standard 9.7, dense 80.0).
- Whole anchors command (run_command plus decoygen ×600 plus DockQ scoring): receipt 0007 (1571 s) minus receipt 0008 (1402 s). Both fetched the same `out/`, because the freeze changes nothing in `out/`. That gives **≈ 170 s ± 20 s** (the poll interval is 20 s, `m5/boxrun.sh:82`). GPU busy over that command was 49.6 s (receipt 0007).
- Implied fetch throughput: about 745 MB / about 1,400 s ≈ 0.53 MB/s, or about 1.8 files/s. That points to per-file scp overhead or a slow link, not workload.

Box time by component so far:

| Component | Time | Share |
|---|---|---|
| Fetch | ≈ 1,400 s × 3 (0007-0009) | ≈ 4,200 s |
| Workload | ≈ 170 s (anchors) + about 145 s (setup) | — |
| Fetch share of box time 16:43:24 to 17:59:06 (4,542 s) | — | about 90% |

## D. Will the run finish within the 12 h ceiling?

**Probably not. My central estimate is about 12.1 h, against a 12 h ceiling. Most of the uncertainty would make it later, not earlier.** The ceiling is 43,200 s from the pipeline start (wf `started` 2026-11-02T16:33:44Z, `run2/agent/wf/status.json:6`), so it falls at about 2026-11-03T04:33:44Z. If measured from the box start (16:27:45Z), it falls at about 04:27:45Z.

Assumptions:
- Fetch rate as measured: 0.53 MB/s.
- `out/` after profile ≈ 3 × about 370 MB (two runs plus the duplicated latest-run) + nsys outputs ≈ 1.1-1.2 GB, so ≈ 2,100-2,300 s per fetch until something deletes `out/`.
- `setup-method` and `run-method` run `rm -rf out` (`m5/implement.js:386, 392`). After that, fetches shrink to roughly one run's outputs (about 745 MB with the symlink duplicate, ≈ 1,400 s), if the method keeps the same output layout.

| Step | Box commands (source) | Estimate |
|---|---|---|
| Elapsed to start of profile command | — | 17:59:06 → 5,122 s |
| profile command | nsys run (about 3-4 min) + export + fetch of about 1.1-1.2 GB | about 2,400-2,600 s |
| concurrency probe | 3 sequential single copies, then batches of 2 and 4 concurrent copies (`m5/concurrency_probe.py:21-23, 119-133`); repeated without MPS if MPS fails (`:140-148`). About 160 s per copy → about 800-1,500 s workload (×2 if MPS retry) + one about 2,200 s fetch | about 3,000-3,700 s (up to about 5,000) |
| seal + propose | agent calls only (seal, possible seal-repair, propose, 5 skeptic votes) | about 1,000-2,000 s (no measurement) |
| implement | Before `out/` is cleared: implement-baseline, adapter upload ≥1, adapter-smoke, state after-author, state before, method upload ≥1, implement-patch. That is ≥ 7 × about 2,200 s ≈ 15,400 s. After: setup-method, run-method, 3 state/test commands, ≈ 5 × about 1,400 s + workloads ≈ 7,000 s (`m5/implement.js:333-428`) | ≈ 20,000-22,000 s (one attempt, no repair) |
| evaluate | upload ≥1, then for validity, equivalence and performance: state before, stage, state after. ≈ 7-10 commands × ≥ 1,400 s + workloads (`m5/evaluate.js:57, 119-133`) | ≈ 10,000-14,000 s |
| **Total from pipeline start** | — | **≈ 41,500-50,000 s; central ≈ 43,500 s (≈ 12.1 h)** |

Things that would push it later:
- an adapter-smoke second attempt (`implement.js:345-347`)
- an implement repair attempt
- upload batches split by size (`implement.js:271-281`)
- MPS retry in the concurrency probe
- the evaluate performance stage writing repetitions (≥ 5 by the seal schema, `m5/SCHEMAS.md:184`) of full 600-decoy runs into `out/`, which would make its fetches far larger

Only a faster fetch path would make it earlier. I cannot rule out a faster link later, but nothing in the logs suggests one.

The pipeline does not stop at the ceiling. Only the setup, anchors and profile budgets are derived from the remaining ceiling time (`m5/pipeline.js:163-166`). Implement and evaluate use fixed defaults (1200/900/2400 s, `m5/pipeline.js:160, 171-174`). Fetch time is outside boxrun's own deadline (`m5/boxrun.sh:74, 87-90`) and only shows up as `overrun` in the receipt (`m5/pipeline.js:204`). So a run that exceeds 12 h would most likely continue and record overruns, not stop at 12 h.

I could not establish the current time, the size of `out/profile/` (nsys report), whether MPS works on the box, how many implement and evaluate upload batches there will be, or the method's output size.

## E. Which of the seed's comparisons the pipeline can produce

**Some.**

The pipeline's later stages are built around a different question: whether a proposed *method* is faster than one bundled *baseline* while staying *equivalent* to it. The stage sequence is profile → seal a protocol and speed-up predictions → propose a speed-up method with skeptic votes → implement → evaluate validity, equivalence, performance and equal cost (`m5/pipeline.js:28-33`; `m5/SCHEMAS.md:171-184`).

Here the brief's three configurations are already folded *inside* the baseline (section B). So:

| Seed request | Covered by the pipeline as configured? |
|---|---|
| CPU vs GPU execution acceleration at identical settings | Not a pipeline comparison. The per-job `Elapsed time` values exist only as baseline measurements (`anchors.log`, `summary.json`). The evaluate stage compares method vs bundled baseline, not cpu_standard vs gpu_standard. No sealed timing repetitions applied to this comparison. |
| Scientific agreement CPU vs GPU with tolerances defined *before* examining results | Partly. Raw deltas are computed (`run_anchors.sh:64-73`) but with `acceptance_tolerance: null`. They were computed, together with DockQ for all configurations, during reproduce, *before* any seal. This breaks the brief's order (`BRIEF.md:13`, `:17`). The seal's equivalence rule is method vs baseline, not CPU vs GPU. |
| Quality change from denser search (DockQ rank-1 and best-of-50, separately) | Measured once in reproduce (`dense_minus_standard`, `run_anchors.sh:64-66`), but no stage compares it under a sealed rule. The evaluate stage's equivalence test treats a quality *change* as non-equivalence, not as a measured improvement. |
| Runtime calibration → sealed configurations, repetitions, comparison rules, total spending cap | Partly. The seal requires repetitions (≥ 5), compute_budgets and baseline_invocation_s (`SCHEMAS.md:184`), but for the method-vs-baseline speed-up question, not the brief's three-way comparison. There is no explicit total-cap field matching the brief. |
| Complete workflow time, GPU activity, billed cost | Yes, coarsely. Stage wall, receipt `gpu_busy_s`, and usd = Σ receipt wall × box price (`m5/pipeline.js:1003-1009`). The billed time is dominated by fetches (section C). |
| Keep three conclusions separate; report contract limitations | Intake recorded the limitation explicitly (`run2/agent/intake/EXECUTION.json:107-110`, `benchmark.json:167-170`). No later stage carries it forward as a separate conclusion. Takeaways is still a stub (`m5/pipeline.js:983`). |

## F. Errors and warnings so far

**Warnings only. No stage failed and no receipt shows an error.**

- All receipts 0006-0009: `rc 0`, `timed_out false`, `overrun false`, `fetched true`. `pipeline.log` shows only PASS. `wf/status.json` shows `errors: []`, `refusals 0`, `substitutions 0`.
- Compiler warnings in the setup log (`-Wformat`, `-Wformat-security`), e.g. `run2/agent/results/reproduce/0006-setup.log:180-269`. The `[ERROR] too large FFT size` text at `:258` and `:269` is quoted source in a warning, not a runtime error.
- `0006-setup.log:329-330`: pip's resolver reports a pipx/argcomplete conflict in system packages. Not fatal; setup rc 0.
- The version string is 4.1.3 while the pinned tag is 4.1.4 (`anchors.log:8`). This may matter for provenance; not established.
- Protocol-order and resource issues (not log errors): DockQ and CPU/GPU comparisons were computed before the seal (section E). The fetch design resends unchanged outputs, including the duplicated `latest-run` (section C), and that drives the time risk in section D.

## Could not establish

- Current time and how far the profile fetch has got.
- Exact on-disk sizes and file counts (no shell; operator figures used).
- The nsys output size.
- Whether MPS will work.
- The number of implement and evaluate commands, which depends on agent outputs and repairs.
- The cause of the 4.1.3/4.1.4 version string.
- The fetch-rate figure assumes link throughput stays constant.
