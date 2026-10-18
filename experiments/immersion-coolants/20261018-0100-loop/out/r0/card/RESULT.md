# Result

Picks 1 · PASS 0 · on-goal cards U4 0 · U3 0 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) Generative search for single-phase immersion coolants | REJECT (2 blocking) | seed | unsure | 3 | — → 5 | — → 4 | 5 | — | — → 1 | — | $874 at score · plan $874 · 3 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**immersion-coolants · Generative search for single-phase immersion coolants.** seed pick · compute tested: yes · plan expects: unsure · REJECT

**Question.** Does verifying more candidate coolants with GPU molecular dynamics keep raising the best figure of merit above known commercial single-phase fluids, or does it plateau?

**What is known.** Org-Mol ML-screened six million esters and experimentally validated two; it never MD-verified hundreds-to-thousands of candidates at once. No study measures whether the best MD-ranked coolant keeps improving as the number of MD-verified candidates grows from 100 to 10,000.

**Hypothesis.** Predictor-filtered molecular dynamics finds PFAS-free esters or hydrocarbons that beat commercial coolants [orgmol], and more candidates keep improving the best one.

**If compute is the lever.** Best cooling figure of merit keeps climbing with candidates verified, so more compute keeps finding fluids that beat commercial ones.

**If not.** Best figure of merit plateaus by a few hundred candidates, because predictor filtering and ~10% force-field error cap how high MD-ranked fluids score.

**Test.** Generate a million PFAS-free esters and hydrocarbons, ML-filter to a ranked shortlist, MD-verify the top 100, 300, then 1000 candidates' viscosity and thermal conductivity, and compare their cooling figure of merit to commercial fluids.

*Compute axis.* Candidate fluids verified by GPU molecular dynamics: 100–1,000 candidates, 3 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** MD pipeline reproduces n-hexadecane thermal conductivity 0.1444 W/m/K and viscosity 2.95 mPa/s near 300 K before scoring candidates. Tolerance: +/-25%.

**Would not show.** Result is a ranking and hit rate, not absolute fluid accuracy; one fluid class, no mixtures, no synthesis or lifetime testing.

*Cost.* Plans $874.15 of the $1,000 budget over 793 machine-hours, leaving $125.85. Main guess: MD throughput on one A6000 for a ~20-30k-atom organic liquid [p], measured after $26.16 of spend; the budget is reached if it is 1.2× lower. 1 cost flag in the block.

**Judges.** Dramaturg: REJECT (2 blocking). Decides at: $874 at score · plan $874 · 3 GUESS (critic: Decision needs best Mouromtseff at 100/300/1000 versus baseline, computed only in score after all levels).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-18 · filesystem $0.20/GiB-month [q]
Spend      anchor  Build the MD pipeline; reproduce n-hexadecane k and viscosity within +/-25%; measure the real MD throughput.  1x NVIDIA A6000 48GB $1.09/h  24 h  $26.16  line_anchor need 8 h in a 24 h box
           predictor  Fine-tune property predictors (dielectric, viscosity, thermal conductivity) on public data, holding out commercial fluids.  1x NVIDIA A6000 48GB $1.09/h  16 h  $17.44  line_predictor need 8 h in a 16 h box
           generate  Enumerate ~1M PFAS-free saturated esters and hydrocarbons, score with the predictor, rank by predicted Mouromtseff number.  1x NVIDIA A6000 48GB $1.09/h  4 h  $4.36  line_generate need 1 h in a 4 h box
           verify  MD-verify the top 100, then 300, then 1000 candidates (eight A6000s at once), computing density, viscosity, heat capacity and thermal conductivity.  1x NVIDIA A6000 48GB $1.09/h  749 h  $816.19
           score  Compute each candidate's Mouromtseff number and hit rate versus the commercial baseline; apply the decision rule.  $10
           verify  Longer 50 ns runs on the top 30 MD-ranked candidates  1x NVIDIA A6000 48GB $1.09/h  93.6 h [=]  $102.02  optional
           Planned $874.15 · unallocated $125.85 · with options $976.18 · cap $1,000
