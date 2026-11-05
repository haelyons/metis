# s31 assessment: the owner decision s30 stopped on, and the main comparison (2026-11-05)

**Scope.** Offline: no network, no box, no git, no credentials. I wrote only into `science/s31/`.

**What I read:**
- s30 in full;
- s29 (`ASSESSMENT.md`, `fixture_design.json`, `_section.md`);
- s27 (`TOLERANCE_RULE.md`, `tolerance_rule.json`);
- s13 (`ASSESSMENT.md`, `FINAL.json`) and s15 (`SHAPES.json`);
- s07 `ASSESSMENT.md` (run6 walls and tiers) and s06 `CALIBRATION_BRIEF.md:313-427` (run6's commands and tier formulas);
- `dut/pipeline/m5/SCHEMAS.md:115-203` (Sealed comparison) and `score_comparison.py:21` (JSON Pointer form);
- the seed `m5/BRIEF.md`, the materials `m5/b01_materials/BRIEF_run1.md`;
- run9's `control/box.json`, `devbox_up.log` and `operator/OPERATOR_TAKEAWAY.md`.

For s01–s06, s08–s12, s14 and s16–s28 I relied on the summaries that s13, s27, s29 and s30 carry. I did not reread them in this step.

**Tool limits.** Shell use was partly denied, including `cp`, `cat` and Python. I wrote every file with the file tool. I checked these with `cmp`, `grep` and `jq`:
- `MAIN_BRIEF.md` bytes 1–39,538 equal `m5/b01_materials/BRIEF_run1.md` (cmp: identical up to that file's EOF).
- That file's first 1,714 bytes equal `m5/BRIEF.md` (cmp).
- The rest of `MAIN_BRIEF.md` equals `_section.md` byte for byte (`cmp -i 39538:0`).
- So `MAIN_BRIEF.md` = `BRIEF_run1.md` + `_section.md`: 39,538 + 10,558 = 50,096 bytes, sha256 `5b7f3ddf…f1be1c`. `_section.md` contains only the new section and exists for that check. It holds no design content.
- The design's lines for A0/A1 commands and env, the four outputs and the evaluator `spec` occur verbatim in `s29/fixture_design.json` (grep -F -x). The only command line that differs is A2's docking line.

## A. The decision s30 stopped on, and whether the standing decisions settle it

**What s30 stopped on** (quoted):
- `s30/ASSESSMENT.md:20`: "It cannot be launched blind, because the sealed hardware-identity clause (rule §3 step 4) conflicts with the hardware of K5's sealed references. I stop with **`needs_owner`** (§D)."
- `s30/ASSESSMENT.md:195`: "No box satisfies both. The launcher picks the box type, and NEXT.json cannot pin it. … Box pinning was raised as an owner decision in s28 §D and s29 §D and is still open. This is a decision, not a contract gap."
- Its options (`:198-207`):
  - (b) pin `gpu_1x_h100_pcie` and repeat the fixture run there (recommended);
  - (a) pin `gpu_1x_a100_sxm4`, with (a1) cross-hardware K5, (a2) an A100 timing calibration, or (a3) dropping K5;
  - (c) launch unpinned.

So the decision was **which box type the main comparison runs on, and whether to pin it**. It is a choice of method, not of cost (`s30_decision_class = method_choice`). s30's own sizing put the run under USD 20 on every box (`:233-240`).

**Do the standing decisions of 2026-11-03 settle it? Yes.** Three of them apply directly, and a fourth fact removes the remaining choice.

1. **Cost is approved.** All of s30's options fit inside the combined USD 100 ceiling: (b) at most USD 16.1 + 12.5, (a2) about USD 2 + 7.6, (c) at most 12.5 (s30 §E). "No further approval is needed for a main run that fits them." No option needs a cost decision.

2. **The consequence of an unmatched box is already decided by the owner and by a sealed rule.**
   - The owner: "tolerances are sealed before the main comparison, or the uncertainty is kept and the main comparison claims no tolerance it cannot defend."
   - s27 §3 step 4, sealed: "If any check fails, every margin is reported as 'not applicable to this main run (software or hardware differs from the fixture run)', and the outcomes are recorded unchanged."
   - Together these say what happens on a box that differs from run9's: the run still decides every comparison, and the report claims no tolerance for that hardware.
   - "A sealed rule is never changed after its result" forbids rewriting §3 step 4 now that run9's result exists. So the conflict s30 found is not open to a new choice. It is resolved by labelling, as both sealed texts already prescribe.

3. **The choice of test is delegated.** "The science agent picks the next justified test; stop only at the spend limit, a genuine owner decision, or when no justified test remains." Choosing among approved, in-ceiling tests is therefore mine.

4. **Pinning is not available on this route, so there is no owner choice left to make.**
   - `NEXT.json` has no box field (s30 `:195`; this step's `NEXT.json` schema).
   - This step's brief requires the design to fit "an A10, an A100 or an H100", which is the operator's own statement that the box is not pinned.
   - Options (a) and (b) presuppose a capability the route does not have, so an owner decision cannot make them executable without a launcher change. What remains is option (c), and points 1–3 already govern it.
   - An unpinned fixture rerun (option (b) without the pin) would not help either: it would not guarantee that the main run lands on the same box type as the rerun.

**Where I depart from s30's reading of option (c).** s30 said an unpinned launch "most likely spends the run without an agreement claim" (`:207`). That overstates the loss:
- **K1, transform identity, is an exact criterion, not a derived margin.** s27 M1: "M1 is a sealed criterion, not a derived tolerance, so it has no defensibility test." So it decides CPU/GPU agreement of the ranked rotations and translations on any box.
- **K4 (the 1.05 ratio) and K5/K9/K10 (run6 tiers) are DESIGN values and references, not s27 margins.** §3 step 4 does not touch them.
- **On a box whose identity equals run9's,** every margin applies. The box would need the same GPU name, driver, CUDA, executables and libraries; run9's box was `gpu_1x_a100_sxm4`, `R9/control/box.json`.
- **On a `gpu_1x_h100_pcie` box,** K5's tiers are on their own hardware frame (`s07/ASSESSMENT.md:75-76`), and the K8/K2/K3/K6/K7 margins are labelled not applicable.
- In every case the run decides some parts, and on two box types it decides most of them.

The cost of a less informative landing is at most USD 14.6 of the remaining USD 88.90.

**Conclusion.** The standing decisions settle it (`settled_by_standing_decisions = yes`). I do not stop. I do not write `OWNER_DECISION.md` (§C does not apply). The next test is the main comparison.

## B. The main comparison

**Files.**
- `main_design.json` is the design for `args.comparison`, in the exact schema of `SCHEMAS.md:117-141`. It is the only copy; sha256 `72c4d2fe…4eff48f`.
- `MAIN_BRIEF.md` is the run's whole brief.

### B1. Arms, inputs, outputs, evaluator

**Arms (s13 §1).**
- **A0:** F-A0's commands and env byte for byte (`s29/fixture_design.json:4-11`).
- **A1:** F-A1's commands and env byte for byte (`:13-20`).
- **A2:** A1 with `-r 3600` replaced by MEGADOCK's documented dense option `-D`. This is run6's argv (`s06/CALIBRATION_BRIEF.md:391`); run6's logs print "Set 54,000 rotational angles" (`s07:78`). It uses the same reconstruction command and env as A1.
- This satisfies s27 §3 step 2: the prepared paths come from `{spec:/prepared/…}`, so the arm text itself is unchanged.

**Inputs: the seed's four apo cases** 1aua, 1ax2, 1dv1 and 1nr5.
- Their sources, bytes, sha256 and natives are copied from `BRIEF_run1.md:56-158`.
- Prepared paths `data/inputs/<case>_R|L.pdb` and prepared sha256 come from `s06/CALIBRATION_BRIEF.md:336-344`.
- They are disjoint from run9's fixtures, which were holo 1a19, 1dtd, 1glj and 1ht8 (`s29/fixture_design.json:40-88`).

**Outputs:** run9's four outputs byte for byte (transforms, scores, coords, dockq).

**Evaluator:**
- `spec` byte for byte as run9's. Its `private_data` text is generic ("for each input, the native complex named in spec.reference"), so it needs no change.
- `timeout_s` 180.

**Metrics:**
- `wall` (trusted_wall, as in run9);
- `dockq_rank1`: sealed_extraction from `eval/dockq.json`, reduce `first`, expect_count 50;
- `dockq_best50`: the same with reduce `max`.
- The brief fixes their extraction rule as `{"kind": "json", "expr": ""}`. The empty pointer matches `POINTER` at `score_comparison.py:21`.

### B2. Comparisons: s13's K1–K7, with s13's ids kept

The contract allows one measure per comparison and ids `K[0-9]{1,2}`. So s13's K1 needs two entries (transforms and coords), and K5 needs one entry per tier. I kept s13's ids and added K8 (K1's coordinate part), K9 and K10 (K5's tiers 2 and 3). Each `given` refers only to earlier entries.

| design id | s13 id / part | arm vs | measure | criterion, unit, pairing, rule | margin / threshold / reference (sealed, design only) | missing | given |
|---|---|---|---|---|---|---|---|
| K1 | K1 / P2 | A1 vs A0 | transforms, `exact` | agreement, per_input_all, paired_replicate, all_pairs | null (s27 M1) | void | – |
| K8 | K1 (coords) / P2 | A1 vs A0 | coords, `elementwise_abs` | same | `{abs 0.001}` = eps_xyz (s30 M2) | void | – |
| K2 | K2 / P2 | A1 vs A0 | scores, `elementwise_abs_plus_rel_max` | same | `{abs 0.01, rel 0.0023}` (s30 M3) | void | – |
| K3 | K3 / P2 | A1 vs A0 | dockq, `elementwise_abs` | same | `{abs 0.001}` = eps_eval (s30 M4) | void | – |
| K4 | K4 / P3 | A1 vs A0 | wall | ratio_at_least, lower_better, pooled_mean, paired_replicate, bootstrap 0.95 | threshold 1.05, strict true (PC:29, s13:37) | void | K1, K8, K2, K3 |
| K5 | K5 tier 1 / P4 | A2 vs reference | wall | non_inferiority, lower_better, per_input_each, unpaired, all_pairs | margin null; tier1 17.330 / 16.152 / 25.509 / 25.413 s | fail | – |
| K9 | K5 tier 2 / P4 | A2 vs reference | wall | same | tier2 23.107 / 21.536 / 34.012 / 33.883 s | fail | – |
| K10 | K5 tier 3 / P4 | A2 vs reference | wall | same | tier3 40.536 / 35.934 / 48.888 / 48.676 s | fail | – |
| K6 | K6 / P5 | A2 vs A1 | dockq_rank1 | superiority, two_sided, per_input_each, unpaired, all_pairs | `{abs 0.012}` = 0.01 + 2·eps_eval (s30 M5) | void | K1, K8, K2, K3 |
| K7 | K7 / P6 | A2 vs A1 | dockq_best50 | same | `{abs 0.012}` (s30 M6) | void | K1, K8, K2, K3 |

Notes on the table:
- Tier values are in the order 1aua / 1ax2 / 1dv1 / 1nr5. They come from `s07/ASSESSMENT.md:56-59` by the formulas sealed at `s06/CALIBRATION_BRIEF.md:421`, as s13:44 froze them.
- **Shapes match s15** (`SHAPES.json`):
  - K1–K3: per_input_all, paired, all_pairs.
  - K4: pooled_mean, paired, bootstrap, ratio of means.
  - K5: per_input_each, unpaired, all_pairs, previous-run reference.
  - K6/K7: per_input_each, unpaired, all_pairs.
- **K6/K7 apply the card's worst-case range rule** (s13:51-53). With unpaired all_pairs:
  - lo = min(A2) − max(A1) and hi = max(A2) − min(A1) (`SCHEMAS.md:193,196`);
  - "supported, sign higher" is gain;
  - "supported, sign lower" is loss;
  - "not supported" means both ranges lie within ±0.012;
  - otherwise "inconclusive" (the card's "unresolved").
- **K4 matches the card** (`SCHEMAS.md:193`): with lower_better the ratio is mean(A0)/mean(A1), the CPU/GPU workflow ratio, and the lower bound must exceed 1.05.
- **K5's "fail" rule** records a dense invocation that has no value as not available at that tier. With `timeout_s` 300 above every tier (largest 48.888 s), a timed-out dense run did exceed the tier. s13:45: "never as DockQ 0".
- **Margins:** every margin is exactly as s30 derived it from s27's sealed rule (s30 §B: eps_xyz 0.001, atol 0.01 with rtol 0.0023, eps_eval 0.001, K6/K7 0.012). No other margin is introduced.
- **Where the sealed numbers live.** Every sealed number is in the design's `comparisons`, `timeout_s`, `budget_s`, seeds and `evaluator.timeout_s`, which the contract keeps out of the view (`SCHEMAS.md:143`). These are the margins, the threshold, the confidence, the reference values, the timeouts, the budget and the seeds.
- **Screen check.** I grepped the view (jq projection of `arms, inputs, outputs, metrics, evaluator.{what,spec}, replicates, warmup`) and `_section.md` for every sealed number and for "margin", "threshold", "confidence", "expected": 0 matches.

**Wall definition.**
- The trusted wall includes the evaluator part (`SCHEMAS.md:125`). That matches the card's tier definition, M = W + E (`s06:421`).
- It also enters K4. There, an added evaluator wall on both arms pulls the ratio toward 1 (s07:99), which makes the test conservative.

**K6/K7 per tier.** A2's output does not depend on the tier; a tier only decides availability. So the report reads K6/K7 for case c at tier k only where K5/K9/K10 is supported for c at tier k. Elsewhere dense is "unavailable at tier k". I fix this reading rule now, before the run.

### B3. Sizing

**Invocations:** 3 arms × 4 inputs × (7 replicates + 1 warm-up) = **96**, the card's 7 blocks plus 1 warm-up (s13:39).

**Per-invocation cost.** I take about 36 s outside the parts, from this step's brief and run9 (s30 §A: 3,978.5 s / 96 = 41.4 s, minus the parts' 12.6 s), plus the parts' walls:
- **Arm parts on the seed cases** (run6 per-case maxima, `s07:38-41`):
  - A0 mean 11.88 s (9.58 / 9.00 / 14.43 / 14.52);
  - A1 3.64 s;
  - A2 19.57 s;
  - mean over arms 11.70 s.
- **Evaluator:** run9's mean 424.0 / 96 = 4.42 s; maximum 7.23 s.

**Pre- and post-evaluate time:**
- run9's intake plus reproduce took 588 s;
- run9's allocation of 1.338 h exceeded its stage walls (4,567 s = 1.269 h) by 0.07 h;
- I take 0.25 h for both (0.45 h pessimistic).

| case | per invocation | evaluate (96 inv. + ≈60 s users/versions) | total h | H100 (3.29/h) | A100 (1.99/h) | A10 (1.29/h) |
|---|---|---|---|---|---|---|
| expected, H100/A100 | 36 + 11.70 + 4.42 = 52.1 s | 5,063 s = 1.41 h | 1.66 | USD 5.5 | USD 3.3 | – |
| pessimistic, H100/A100 (arms ×1.5, eval 7.2 s, overhead 45 s) | 69.8 s | 6,761 s = 1.88 h | 2.33 | USD 7.7 | USD 4.6 | – |
| expected, A10 (A0 ×1.6, GPU arms ×3, eval ×1.6) | 36 + 29.5 + 7.1 = 72.6 s | 7,030 s = 1.95 h | 2.20 | – | – | USD 2.8 |
| pessimistic, A10 (and ×1.5, eval 10 s, overhead 45 s) | 99.3 s | 9,593 s = 2.66 h | 3.11 | – | – | USD 4.0 |
| worst: budget exhausted | – | 14,400 s = 4.0 h | 4.45 | USD 14.6 | USD 8.9 | USD 5.7 |

Notes on the table:
- **A10 factors.** On the A10 (run7, s29:188), the largest arm wall measured was 39 s, against run9's A100 maximum of 24.0 s for A0 on f1ht8. That gives ×1.6 for the CPU. For the GPU arms I take ×3 (s30's assumption), because A2 has never been timed on an A10 or an A100.
- **Settings:**
  - `budget_s` = 14,400. It is below 19,800, and leaves 1.51× headroom over the A10 pessimistic case and 2.13× over the H100/A100 pessimistic case. Budget plus pre-evaluate time (≈1,260 s, s29:193) is 15,660 s, below a 19,800 s run ceiling.
  - `timeout_s` = 300. That is 3.4× the pessimistic A10 dense wall (19.57 × 3 × 1.5 = 88 s) and 41× run6's largest dense wall.
  - `evaluator.timeout_s` = 180. That is 25× run9's largest evaluator wall.
  - `bootstrap_resamples` = 10,000 (PC:30).
  - `order_seed` 20261103 is the card's scheduling seed (s13:65). `bootstrap_seed` is 31311.
- **Why the budget is generous.** Agreement comparisons with `missing: void` are voided by any missing pair (`SCHEMAS.md:194`). Running out of budget would therefore void the agreement gate.
- **How it holds on each box.** Every case stays below the 6 h run limit, with at most 4.45 h even if the budget is exhausted, and below USD 20 on each box type:
  - **A10:** the slowest GPU arms. The pessimistic case is 3.1 h and USD 4.0.
  - **A100:** dense is untimed there. Even at ×3 the A10 bound covers it, at 2.3–3.1 h and USD 4.6–6.2.
  - **H100:** the arms were measured there (run6). The worst case is USD 14.6.

**Projection:** about 1.7–2.3 h, USD 2.8–7.7 depending on box. The ceiling is 4.45 h and USD 14.6.

### B4. What each result decides for the seed's question

The decision rules are as sealed in the design. The labels below are fixed now.

**Agreement at identical settings (P2: K1, K8, K2, K3, per input, all replicates):**
- **All four supported on an input:** CPU and GPU agree at identical settings on that case. That means identical ranked transforms, coordinates within one PDB unit, scores within atol + rtol·max, and DockQ within eps_eval.
- **Any of them not supported:** a negative agreement result for that case, recorded as is.
  - run9's flag G_T was false: GPU transforms were self-reproducible on fixtures (s30 §B M1). So a K1 failure can be attributed to CPU/GPU disagreement.
  - A K2 failure with K1 supported means score differences beyond the fixture-derived bound.
- **Void:** missing values; that case's agreement is unresolved.
- **Gating:** K4 is void (`not_eligible`) unless all four are supported on every case. K6/K7 are void per case where agreement failed.

**Execution acceleration (P3: K4):**
- **Supported:** the GPU complete workflow is faster than the CPU's, with the 95% bootstrap lower bound of mean(A0)/mean(A1) above 1.05.
- **Not supported:** the upper bound is ≤ 1.05, so there is no acceleration at workflow level.
- **Inconclusive:** neither.
- **Void:** the agreement gate failed, or values are missing.

**Affordability of dense at common budgets (P4: K5, K9, K10, per case and tier):**
- **Supported:** every dense replicate finished within the tier, so dense is affordable at that tier for that case.
- **Not supported:** every replicate exceeded the tier, or dense failed, so dense is unavailable there.
- **Inconclusive:** some replicates are above the tier and some below, so availability is not established.

**Quality from additional search (P5 rank-1: K6; P6 best-of-50: K7, per case):**
- **Supported, sign higher:** dense improves by more than 0.012 DockQ in the worst case.
- **Supported, sign lower:** dense worsens it. This is a negative result and is kept.
- **Not supported:** no difference beyond 0.012.
- **Inconclusive:** unresolved.
- **Void:** not eligible because agreement failed for that case.
- Rank-1 is never inferred from best-of-50. Conclusions are limited to these four cases, with no biological inference (seed lines 17, 23).

**Applicability, decided now from the sealed rules.** After the run, the next step applies s27 §3 step 4 against run9's `Y.system` (s30 §A):
- **Identity holds:** every margin applies as sealed.
- **Identity fails:** K8, K2, K3, K6 and K7 are reported with "margin not applicable to this main run (software or hardware differs from the fixture run)", their outcomes unchanged. Agreement and quality are then claimed under tolerances that were not validated for this hardware, which is the uncertainty the owner allows to be kept. K1 (exact) and the K4 threshold are unaffected. K4's eligibility, however, rests on the not-applicable margins, and the report says so.
- **K5/K9/K10:** reported on the same hardware frame when the box is `gpu_1x_h100_pcie` with run6's CPU model (Xeon Platinum 8480+). Otherwise they are reported as cross-hardware against run6's tiers.
- **Uncertainties that carry over** (s30 §B): no independent check of DockQ's absolute accuracy (s27 §4), and disclosure of grid-size extrapolation (§3 step 5).

**How many main runs the question needs: one.** All seven of s13's comparisons fit one design and one allocation: 10 entries of the 12 the contract allows, and 96 invocations. No comparison depends on another run's outcome. If the box differs from run9's, the agreement tolerances stay as a kept uncertainty. A further run would not be justified automatically, because the box cannot be pinned on this route; whether to pursue one is the next step's call, made from the result.

## C. Not applicable

The standing decisions settle s30's stop, so I write no `OWNER_DECISION.md`.

## D. Do the main runs fit the USD 88.90 left?

Yes:
- **Worst case** (budget exhausted on an H100): 88.90 − 14.6 = **USD 74.3** left.
- **Expected:** 88.90 − 5.5 = USD 83.4 on an H100; 88.90 − 3.3 = USD 85.6 on an A100; 88.90 − 2.8 = USD 86.1 on an A10.
- Even a complete repeat of this run at the worst case would leave 74.3 − 14.6 = USD 59.7.
- The run projects below the USD 20 line, and within the 6 h limit on every box type.

## E. Narrowing

Unchanged: no narrowing (`NARROWING.md`). Every part of the seed's question (agreement, acceleration, affordability, rank-1 and best-of-50 recovery) is in the design. The hardware labels in §B4 are reporting rules that were already sealed (s27 §3 step 4) or are stated here before the run. They drop no part of the question.

## F. Predictions and outcomes

- s30 sealed no predictions, so `outcomes.json` is `{"items": []}`.
- 20 predictions for the main run are in `PREDICTIONS.md` and `predictions.json`. The operator seals them by committing them before launch.
