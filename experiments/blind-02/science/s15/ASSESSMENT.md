# s15 assessment: how each FINAL.json comparison must be measured and decided, and the remaining fixes for G1/G3/G6 (2026-11-03)

**Scope.** I ran no test. I used no network, contacted no box, ran no git commands and read no credentials. I read:
- `science/s13/` (FINAL.json, ASSESSMENT.md);
- `science/s14/` (ASSESSMENT.md, NARROWING.md, and the operator's draft in PROMPT.md, lines 43–60 and 74);
- the physical card's plan `20261103-0124-tree/out/work/seed-20261103/R1/physical/1fffee1a/producer.md` (PC below), lines 18–113.

The Bash tool was denied in this session, so I wrote every file with the file tools. I wrote only into `science/s15/`.

`SHAPES.json` turns s14's nine problems into the fixed vocabulary. Each shape follows the rule the card sealed (PC:29, 30, 58, 97, 107). Where the card's rule and a listed code differ, I kept the card's rule and chose `other`. Moving a sealed criterion toward the vocabulary would change the decision rule before any result exists.

## 1. Shape of each comparison

### K1: A1 vs A0, ranked transforms and reconstructed coordinates (PC:58)
**Shape:** `cross_arm_outputs`, `elementwise_abs`, `per_input_all`, `paired_replicate`, `all_pairs`, `abs`, `baseline_arm`.
- **Metric origin.** The trusted comparator reads both arms' output files for the same case and replicate. Neither arm's own scalar can express "identity of the ranked list" (s14 problem 1).
- **Comparator.** The rotation/translation indices, the rank order and cutoff membership are integers, compared with atol 0, which is exact identity. Reconstructed coordinates are compared within eps_xyz. Both are elementwise absolute checks with a tolerance per field. A length or tie mismatch fails (PC:58, "Tie mismatch fails this strict gate").
- **Decision unit.** It must hold on all 4 cases, because the gate halts dense quality on "any anchor/agreement failure" (PC:102).
- **Pairing and interval.** GPU output is not byte-reproducible (s13 §2: 39 distinct hashes over 40 files), so each replicate is paired by round and every pair must pass.

### K2: A1 vs A0, the 50 ranked scores (PC:58)
**Shape:** `cross_arm_outputs`, comparator **`other`**, `per_input_all`, `paired_replicate`, `all_pairs`, `abs_plus_rel`, rel_base `per_element`, `baseline_arm`.
- **Why the comparator is `other`.** The card seals abs(s_CPU − s_GPU) ≤ atol + rtol·max(|s_CPU|, |s_GPU|). The listed `elementwise_abs_plus_rel` uses abs(b), the base of one arm only. That rule is asymmetric and stricter than the sealed one. The sealed rule is fixed, so I did not substitute the listed comparator.
- **What `other` needs.** A comparator mode `elementwise_abs_plus_rel_symmetric`, with element tolerance atol + rtol·max(|a_i|, |b_i|). The rel_base is still each element's own pair, so `per_element` holds.

### K3: A1 vs A0, each paired DockQ difference ≤ eps_eval (PC:58)
**Shape:** `cross_arm_outputs`, `elementwise_abs`, `per_input_all`, `paired_replicate`, `all_pairs`, `abs`, `baseline_arm`.
- The elements are per-pose DockQ values: 50 poses per case. A pinned DockQ evaluator, which alone has the native references mounted (PC:23), computes them from each arm's decoys. Adapters do not compute them (see the leak fixes). The comparator then takes the elementwise absolute difference across arms.

### K4: A1 vs A0, wall ratio CPU/GPU, lower bound > 1.05 (PC:29–30)
**Shape:** `trusted_wall`, `pooled_mean`, `paired_replicate`, `bootstrap`, `rel`, rel_base `against_value`, `baseline_arm`, `ratio_of_means`.
- **Metric origin.** The trusted wall of each invocation, with one case per invocation (inputs fix below). The card times the complete workflow, including decoy reconstruction and DockQ (PC:68). The design must state that scope.
- **Decision unit, pairing and interval.** "Resample 7 blocks jointly across cases, 10000 draws, 95% interval" (PC:30). The block is the replicate round, so the pairing is by replicate and the decision is made once over all cases.
- **Ratio form.** Each draw is Σ wall(A0) / Σ wall(A1) over the resampled blocks and all cases. That is a ratio of means over equal case sets. This is my reading of PC:30, which does not state the ratio form; s14 problem 2 reads it the same way. The design must seal it explicitly.
- **Margin.** The lower bound must be strictly greater than 1.05 (PC:29, "> 1.05"). Strict vs non-strict must be a design field (s14 problem 3).
- **Gating.** K4 runs only after K1–K3 pass (PC:30, 65). The vocabulary has no field for gating, so it stays a required contract item from s14 problem 3 (`after: [K1, K2, K3]`, outcome `gated`).

### K5: A2 within per-case tier seconds (PC:97, 107)
**Shape:** `trusted_wall`, `per_input_each`, `unpaired`, `all_pairs`, margin `none`, `previous_run`.
- **Reference.** 4 cases × 3 tiers. They are frozen by the card's formula from walls measured in the calibration run (run 1), before run 2 (PC:96–97). So the origin is `previous_run`. The design must name that run and the formula, and seal the 12 values.
- **Decision unit.** Per case and per tier, reported, never averaged (PC:29, 111). A dense invocation that times out or fails is recorded as unavailable at that tier. It is never dropped and never counted as DockQ 0 (PC:29, 107). Nulls must therefore fail the tier rather than leave the pairing (s14 problem 2, `missing: "fail"`).
- **Interval.** `all_pairs` here means that every dense replicate finishes within the tier. The card does not state this rule word for word. It is the reading most consistent with PC:107 ("incomplete search unavailable at that tier") and the card's worst-case treatment elsewhere, and the sealed design must state it.

### K6 (rank-1 DockQ) and K7 (best-of-50 DockQ): A2 vs A1 (PC:29)
**Shape:** `sealed_extraction`, `per_input_each`, `unpaired`, `all_pairs`, `abs`, reference `none`.
- **Metric origin.** A rule fixed before the run reads the scalar from the trusted evaluator's per-pose DockQ for each arm's own output: rank 1 is the pose with the highest MEGADOCK score, and best-of-50 is the maximum over the 50 retained poses (PC:36). The two are separate extractions, and rank 1 is never inferred from best-of-50 (PC:29).
- **Pairing and interval.** The card's rule is gain iff min(dense) − max(standard) > margin + 2·eps_eval, and loss iff max(dense) − min(standard) < −(margin + 2·eps_eval). Taking every cross pair (i, j) of unpaired replicates and requiring all of them to clear the margin gives exactly min − max. That is `unpaired` + `all_pairs`. The paired-replicate form would be more liberal than the card (s14, K6/K7 row).
- **Margin.** abs, 0.01 + 2·eps_eval (PC:29).
- **Still outside the vocabulary.** The rule must report gain, loss or unresolved per case and per eligible tier, which is s14's `sign` field. Its eligibility depends on K5's per-tier outcome, and it is gated on K1–K3.

## 2. Fixes

**inputs: `one_input_per_invocation`.** The draft passes all inputs to one invocation (PROMPT.md:57, `CMP_INPUTS` = the view's inputs), so `process_wall` is shared by the 4 cases. K4 and K5 need per-case trusted walls, and the card runs "all 3 arms per case in randomized order" (PC:30). All arms take the same 4 pinned cases, so `inputs_differ_by_arm` does not apply. Run 1's synthetic fixtures feed the evaluator and tolerance analysis, not the arms.

**budget: `design_sets_budget`, `split_into_runs`.**
- The draft's only timeout is the time left in the shared evaluate budget (PROMPT.md:58). The card needs a per-invocation cap equal to the largest frozen tier (PC:107), and a phase timer checked against the 12 h ceiling before any box command.
- The card's phases need repair, then calibration (3 h, PC:85–86), then freeze, then agreement (2 h) and main (4 h) with a 2 h report reserve and a 12 h hard stop (PC:102, 107, 112). The tiers and tolerances must be frozen from run 1 before run 2 (PC:96), so K1–K7 cannot be decided in one run.
- Run 2 projects USD 49.48 (PC:75), above the USD 20 rule, so it needs owner approval (s13 §5).

**compute: `per_invocation_rows`, `exclude_overhead`, `software_versions`, `cpu_identity`, `other`.**
- `per_invocation_rows`: K4's bootstrap and K5's per-case tiers need each invocation's wall, not only the per-arm sums the draft writes (PROMPT.md:60).
- `exclude_overhead`: the arm's subprocess only, not link setup or fetches. The card reports cold setup and retrieval separately (PC:68).
- `software_versions`: CUDA, cuFFT, driver, FFTW and each binary's hash are pinned (PC:22). The draft's hardware record has the driver only.
- `cpu_identity`: A0 runs on the host CPU with 26 OpenMP threads and fixed affinity (PC:22, 24). The CPU wall is half of K4's ratio.
- **`other` (billed allocation).** FINAL.json's `usd` is the billed allocation: hours × price including setup, idle and failed work, with allocation start and end (PC:68, 111–112; s13 §3). The draft's per-arm `usd` is receipt wall × price (PROMPT.md:60), which is compute attribution. **What it needs** (s14 problem 8): an `allocation` record `{started_utc, ended_utc, hours, usd, final}` from `C/box.json`, refreshed when the allocation ends, with `final: false` marking an estimated bill; and per-arm `usd` renamed `attributed_usd`. No listed code describes the bill.

**leaks: `adapter_no_metrics`, `view_text_screened`, `other`.**
- `adapter_no_metrics`: in the draft, adapters report the metrics (PROMPT.md:59). With the shapes above, every number comes from the trusted comparator, the sealed extraction or the trusted wall. DockQ comes from the pinned evaluator, which alone has the natives (PC:23). An adapter therefore cannot shape a result.
- `view_text_screened`: the science step that writes the design's free text owns this check.
- **`other` (arms differ only in the declared axis, and criteria cannot be reached).** The card requires identical shared flags across arms (PC:23, 40–48). I did not choose `separate_adapter_authors`, because different authors still would not guarantee identical flags. **What it needs** (s14 problem 9):
  - a sealed `arms[].argv` per arm (the exact published command line), which the pipeline compares against the command each adapter executes;
  - the design source and `C/` outside every agent's readable roots, so margins and references cannot be reached by reading files, not only kept out of prompts.

## 3. Still open for the owner (unchanged from s13 §5)
These shapes do not depend on the choices below:
- The tolerance source for atol, rtol, eps_xyz and eps_eval (K1–K3, and the 2·eps_eval term in K6 and K7).
- Approval of run 2 above USD 20.

## 4. Counts and next action
- `other` appears 3 times in SHAPES.json: K2's comparator, compute and leaks.
- s14 sealed no predictions, so `outcomes.json` is empty.
- This step runs no test and makes no predictions.
- Next action: stop, `contract_gap`, for the operator's single revision of U57/U58.