Rests on   MD throughput on one A6000 for a ~20-30k-atom organic liquid 500 ns/day [p] "| [ns/day] | System 1 | System 2 | System 3 | System 4 | System 5 | System 6 | ... A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2 | ... A40 | 277.0 | 731.8 | 268.1 | 122.3 | 34.9 | 19.0 |" · differs: my systems are 10-45k-atom pure ester/hydrocarbon liquids with rare output, not RNA or hexane benchmarks, System 1's very high output rate cuts speed ~2.6x, A6000 is the same GA102 chip as the A40 (277.0 ns/day), clocked slightly differently, I discount System 2's 691.7 to 500 ns/day for margin · measured in anchor ($26.16 spent by then) · budget reached at 433 (1.2× lower)
           predictor holdout R^2 expected 0.9 dimensionless [g] rests on: Org-Mol reports test-set R^2 above 0.92 for these exact properties · measured in predictor ($43.60 spent by then) · gate predictor holdout R^2 expected ≥ 0.85 in predictor (now 0.9, passes; uncut plan at it $874.15), else Fall back to a group-contribution ranking as the filter instead of the ML predictor. · budget not reached within 1000×
           candidates available after predictor filter 3,000 molecules [g] rests on: Org-Mol filtered 461 hard-threshold passes from 6M esters; ranking by predicted score always yields a top-N · measured in generate ($47.96 spent by then) · gate candidates available after predictor filter ≥ 1,000 in generate (now 3,000, passes; uncut plan at it $874.15), else Relax the dielectric-constant filter and re-rank before starting MD. · budget not reached within 1000×
           anchor fractional error on n-hexadecane conductivity expected 0.15 ratio [g] rests on: Mie force fields predict alkane viscosity to ~10% and thermal conductivity typically within a few percent · measured in anchor ($26.16 spent by then) · gate anchor fractional error on n-hexadecane conductivity expected ≤ 0.25 in anchor (now 0.15, passes; uncut plan at it $874.15), else Switch to a Mie (Potoff/TAMie) force field and rerun once; if it still fails, stop before spending on candidates. · budget not reached within 1000×
Scenarios  Throughput lands at the A100 System-1 level (267 ns/day) and overhead is 1.5x: only the 100 and 300 levels stay under $1000. → $1,821.56 (over budget)
Buys       candidates verified at level 3: 1,000 [d] · Throughput lands at the A100 System-1 level (267 ns/day) and overhead is 1.5x: only the 100 and 300 levels stay under $1000.: 1,000
           candidates verified at level 2: 300 [d] · Throughput lands at the A100 System-1 level (267 ns/day) and overhead is 1.5x: only the 100 and 300 levels stay under $1000.: 300
           candidates verified at level 1: 100 [d] · Throughput lands at the A100 System-1 level (267 ns/day) and overhead is 1.5x: only the 100 and 300 levels stay under $1000.: 100
           top candidates given longer refinement runs: 30 [d] · Throughput lands at the A100 System-1 level (267 ns/day) and overhead is 1.5x: only the 100 and 300 levels stay under $1000.: 30
Flags      error (quote) at numbers.throughput_ns_day.quote: 500 does not appear in the quote "| [ns/day] | System 1 | System 2 | System 3 | System 4 | System 5 | System 6 | ... A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2 | ... A40 | 277.0 | 731.8 | 268.1 | 122.3 | 34.9 | 19.0 |"; a value transformed from the page belongs in a DERIVED number
           error (quote) at numbers.anchor_k_hexadecane.quote: 0.1444 does not appear in the quote "298.15 144.43"; a value transformed from the page belongs in a DERIVED number
           error (quote) at numbers.anchor_eta_hexadecane.quote: 2.9523 does not appear in the quote "0.1 2952.3"; a value transformed from the page belongs in a DERIVED number
           error (quote) at numbers.ff_visc_err.quote: 0.1 does not appear in the quote "For saturated liquids, both Mie-based potential models (Potoff and TAMie) provide roughly 10% accuracy for linear alkanes, while deviations are closer to 20 to 50% for TraPPE-UA."; a value transformed from the page belongs in a DERIVED number
           thin headroom: the budget is reached if MD throughput on one A6000 for a ~20-30k-atom organic liquid is 1.2× lower
