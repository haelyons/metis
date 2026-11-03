# s13 assessment: what the final experiments must compare (G1, G3, G6), 2026-11-03

**Scope.** No test, no network, no box contact, no git, no credentials. I read `science/s09/` (ASSESSMENT.md, PARTS.json, REQS.json, NARROWING.md), `science/s10/`–`s12/` (ASSESSMENT.md, CHECK.json), `s07/ASSESSMENT.md` §A–§D, `s01/ASSESSMENT.md:30–90`, the seed `m5/BRIEF.md`, the tree result `20261103-0124-tree/out/result.json:250–300` (T below) and the physical card's plan `T/out/work/seed-20261103/R1/physical/1fffee1a/producer.md` (PC below). The Bash tool could read files but could not write them, so I wrote the files with the file tool. I wrote only into `science/s13/`.

`FINAL.json` puts the content of this file into the fixed vocabulary. It covers both final runs that s09 expects (`s09/ASSESSMENT.md` §5):
- **run 1**, the P2 tolerance and repeatability calibration;
- **run 2**, the physical card's main study, which also carries C2's acceleration component.

## 1. Arms

The seed fixes three configurations (`m5/BRIEF.md:5–9`), and s09 keeps them as the arms. The budget tiers are conditions on these arms, not further arms (`s09/ASSESSMENT.md` G1).

| Arm | What it is | Axis | New code | Published |
|---|---|---|---|---|
| A0 baseline | MEGADOCK CPU, standard sampling (3600 rotations), score settings fixed, 50 retained | none | no | yes |
| A1 | MEGADOCK GPU, identical settings | implementation | no | yes |
| A2 | MEGADOCK GPU, documented dense sampling (54000 rotations, PC:8) | configuration | no | yes |

- **A2's axis.** Compared with A0, A2 differs in both implementation and configuration. The vocabulary allows one axis per arm, so I gave A2 `configuration`. That is the only difference in every comparison A2 enters (K6 and K7 are against A1). K5 is against a fixed budget, not against an arm.
- **New code.** None of the arms needs new code. The seed requires "MEGADOCK's existing implementations" (`BRIEF.md:11`), and run6 ran all three as published flags and inputs (`s07` §A, 60/60 jobs). The card's independent transform-reconstruction checker and DockQ-component checker (T:263–264) are harness and evaluation code, not arm code. So `arms_need_implement` is `none`. m5's implement stage must not be asked to write a method for any arm.

## 2. Comparisons

### P2: agreement at identical settings (run 1 fixes the margins; run 2 applies them before anything else)
The card's agreement gate has three numeric parts (T:263, PC:58). I made each one its own comparison, all A1 against A0, `equivalence`, `two_sided`:
- **K1, `result_agreement`, `abs`.** Ranked rotation/translation identity, including rank 1 and cutoff membership, with reconstructed coordinates within eps_xyz.
- **K2, `result_agreement`, `rel`.** Scores within atol + rtol·max(|s_CPU|, |s_GPU|). The real form has both an absolute and a relative component. The vocabulary allows one form, so I chose `rel` (see §4).
- **K3, `quality`, `abs`.** Each paired DockQ difference is at most eps_eval.

Settings for all three:
- **Margin source `unknown`.** No numeric tolerance has a basis yet (`s07` §D item 1; `s09/REQS.json` G3 `margin_source: unknown`). The seed asks for "justified numerical tolerances" (`BRIEF.md:13`) but gives no values. The card forbids deriving them from fresh four-case differences (T:263).
- **Stochastic `yes`.** GPU `docking.out` was not byte-reproducible: 39 distinct hashes over 40 files (`s07` §B). One GPU run therefore cannot separate GPU-vs-GPU repeat spread from the CPU/GPU difference.
- **Replicates `two_to_five`.** This matches s09 REQS G3. Run6's three retained blocks are the precedent.

### P3: execution acceleration (run 2; gated on P2)
- **K4: A1 against A0, `throughput`, `ratio_at_least`, `higher_better`, `rel`, `design_choice`.**
- The card's rule is that the 95% paired-block-bootstrap interval of the CPU/GPU complete-workflow wall ratio must have its lower bound above 1.05 (PC:29, `speed_threshold` 1.05 with basis DESIGN at PC:276–281; `ci_percent` 95; `bootstrap_draws` 10000). Writing the metric as throughput (A1/A0 ≥ 1.05) makes it identical to the wall ratio CPU/GPU ≥ 1.05.
- The 1.05 comes from neither the seed nor a publication, so the source is `design_choice`.
- Replicates are `six_to_ten`: 7 balanced blocks (PC:30, `timing_repeats` 7).
- The run6 screen medians were 2.311–2.570 (`s07` §A). That is a calibration screen, not a verdict.

