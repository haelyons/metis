# Run9 scale assessment

Authorized reader; 2026-11-01. Read-only assessment of existing records. No workload, network fetch, box contact or git command performed. Writes confined to `run9_scale/`.

Requested `run9/A/` is physically `run9/agent/` in this checkout. Paths below are relative to `experiments/blind-01/m5/`, except explicitly identified repository paths. Repository scoring files are at `../../../dut/pipeline/m5/`, three parent traversals from this working directory. Directory sizes inspected before targeted output reads: reproduce approximately 2.1 GB, profile approximately 4.2 GB. No large decoy tree or archive was read.

Run9 establishes executable baseline calibration on eight selected real benchmark cases, an acceptable DockQ pose, and exact agreement with two dataset composition counts. **“Reduced-scale baseline calibration” fairly describes this result**, provided scale means fewer cases and calibration means observed execution, scoring and timing. It does not establish a reproduced published FroDock success rate, benefit from increased parallelism, or identity of mirror materials with original distribution. Per-case configuration retained 50 candidates and eight MPI ranks; candidate count has no published default established in intake.

## 1. Items and reference comparisons — recorded/measured

`run9/agent/intake/anchors.json` contains three items: **one gated anchor and two ungated references**. `run9/agent/results/reproduce/anchors_scored.json` records `anchors_passed=1`, `anchors_total=1`, `references_total=2`, `all_passed=true`.

| Item | Comparison | Published value | Measured | Tolerance | Gate |
| --- | --- | ---: | ---: | --- | --- |
| `dockq_acceptable_threshold` | `>=` | 0.23 | 0.9775788581560528 | null; ignored | pass |
| `pinder_s_system_count` | `==` | 250 | 250 | null | reference only |
| `pinder_s_apo_paired_count` | `==` | 93 | 93 | null | reference only |

Both reference differences equal zero. They therefore satisfy any hypothetical nonnegative equality tolerance, including zero; status `references_within_tolerance=all` means this exact-match fact. No actual tolerance is assigned retrospectively. References remain unscored (`passed=null`).

Repository `dut/pipeline/m5/SCHEMAS.md`, intake and deterministic anchor scoring sections, and `score_anchors.py:score()` agree: a reference has equality comparison and null tolerance. Inequality anchors compare directly to threshold and ignore tolerance. A null tolerance does not make an inequality item a reference. Thus the premise “within tolerance” needs correction here: this pass is a **threshold pass**, not agreement within an error band around a published outcome.

## 2. What anchor measures — measured and interpretation

`run9/agent/harness/run_anchors.sh` defines measurement as maximum DockQ across all scored decoys: best-of-50 per job, then maximum across 16 jobs. `out/anchors_details.json` under reproduce repeats that definition. This measures pose recovery, a main scientific quantity named in `intake_mirror/BRIEF_run5.md` and `run9/agent/intake/benchmark.json:outcome_definition`. Status `anchor_quantity=main` classifies DockQ, not a count or runtime. The gated aggregation tests existence of one acceptable pose, not benchmark-wide recovery, ranking quality, or the effect of parallel computation.

Read-only CSV analysis of `run9/agent/results/reproduce/out/results/frodock_metrics.csv` found 800 selected PINDER-S rows and 800 unique `(id, monomer_name, model_name)` tuples. CSV has 6,542 total rows because evaluator also reports other subsets and missing-system penalties; those are not 6,542 generated poses.

Maximum occurs at `1nr5__A1_P07547--1nr5__A2_P07547`, **holo**, `model_1`: DockQ 0.9775788581560528, iRMS 0.31775161623954773, LRMS 0.6186391711235046, Fnat 0.9809523809523809, CAPRI `High`. This is bound-component redocking, not independently unbound input. `out/anchors_details.json` additionally reports:

| Pairing | Jobs | Top-1 DockQ >= 0.23 | Best-of-50 DockQ >= 0.23 |
| --- | ---: | ---: | ---: |
| holo | 8 | 6 | 8 |
| apo | 8 | 4 | 7 |
| total | 16 | 10 | 15 |

These are selected-case observations, not population estimates. No failed selected jobs were penalized. FroDock ranking and oracle best-of-50 differ. The generated leaderboard includes penalties for unrun cases; its full-subset percentages are not measured full-benchmark performance. Its CAPRI classifications also must not be conflated with the brief's DockQ cut-off: intake explicitly distinguishes those definitions.

## 3. Scale and published values — recorded, inferred, unknown

`run9/agent/intake/EXECUTION.json:representative_scale` fixes first eight lexicographically sorted IDs among 93 paired-apo PINDER-S cases, each with holo and apo input: 16 docking jobs, 50 poses/job, **800 poses**. Selection is deterministic and preregistered, not a random sample. `out/results/frodock_setup.csv`, resolved `out/run_command/frodock_config.yaml`, log configuration and 800 selected CSV rows confirm execution. MPI rank count stays eight; no per-case length, grid/problem size or search-step reduction is established.

