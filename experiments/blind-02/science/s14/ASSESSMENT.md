# s14 assessment: the operator's draft "Sealed comparison (U57, U58)" against s13's FINAL.json (2026-11-03)

**Scope.** I ran no test. I used no network, contacted no box, ran no git commands and read no credentials. I read:
- `science/s09/` (ASSESSMENT.md, REQS.json, PARTS.json);
- `science/s13/` (FINAL.json, ASSESSMENT.md, NARROWING.md);
- the seed `m5/BRIEF.md`;
- the physical card's plan `20261103-0124-tree/out/work/seed-20261103/R1/physical/1fffee1a/producer.md` (PC below);
- `dut/pipeline/m5/SCHEMAS.md:146–156` and `:318–339` (receipts, evaluate and compute metadata).

The Bash tool was denied in this session, so I read and wrote everything with the file tools. I wrote only into `science/s14/`. "Contract" below means the draft section as it appears in the step brief. It has no line numbers yet, so I cite it by its sub-heading.

## Verdict: partial

The design's structure is sound, and I recommend keeping it:
- a sealed design with a hash seal written before any agent call;
- an agent-visible view with no criteria;
- one adapter per arm, sealed before upload;
- interleaved shuffled rounds with warmups;
- a trusted scorer that re-checks the seal;
- "not supported is a result, never a stage failure".

All three arms are runnable as written. A0, A1 and A2 are published MEGADOCK CPU/GPU binaries and flags, and the harness already ran them in run6, 60/60 jobs (`s13/ASSESSMENT.md` §1). The hardware record is complete.

**As written, though, the contract cannot decide any of FINAL.json's seven comparisons in the form FINAL.json and the sealed card need.** The scorer reduces each arm and replicate to one scalar: the mean over all inputs of that arm's own metric (contract, Scoring, first bullet). The agreement comparisons need elementwise cross-arm checks. The quality and affordability comparisons need per-case decisions. Two comparisons need decision rules the card sealed and the contract cannot express. Every fix below adds to the same design and none replaces it, so the verdict is "build after the listed fixes", not "insufficient".

## Per comparison

| Id | FINAL.json | Why the draft cannot decide it as needed |
|---|---|---|
| K1 | A1 vs A0, result_agreement, equivalence, abs | The card requires exact ranked rotation/translation identity, including rank 1 and cutoff membership, and reconstructed coordinates within eps_xyz per pose (PC:58). The draft has two limits. (1) An adapter may compute a metric only from "this invocation's own output", so no metric can compare A1's output with A0's. (2) The scorer only takes differences of per-arm means, and a difference of mean coordinates says nothing about per-pose identity. |
| K2 | A1 vs A0, result_agreement, equivalence, rel | The card requires abs(s_CPU − s_GPU) ≤ atol + rtol·max(\|s_CPU\|,\|s_GPU\|) for each of the 50 ranked scores (PC:58). The draft allows an abs or a rel margin, never both. Its rel base is the median of the against arm's paired values, not the per-element max(\|a\|,\|b\|). |
| K3 | A1 vs A0, quality, equivalence, abs | The card requires each paired DockQ difference ≤ eps_eval (PC:58), which is an elementwise maximum. A difference of means over 4 cases × 50 poses can be inside the margin while single poses are far outside it. |
| K4 | A1 vs A0, throughput, ratio_at_least 1.05 | The metric can be captured: `process_wall` with `lower_better` gives wall_A0/wall_A1. The sealed rule cannot be expressed: a 95% paired block bootstrap, 7 blocks resampled jointly across cases, 10000 draws, lower bound > 1.05 (PC:29–30). With n = 7, `sign_test` at 0.95 gives k = 1, because P(X<1) = 1/128 ≤ 0.025 and P(X<2) = 8/128 > 0.025. That is the min–max interval, a different and more conservative rule than the one the card sealed. K4 is also gated on K1–K3 (PC:65; s13 §4 item 1), and the draft scores every comparison unconditionally. |
| K5 | A2 vs reference, runtime, non_inferiority, lower_better | The references are per-case, per-tier seconds, 4 cases × 3 tiers (PC:97; s13 §2 lists 12 values). The draft has three limits. (1) It allows one number per comparison and averages over inputs. (2) `process_wall` is the wall of the whole invocation, so all four cases share one value and no per-case trusted time exists. (3) A timed-out or failed invocation becomes null and drops out of the pairing. A dense run that misses its budget therefore vanishes, and the remaining replicates can still return "supported". The seed requires budget overruns to be preserved (`BRIEF.md:19`), and the card records a miss as unavailable at that tier (PC:29, 107). 12 per-case-tier comparisons plus the other six would also exceed the 12-comparison cap. |
| K6, K7 | A2 vs A1, rank-1 / best-of-50 DockQ, superiority, two_sided, abs | The card's rule is per case and eligible tier: gain iff min(dense) − max(standard) > margin + 2·eps_eval; loss iff max(dense) − min(standard) < −(margin + 2·eps_eval) (PC:29). The draft pairs replicates and uses [min, max] of the paired differences. Since min_r(d_r − s_r) ≥ min d − max s, the draft returns "supported" in cases the card calls unresolved, which is more liberal than the sealed rule. The draft also averages over cases, where the card needs a 4-case table. It cannot gate on K1–K3, and its two-sided "supported" does not say whether the result was a gain or a loss. |
| compute_facts | per_arm_wall, per_arm_gpu_s, hardware_identity, usd | Wall, GPU-busy seconds and hardware are recorded correctly. `usd` is receipt-wall × price per arm, which is compute attribution. FINAL.json (s13 §3, citing PC:68) and s09 G6 require the billed allocation: hours × price including setup, idle and failed work, with the allocation end. run6's `C/box.json` had no `ended_utc` (s09 G6). The draft adds no allocation record, and `run_box_usd` (`SCHEMAS.md:337`) uses the accounting time as the end while a box is still active. |