Full scale Verify 10,000 candidates by MD (the option's 10^4 level): $8,161.92 = 8.16× budget = 8.16× candidates verified at level 3 · inputs 1 c, 3 d, 1 p ([p] MD throughput on one A6000 for a ~20-30k-atom organic liquid)
Outside    human time writing the generator, filter and analysis code: 40 hours · human time running and reviewing results: 15 hours · local 4-core CPU for generation, filtering and scoring (not Lambda): 30 CPU-hours
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
ns_per_gpu_hour = throughput_ns_day / 24 = 500 / 24 = 20.8333 ns/hour
md_gpu_hours_per_candidate = (sim_len_ns / ns_per_gpu_hour) * overhead_factor = 12 / 20.8333 * 1.3 = 0.7488 GPU-hours
line_verify_100.hours = n_cand_100 * md_gpu_hours_per_candidate = 100 * 0.7488 = 74.88 h
line_verify_300.hours = (n_cand_300 - n_cand_100) * md_gpu_hours_per_candidate = (300 - 100) * 0.7488 = 149.76 h
line_verify_1000.hours = (n_cand_1000 - n_cand_300) * md_gpu_hours_per_candidate = (1000 - 300) * 0.7488 = 524.16 h
line_refine.hours = n_refine * refine_len_ns / ns_per_gpu_hour * overhead_factor = 30 * 50 / 20.8333 * 1.3 = 93.6 h
line_storage.usd = 50 * fs_usd_gib_month = 50 * 0.2 = 10 usd
fs_10k = n_cand_10000 * md_gpu_hours_per_candidate * a6000_usd_h = 10000 * 0.7488 * 1.09 = 8161.92 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:hypothesis` PARTIAL · page: "we apply the Org-Mol fine-tuned models to systematically screen out promising candidates for immersion coolants, which require low dielectric constant (strictly lower than 3.20 at room temperature for electrical safety), low kinematic viscosity (preferably lower than 12 cSt at 40 °C), high thermal conductivity (preferably higher than 0.140 W/m ⋅ K), and environmental friendliness." · note: orgmol supports screening esters as immersion-coolant candidates (predictor-first design), but it only covers synthetic esters, not hydrocarbons; it never states 'PFAS-free'; and it never claims the candidates 'beat commercial coolants' (it validates two but does not benchmark against commercial fluids). The MD part is the plan's own prediction (no source needed).
- sample 1 · `card:if_not` PARTIAL · page: "" · note: The plateau prediction itself needs no source, but '~10% force-field error' is a specific factual claim with no source cited, so that clause is unsupported.
- sample 1 · `card:left_open` UNSUPPORTED · page: "" · note: This is a factual claim about the literature ('No study measures...') with no source cited. Cannot be verified from any fetched page; unsupported.
- sample 1 · `card:anchor` UNREACHABLE · page: "Berger Bioucas, F. E., Rausch, M. H., Koller, T. M., & Fröba, A. P. (2024). Thermal Conductivity of Liquid Cyclohexane, n-Decane, n-Hexadecane, and Squalane at Atmospheric Pressure up to 353 K... International Journal of Thermophysics, 45(7)." · note: The DOI resolves only to the abstract/citation landing page; the quoted data table (T=298.15 K, λ=144.43 mW/m/K) is in the paywalled full text and does not appear on the fetched page, so the value cannot be verified. Also, the viscosity claim (2.95 mPa/s) is not even in the cited quote (which only lists λ).
- sample 1 · `src:berger2024` UNREACHABLE · page: "Berger Bioucas, F. E., Rausch, M. H., Koller, T. M., & Fröba, A. P. (2024). Thermal Conductivity of Liquid Cyclohexane, n-Decane, n-Hexadecane, and Squalane at Atmospheric Pressure up to 353 K Determined with a Steady-State Parallel-Plate Instrument. International Journal of Thermophysics, 45(7)." · note: Fetched page is only the abstract/citation; the quoted data table ('298.15 144.43') is not present, so the quote cannot be confirmed against the page.
- sample 1 · `num:throughput_ns_day` PARTIAL · page: "[ns/day] System 1 System 2 System 3 System 4 System 5 System 6  A100 267.5 691.7 265.8 129.1 38.8 23.2  A40 277.0 731.8 268.1 122.3 34.9 19.0" · note: The benchmark table appears and matches the quote (A40 System 1 = 277.0, System 2 = 731.8; A100 = 267.5/691.7), and page_setting (R-143a in hexane 20,248 atoms; RNA in water 31,889 atoms) is correct. But the page benchmarks no A6000 and states no 500 ns/day value; 500 is the producer's proxy, so the stated number for the A6000 setting is not on the page. · page value 277
- sample 2 · `card:if_not` UNSUPPORTED · page: "the accuracy of such methods relies on the applied force field and/or the algorithm applied in the ML model, as well as the quality and the size of the data set" · note: The plateau prediction is a plan prediction (no source needed), but '~10% force-field error' is a quantitative factual claim with no source, and no fetched page states any force-field error percentage (the orgmol page only says accuracy 'relies on the applied force field').
- sample 2 · `card:left_open` UNSUPPORTED · page: "(no source cited; no page fetched)" · note: 'No study measures X' is a factual claim about the literature with no citation attached; none of the fetched pages establishes this negative, so it is unsupported.
- sample 2 · `card:anchor` PARTIAL · page: "While the lowest T investigated was set to 278.15 K for n-decane and squalane, somewhat larger values of 283.15 K for cyclohexane and 298.15 K for n-hexadecane were selected considering the melting points. ... T (K) λ (mW·m−1·K−1) Cyclohexane n-Decane n-Hexadecane Squalane ... 298.15 144.43" · note: Thermal-conductivity half supported: n-hexadecane is the only fluid measured at 298.15 K and Table 2 gives 144.43 mW·m⁻¹·K⁻¹ = 0.1444 W/m/K (~300 K). The viscosity value 2.9523 mPa/s (and the 2.95 mPa/s in the text) appears nowhere on the cited page, which reports thermal conductivity only; the 'MD pipeline reproduces...' part is what the plan will do.

**Critic.**
- stakes 4 · `card:limits` "Result is a ranking and hit rate, not absolute fluid accuracy; one fluid class, no mixtures, no synthesis or lifetime testing." · Both outcomes change whether to scale GPU compute on MD verification, but the deployment choice awaits experimental validation not performed.
- lever 3 · `plan:predictions.noise_rule` "Run 2 independent replicas per candidate; a level-to-level best-score difference counts only if it exceeds the replica-to-replica standard error of the score." · Plan does not state whether the 5% threshold exceeds replica standard error, so effect versus noise cannot be told.
- verifiable 5 · `card:anchor` "MD pipeline reproduces n-hexadecane thermal conductivity 0.1444 W/m/K and viscosity 2.95 mPa/s near 300 K before scoring candidates. Tolerance: +/-25%." · Measured commercial-fluid data, independent of MD; anchor reproduces published n-hexadecane values within tolerance.
- open 5 · `card:left_open` "No study measures whether the best MD-ranked coolant keeps improving as the number of MD-verified candidates grows from 100 to 10,000." · Prior screened many esters and validated two, but did not MD-scale candidates from 100 to 1000.
- reshape 1 · `card:method` "none" · method none; no condition or pre-spend phase removes serial dependency, only independent candidates could be run concurrently.
- baseline NA · `card:method` "none" · restructuring.method is none, so sequential/copy baseline comparison does not apply.

**Producer says (not judged).** expected unsure (No published run has MD-verified thousands of immersion-coolant candidates, so whether the hit rate saturates or keeps rising is genuinely unknown.); compute_tested yes (The test varies the number of candidates verified by MD (100 to 1000), which is exactly what more parallel GPUs buy; each candidate is an independent simulation run one-per-GPU.); decides no; searched yes.

**Annotations.**
- quote at numbers.throughput_ns_day.quote: 500 does not appear in the quote "| [ns/day] | System 1 | System 2 | System 3 | System 4 | System 5 | System 6 | ... A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2 | ... A40 | 277.0 | 731.8 | 268.1 | 122.3 | 34.9 | 19.0 |"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.anchor_k_hexadecane.quote: 0.1444 does not appear in the quote "298.15 144.43"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.anchor_eta_hexadecane.quote: 2.9523 does not appear in the quote "0.1 2952.3"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.ff_visc_err.quote: 0.1 does not appear in the quote "For saturated liquids, both Mie-based potential models (Potoff and TAMie) provide roughly 10% accuracy for linear alkanes, while deviations are closer to 20 to 50% for TraPPE-UA."; a value transformed from the page belongs in a DERIVED number
- thin headroom: the budget is reached if MD throughput on one A6000 for a ~20-30k-atom organic liquid is 1.2× lower
- question: a sentence of 25 words
- hypothesis: a sentence of 21 words
- predictions.if_not: a sentence of 23 words
- test_summary: a sentence of 34 words
- novelty.left_open: a sentence of 21 words
- limits: a sentence of 21 words
- dramaturg findings failed G-find after a resample; decided as returned
- dramaturg-2 findings failed G-find after a resample; decided as returned

**Root question (null).** generative pipeline for discovery of single phase immersion coolants

**Producer file.** [producer.md](/home/hal/dev/interp/latent_open/experiments/immersion-coolants/20261018-0037-loop/out/r0/card/work/seed-1/seed/idea/63a459fc/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: quote at numbers.throughput_ns_day.quote: 500 does not appear in the quote "| [ns/day] | System 1 | System 2 | System 3 | System 4 | System 5 | System 6 | ... A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2 | ... A40 | 277.0 | 731.8 | 268.1 | 122.3 | 34.9 | 19.0 |"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: quote at numbers.anchor_k_hexadecane.quote: 0.1444 does not appear in the quote "298.15 144.43"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: quote at numbers.anchor_eta_hexadecane.quote: 2.9523 does not appear in the quote "0.1 2952.3"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: quote at numbers.ff_visc_err.quote: 0.1 does not appear in the quote "For saturated liquids, both Mie-based potential models (Potoff and TAMie) provide roughly 10% accuracy for linear alkanes, while deviations are closer to 20 to 50% for TraPPE-UA."; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: thin headroom: the budget is reached if MD throughput on one A6000 for a ~20-30k-atom organic liquid is 1.2× lower
seed:idea:seed: question: a sentence of 25 words
seed:idea:seed: hypothesis: a sentence of 21 words
seed:idea:seed: predictions.if_not: a sentence of 23 words
seed:idea:seed: test_summary: a sentence of 34 words
seed:idea:seed: novelty.left_open: a sentence of 21 words
seed:idea:seed: limits: a sentence of 21 words
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:limits
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg-2: card:limits: 0 findings
seed:idea:seed: dramaturg-2 (resample): card:limits: 0 findings
seed:idea:seed: dramaturg-2 findings failed G-find after a resample; decided as returned
```