Reduction is **number of benchmark cases/samples**: `93/8 = 11.625x` relative to prioritized paired-apo set; `250/8 = 31.25x` relative to all PINDER-S cases. Both map to `10_to_100x`. Full set cannot supply paired apo for all 250. Published configuration also permits predicted monomers, omitted at this calibration scope; that is additional input coverage, not evidence that individual problems or candidate budgets were shrunk. AAV challenge was deferred explicitly in EXECUTION.json.

**Unknown whether published numerical outcomes were obtained at published scale.** Intake `baseline.json:published_baseline_numbers.available=false` and `benchmark.json:published_numbers_available` say no published FroDock DockQ or success-rate values were located. The three listed values are a classification convention and full-dataset composition counts. Counts describe full release, but are not docking experiments performed at a particular scale. Threshold 0.23 is not a reported full-scale FroDock result. No published per-method trial count, candidate default, seed schedule or empirical expected maximum is established. Status `published_values_at_published_scale=unknown` preserves this distinction; it does not assert that published results were obtained at reduced scale.

## 4. Expected value and scale — inference

Acceptance cut-off **0.23 stays constant**. Measured statistic is nevertheless a maximum over cases and candidates, not an unbiased estimate of a fixed published mean. Expanding a nested collection while retaining existing poses makes maximum nondecreasing. Under a stochastic model its expectation can increase as opportunities increase; for independent identical candidates with CDF F, `P(max of n <= x) = F(x)^n`. This illustrative formula is not an independence assumption about these docking poses. Cases differ, and selection is sorted rather than random.

Hence `anchor_expectation=scale_dependent` describes measured maximum, not the cut-off. Larger scale need not merely reduce sampling noise, and could leave observed maximum unchanged. Per-case DockQ itself need not change when other cases are added. Numerical expected maximum and its variance remain unknown.

## 5. Tolerance, noise and source — undefined/unknown

There is **no tolerance width**: anchor has `comparison=">="`, `tolerance=null`, `uncertainty=null`. No meaningful classification as much wider/comparable/narrower exists; status `tolerance_vs_noise=unknown`. No tolerance source exists in evidence; `tolerance_source=unknown`. Cut-off source is known separately: brief's DockQ/CAPRI community convention, recorded by intake without fetching its primary publication. It is neither published uncertainty nor an intake-created error band.

`benchmark.json:scoring_and_repeatability.determinism` says complete-run determinism was **not established**; FFT search is deterministic in principle for fixed inputs, but MPI ordering can matter. DockQ evaluation is deterministic conditional on fixed decoys. `data.json:seeds` records no published seed values and no seed-parameterized FroDock stage; `harness/run_evaluation.sh` likewise says a recorded seed is only exported, not consumed by FroDock. Eight sorted cases are not independent replicate runs or a basis for a standard error. Do not use `1/sqrt(n)` to manufacture noise or label entire pipeline proven deterministic.

## 6. Margin — measured gap, undefined tolerance fraction

Threshold surplus is `0.9775788581560528 - 0.23 = 0.7475788581560529` DockQ units. Measured value is approximately 4.25034 times cut-off. Neither number is a fraction of tolerance. There is no `abs(measured-published)/tolerance` to calculate and no “percent tolerance used”; status `margin=unknown`. Treating null as zero or treating 0.23 as a tolerance would change scoring semantics.

## 7. Defect sensitivity — unknown probability, limited structural inference

No controlled wrong-data, wrong-parameter or software-version perturbation comparison is available in specified records. No defect size/distribution or noise model is established. Likelihood of detection at run9 scale or published scale is therefore **unknown** for both status fields.

Gate's limits can still be inferred. All candidate DockQ scores would need to fall below 0.23 to fail this scalar threshold. Fifteen jobs currently supply at least one acceptable pose. A defect confined to an unselected case is untested; one affecting a low-scoring pose, ranking alone, or a nonwinning job can leave gated value unchanged. A severe defect could remove every acceptable pose. Dataset-count references check composition counts and are ungated; they do not authenticate coordinates or scoring potential. These examples establish possible blind spots, not a probability for an unspecified plausible defect.

At expanded nested scale, keeping original passing poses preserves this existential pass; adding more cases cannot by itself make maximum fail. New per-case outcomes could expose case-specific defects if inspected or separately gated, but merely running existing scalar threshold over more poses does not establish stronger defect detection. No basis to claim a full-scale run makes this check likely to detect material differences.

## 8. What full scale adds; provenance — inferred and unknown

