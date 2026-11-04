# s27 predictions for the fixture run (sealed before launch)

**The run.** One m5 comparison-mode run with the following inputs:
- brief: `FIXTURE_BRIEF.md`;
- design: `fixture_design.json`.

**Arms.**
- F-A0: CPU standard.
- F-A1: GPU standard.
- F-A2: duplicate of F-A0.
- F-A3: duplicate of F-A1.

**Fixtures.** f1a19, f1dtd, f1glj and f1ht8, with 6 replicates and 1 warmup.

**Notation.** It follows `TOLERANCE_RULE.md` §0. F-Kn are the design's comparisons and M1–M6 are the rule's margins.

**How each prediction resolves.** Every statement resolves from these files of the run:
- `control/stages/*.json`;
- `C/comparison_scored.json`;
- `A/results/evaluate/comparison_compute.json`;
- the fetched `out/docking.out` files;
- for Q14, the operator's allocation record.

Each statement resolves to null only if the named file is absent for a reason other than the outcome it predicts.

| id | statement | resolves |
|---|---|---|
| Q1 | Reproduce PASS and evaluate PASS, and `C/comparison_scored.json` is written. | stage records; file exists |
| Q2 | Completeness Z holds: every one of F-K1…F-K12 has at least 4 present pairs for every fixture. | `comparison_scored.json` pairs |
| Q3 | Every present pair of F-K2, F-K5, F-K8 and F-K11 (CPU self-agreement on all four outputs) has `agrees` true. | pairs |
| Q4 | Every present F-K6 pair (GPU self-agreement, scores) has `agrees` true. | pairs |
| Q5 | Every present F-K3 pair (GPU self-agreement, transforms) has `agrees` true, i.e. flag G_T is false. | pairs |
| Q6 | Every present F-K1 pair (CPU vs GPU, transforms) has `agrees` true, i.e. flag X_T is false. | pairs |
| Q7 | The maximum `max_rel_error` over the present F-K4 pairs (CPU vs GPU scores) is ≤ 1e-4. | pairs |
| Q8 | The maximum `max_rel_error` over the present F-K6 pairs (GPU self) is ≤ the same maximum over F-K4 (cross). | pairs |
| Q9 | For every fixture, the per-fixture score maxima satisfy the analytic ceiling A_rel(N_f) of M3 step 6. | pairs; A0 `docking.out` header |
| Q10 | M3 (main K2 atol/rtol) is defensible under the rule. | rule applied |
| Q11 | M2 (main K1 eps_xyz) is defensible under the rule. | rule applied |
| Q12 | M4 (main K3 eps_eval) is defensible under the rule, and therefore so are M5 and M6. | rule applied |
| Q13 | M2, M3 and M4 are all defensible. | rule applied |
| Q14 | The allocation's USD (`comparison_compute.json` `allocation.usd`, or the final bill when recorded) is ≤ 10. | compute record |
| Q15 | Every one of the 112 scheduled invocations (7 rounds × 16) has status `ok`. | `comparison_compute.json` invocations |
| Q16 | The derived rtol of M3 (whether or not defensible) is ≤ 1e-3. | rule applied |

**Reasoning, stated before the run.**
- **CPU reproducibility.** CPU outputs were byte-reproducible in 20/20 run6 jobs (`science/s07/ASSESSMENT.md:116–118`), hence Q3 is high.
- **GPU reproducibility.** GPU `docking.out` gave 39 distinct hashes in 40 files (`:117`), hence Q4 is low. Whether the differences reach the transforms, through near-tie rank swaps or cutoff membership, is unknown. Hence Q5 and Q6 are near even, and Q6 is lower because a deterministic library difference (FFTW vs cuFFT, `-use_fast_math`) adds to the GPU's own noise.
- **Completeness.** The pipeline has not run an evaluator-bearing comparison on a box (run20 probed isolation with hostile parts, not this harness). Hence Q1, Q2 and Q15 are moderate.