## Problems and the smallest fix for each

1. **metric_not_capturable** (K1–K3). Add the metric source `"pair"`: a list-valued adapter metric that the trusted scorer compares across arms within the same round and input. Adapters may then report finite-number arrays (ranked transform indices, coordinates, scores, per-pose DockQ) taken from their own output. Also state that adapters may read the pinned inputs and the reference structures for evaluation only. The current "own output only" wording can be read as forbidding DockQ.
2. **statistic_unfit** (K1–K7). Add these `rule` values:
   - `"elementwise_max"`: per round and input, the maximum over elements of \|a_i − b_i\| minus the element tolerance. Supported when it is ≤ 0 in every paired round. Requires equal lengths; a length mismatch is not_supported, as the card's "tie mismatch fails" requires.
   - `"block_bootstrap"` with `draws` and `confidence`: seeded by `order_seed`, resampling replicate rounds jointly across inputs, giving a percentile interval of the ratio of summed walls.
   - `"range_worst_case"`: per input, lo = min(arm) − max(against), hi = max(arm) − min(against), over replicate values.

   Add a field `missing: "drop" | "fail"`. Under `"fail"`, any null replicate makes the outcome not_supported, which is what K5 needs. Record `n_missing` per row.
3. **criterion_unfit** (K4, K6, K7). Add an optional `after: [comparison ids]`. When any listed comparison is not supported, the scorer writes outcome `"gated"`, adds `gated` to `totals`, and adds `comparisons_gated` to the facts. For two-sided superiority, add `"sign": "gain" | "loss" | null` to each scored row. The card's rule also uses strict > for the speed bound (PC:29), while the draft's ratio test is ≥. Let the design choose strict or non-strict.
4. **margin_rule_unfit** (K2). Allow the margin `{"abs": a, "rel": r}` with an element tolerance of a + r·max(\|a_i\|,\|b_i\|) under `elementwise_max`. Keep the existing forms unchanged.
5. **reference_unfit** (K5). Allow `reference` to be an object mapping each input id to a finite number, or to a list of finite numbers (one per tier, each scored as a separate row). This fits the per-case, per-tier tiers without raising the 12-comparison cap.
6. **inputs_unfit** (K1–K7). (a) Run one invocation per arm *and input*: `CMP_INPUTS` holds that single input id, and the round's order is one shuffle of the arm ids for each input, inputs in id order. This gives a trusted per-case `process_wall`, matching "all 3 arms per case in randomized order" (PC:30). (b) Add `per_input: true|false` to each comparison. With true, the scorer writes one row per input, and the mean over inputs is used only when it is false.
7. **budget_unfit** (K5). The only timeout is the time left in the shared `evaluate` budget. One overrunning dense invocation can therefore consume every later round, and the card's per-invocation cap at the largest frozen tier (PC:107) cannot be expressed. Add an optional design field `timeout_s` per arm and input. Each invocation's timeout becomes the smaller of `timeout_s` and the time left, and a timeout is recorded as `"timeout"` and never as a measured value.
8. **compute_unfit** (compute_facts). Add `allocation` to `comparison_compute.json`, exactly `{started_utc, ended_utc, hours, usd, final}`, from `C/box.json`. Refresh it at takeaways when the matching allocation record has `ended_utc` (`SCHEMAS.md:332–333`). When it has not been refreshed, `final` is false, so a missing final bill is marked as estimated (PC:112). Keep per-arm `usd` but rename it `attributed_usd`, so it is never read as the bill.
9. **leaks_or_biases**. Two issues:
   - Nothing checks that the adapters differ only in the declared axis. The harness agent writes all of them, and an agent could give A2 different scoring flags or a different retained count without detection, while the card requires identical shared flags (PC:23). The smallest fix is an optional design field `arms[].argv`: the exact published command line, sealed in `C/`, which the pipeline compares against the command each adapter executes (or passes in as `CMP_ARGV`). Adapters then wrap the command but do not choose it.
   - Criteria are hidden only through prompt wording ("prompts never name it"). The contract should also require the design source path to lie outside every agent's readable roots, and agents to have no read access to `C/`. Otherwise the margins are reachable.

## Items that are correct as written
- Sealing order and content: `C/comparison.json`, its seal, the scorer's hash re-check and `C/arms_seal.json`.
- The view's contents.
- Warmup handling.
- `seeds` null for MEGADOCK, which takes no seed.
- The replicate range, which covers both 2–5 and 6–10.
- The hardware record.
- Evaluate PASS whatever the outcomes.
- Exclusivity with the other modes.

I found no `sealing_unfit`, `order_unfit` (beyond the per-input change in fix 6) or `arm_not_runnable` defect.

## For the owner
After these nine fixes I expect the section to express both of s09's runs: the P2 tolerance calibration, and the physical card's main study with gating. The owner's choice of tolerance source for K1–K3 (s13 §5) is still open and is not affected by this check. s13 sealed no predictions, so `outcomes.json` is empty. This step runs no test. Next action: stop, `contract_gap`, for the operator to revise U57/U58.