Running all 93 prioritized paired-apo cases with same pairings would add 85 cases, 170 jobs and 8,500 poses: 186 jobs and 9,300 poses total. It adds observed case coverage and allows top-1/best-of-50 summaries for that complete finite subset instead of eight sorted cases. Extending holo to all 250 adds broader benchmark coverage. These are useful scientific additions; they are not only reduced noise. They would not establish improvement from parallelism without a comparative experiment.

No published FroDock result table or uncertainties were established, so whether expansion enables a **tighter comparison with published outcomes, additional published quantities, or both** remains unknown. Existing gate stays same and may saturate. Status `full_scale_adds=unknown` reflects that the allowed categories describe published-value comparisons; none directly represents the established benefit, broader observed case coverage. It does not mean full scale has no benefit. AAV results require separate extraction/protocol work; increasing case count alone does not produce them.

**Full scale does not resolve provenance** (`full_scale_resolves_provenance=no`). `intake_mirror/REPORT.md`, its `status.json` (`alternative=unverified_mirror`, `refetch=match`), and owner rule in `intake_mirror/BRIEF_run5.md` retain uncertainty. No authenticated original FroDock package hash/member manifest or exact study-era scoring/software pin was established. Mirror archive SHA-256 `91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4` and required `bin/soap.bin` SHA-256 `791f31ec8ef1ef1466092b425638e926755519c9626f5678ca675ef6c76234fc` identify used bytes, not their equality with original. Outcome agreement, however broad, tests observed behavior rather than copy identity.

Executed path also includes recorded adapter fixes (`harness/pinder_frodock_fixes.patch`; copied to `out/setup/pinder_frodock_fixes.applied.patch`): enum membership, pandas CSV API, input/path staging, binary path separator and glob expansion. `run_command.sh` restores blank ligand HETATM chain labels before evaluation; final log reports 100 models and 2,700 atom labels restored, with originals archived and change manifest retained. `out/setup/setup_record.json` records build/environment deviations and labels four FroDock binaries compiled. These records support describing precisely which baseline ran; they do not establish equivalence to an untouched original installation.

## 9. Published-scale serial runtime — measured basis and conditional extrapolation

`out/anchors_details.json:summary.docking_wall_s_sum = 4536.183000564575 s` for 16 sequential jobs. Per-job observed range **40.5–582.405 s**, mean `4536.183000564575/16 = 283.51143753528595 s`. Holo sum 2346.6840002536774 s; apo sum 2189.499000310898 s. Logger span ends at “Copying the results,” so includes stage execution but excludes subsequent copying/scoring overhead.

Final successful log `run9/agent/results/reproduce/0116-anchors.log` starts `2026-11-01T07:13:43Z`, ends `08:30:56Z`: **4,633 s = 1.287 h** wall for command plus extraction/reporting. Last docking copy timestamp is `08:29:28.591`; scoring completes before final timestamp. Log has `PREDICT_EXIT=0`, `EVAL_EXIT=0`; intermediate Python logging-format errors did not terminate execution. Log-file modification/fetch times are later and must not replace internal execution timestamps. Earlier repaired attempts and transfer time are excluded from steady-state projection.

Same-box serial here means jobs executed sequentially **with eight MPI ranks per job**, not a one-core execution. `out/setup/setup_record.json` records Intel Xeon Platinum 8480+, 26 visible host CPUs, Open MPI 4.1.2, Python 3.10.12; command exposes zero GPUs.

| Target, retaining 50 poses/job | Jobs | Factor versus 16 | Docking projection | Proportional 4,633-s wall projection |
| --- | ---: | ---: | ---: | ---: |
| 93 paired-apo cases, holo + apo | 186 | 11.625 | 14.648 h | 14.961 h |
| 250 holo + 93 paired apo | 343 | 21.4375 | 27.012 h | 27.589 h |
| Above plus 250 predicted jobs, if available/configured | 593 | 37.0625 | 46.701 h | 47.697 h |

Arithmetic: multiply measured seconds by `target_jobs/16`, divide by 3,600. First row is direct expansion of intake's prioritized design. Second and third are conditional coverage scenarios, not evidence of a uniquely specified published experiment. `published_scale_runtime=12_to_48h` encodes central extrapolation, chiefly approximately **15 h** for 93 paired cases. Proportional wall estimate includes observed ancillary work, not an independently measured linear scoring model. Setup record reports 239 s setup including 12 s preprocessing; do not multiply whole setup/download time by case factor or add failed repair costs as scientific runtime.

Actual runtime, uncertainty bounds, a strictly single-core runtime and AAV runtime remain unknown. Eight sorted cases may not represent size/cost distribution of remaining cases; measured job costs vary about 14.4-fold. Full predicted scenario lies close to 48 h and cannot reliably be assigned below that boundary in advance. No extrapolation removes that uncertainty or establishes full-scale feasibility under the earlier 12 h run ceiling.