### P4: is dense affordable at common budgets (run 2)
- **K5: A2 against `reference`, `runtime`, `non_inferiority`, `lower_better`, margin `none`, `design_choice`.**
- The reference values are the per-case tier seconds, frozen from the calibrated walls by the card's DESIGN formula (PC:97). Run6 gave 1aua 17.330 / 23.107 / 40.536 s, 1ax2 16.152 / 21.536 / 35.934, 1dv1 25.509 / 34.012 / 48.888, 1nr5 25.413 / 33.883 / 48.676 (`s07` §A).
- The criterion is that A2's complete workflow finishes within the tier. A dense arm that misses a tier is recorded as unavailable, never as DockQ 0 (PC:29, 107).
- Billed cost for P4 comes from the compute facts (§3), not from a separate comparison.

### P5 and P6: does dense improve recovery (run 2; gated on P2)
- **K6 (rank-1 DockQ, P5) and K7 (best-of-50 DockQ, P6): A2 against A1, `quality`, `superiority`, `two_sided`, `abs`, `design_choice`, `six_to_ten`.**
- The card's rule (PC:29) applies per case and eligible tier:
  - **gain** iff min(dense) − max(standard) > margin + 2·eps_eval;
  - **loss** iff max(dense) − min(standard) < −(margin + 2·eps_eval);
  - otherwise **unresolved**.
- margin = 0.01 DockQ (PC:270–274, basis DESIGN).
- I used `two_sided` with `superiority` because the same margin also declares a loss, and the seed requires negative results to be kept (`BRIEF.md:21`).
- K6 and K7 are separate, and rank 1 is never inferred from best-of-50 (`BRIEF.md:17`).
- The margin source is `design_choice` for the 0.01 term. The 2·eps_eval term inherits K3's `unknown` source.

## 3. Compute facts (G6)
`per_arm_wall` (complete workflow time), `per_arm_gpu_s` (GPU activity), `usd` (billed allocation cost) and `hardware_identity` (box type). The seed requires the first three (`BRIEF.md:19`). The fourth is needed because billed cost and timing depend on box type (`s09` G6; s11 `record_run_identity`).
- `usd` must be the billed allocation, meaning hours × price including setup, idle and failed work (PC:68). It is not compute seconds alone. Run6's `box.json` lacked the allocation end (`s09` G6).
- I did not request `gpu_memory`, `cpu_utilisation` or `energy`. The seed does not ask for them, and no part needs them.

## 4. Design, and what the vocabulary cannot carry
- **same_box `yes`, order `interleaved`.** All three arms run per case in randomized balanced blocks, scheduling seed 20261103 (PC:30). Tiers are only common if every arm runs on the same hardware.
- **inputs `two_to_five`.** These are the four pinned cases (`BRIEF.md:3`). Run 1 also needs synthetic, non-study fixtures for atol/rtol and eps_eval (T:263–264). Their count is not fixed in any file.
- **who_seals `science_step`.** The arms, the 0.01 and 1.05 values and the tier formulas are already sealed in the card. G2 carries the card's plan and decision rule intact (`s12` verdict). m5's seal agent needs a cited source for each tolerance, and these are design choices, not citations, so the seal agent should not fix them. The final tolerances are fixed by a science step after run 1, before run 2, as s12 did for bands.
- **Not expressible in FINAL.json, but required by the card.** G1 and G3 must still provide all of the following:
  1. **Ordered gating.** K4, K6 and K7 are evaluated only if K1–K3 pass. Otherwise they are reported as gated (PC:58; `s09` §6).
  2. **Combined abs + rel margin for K2.** `s09/REQS.json` G3 says `criterion: mixed`.
  3. **Worst-case range rule for K6 and K7.** The rule uses min/max over repeated endpoints with 2·eps_eval, not m5's sign test over seeds. The repeats are timing blocks, not seeds, and "deterministic repeats do not increase biological sample size" (PC:30). The sign-test default would apply the wrong rule.
  4. **Paired block bootstrap for K4.** 7 blocks resampled jointly across cases, 10000 draws (PC:30).
  5. **Per case and per tier reporting**, with unavailable arms recorded as unavailable.
  6. **Three arms per run.** m5's evaluate stage compares exactly two arms today.

## 5. What the owner must choose
**The tolerance source for K1–K3 (and with it the eps_eval term in K6 and K7).** This is the same choice s07 §D and s08 posed:
- (a) independent fixture analysis in run 1;
- (b) a declared engineering tolerance, labelled as not justified;
- (c) leave agreement unresolved. P3, P5 and P6 are then reported as gated.

Neither the seed nor a published source gives these values, so `margin_owner_input` is `yes`.

The owner may also confirm or replace two DESIGN margins: 0.01 DockQ and the 1.05 speed ratio. They are already sealed in the card, so they do not block anything.

Run 2 projects above USD 20 (plan USD 49.48, T:254), so it needs owner approval before launch (`s09` §5).

## 6. Predictions and outcomes
s12 sealed no predictions, so `outcomes.json` is empty. This step runs no test, so `predictions.json` is empty. Next action: stop, `contract_gap`. G1, G3 and G6 are still to be designed by the operator from `FINAL.json`.
