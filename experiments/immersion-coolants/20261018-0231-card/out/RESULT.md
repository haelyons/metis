# Result

Picks 1 · PASS 0 · on-goal cards U4 0 · U3 0 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) MD verification inserted into Org-Mol's ester shortlist before synthesis | REJECT (1 blocking) | seed | if_lever | 5 | — → 5 | — → 3 | 5 | — | — → 5 | 3 | $984 at verify_300 · plan $984 · 3 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**IC-V3 · MD verification inserted into Org-Mol's ester shortlist before synthesis.** seed pick · compute tested: yes · plan expects: the lever · REJECT

**Question.** Does molecular-dynamics verification of viscosity and thermal conductivity reorder a machine-learning ester shortlist, or merely confirm it, and does the best coolant keep improving?

**What is known.** Org-Mol screened 461 monoester cooling candidates with a transformer and measured only two by synthesis; none were molecular-dynamics-verified for viscosity or thermal conductivity [s1]. No published work runs Green-Kubo viscosity and thermal conductivity over a 100-to-1000 candidate ester shortlist, so whether MD reorders the ML ranking is untested.

**Hypothesis.** Molecular dynamics will reorder the shortlist because the machine-learning viscosity error (22.5% MAPE) exceeds MD's, so better esters appear only after verification.

**Restructuring.** Each candidate's viscosity waits on one long trajectory; the ranking waits on 100, 300, then 1000 candidates. Run each candidate as parallel short replicas on separate GPUs and block-average the Green-Kubo integrals, so wall-clock shrinks by the replica count.

**If compute is the lever.** By 100 candidates the replica ranking matches the sequential baseline and diverges from ML; the best figure keeps improving through 1000.

**If not.** Replicas only match the sequential baseline by 300 candidates, and MD then merely confirms the ML ranking, unchanged from 100 through 1000.

**Test.** Rent an 8-GPU A100 node; run OPLS-AA Green-Kubo viscosity and thermal conductivity for the top 100 then 300 of Org-Mol's 461 monoesters; compare ML-vs-MD rank correlation and whether the best cooling figure keeps climbing; time a 45 ns single-trajectory baseline against parallel 5 ns replicas.

*Compute axis.* MD-verified monoester candidates: 100–1,000 candidates, 3 levels. Closest prior: 0 [s1], beyond it.

**Check first.** Green-Kubo MD (OPLS-AA) reproduces Org-Mol Ester 1's measured 40 C viscosity 6.41 cSt Tolerance: ±25% on viscosity; ±20% on thermal conductivity 0.141 W/m K.

**Would not show.** Shows single-phase ranking only, under one force field and 15 ns sampling; no synthesis, dielectric, flammability, compatibility, or stability checks.

*Cost.* Plans $984.16 of the $1,000 budget over 61.8 machine-hours, leaving $15.84. Main guess: GROMACS throughput on A100 for a 20,000-atom liquid [p], measured after $20 of spend; the budget is reached if it is 1.0× lower. 1 cost flag in the block.

**Judges.** Dramaturg: REJECT (1 blocking). Decides at: $984 at verify_300 · plan $984 · 3 GUESS (critic: Decision rule uses ML-vs-MD Spearman and 100-to-300 figure climb; verify_300 produces both).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-18 · filesystem $0.20/GiB-month [q]
Spend      anchor  Green-Kubo run of Ester 1 and Ester 2 (5 replicas x 10 ns each) plus a 1 ns throughput benchmark of the ~20,000-atom box  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  1.26 h [=]  $20  time box; need 1.26 h (margin 1.00×)
           verify_100  top-100 candidates, 3 ns equilibration + 3 x 5 ns Green-Kubo each, 8 candidates at a time  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  20.2 h [=]  $321.38  time box; need 20.2 h (margin 1.00×)
           verify_300  candidates 101-300, same protocol  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  40.4 h [=]  $642.75  time box; need 40.4 h (margin 1.00×)
           verify_300  box files, Green-Kubo autocorrelations and logs (~2 GiB kept ~60 h)  [=]  $0.03
           Planned $984.16 · unallocated $15.84 · cap $1,000
Rests on   GROMACS throughput on A100 for a 20,000-atom liquid 268 ns/day [p] "| A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2 |" · differs: system: R-143a-in-hexane 20,248 atoms vs a ~20,000-atom saturated monoester box, force field: benchmark AMBER-family vs my OPLS-AA, benchmark has a very high output rate, which the NHR authors note lowers ns/day by ~2.6x vs a low-output run · measured in anchor ($20 spent by then) · budget reached at 263 (1.0× lower)
           MD viscosity MAPE on the two anchor esters 15 % [g] rests on: OPLS Green-Kubo viscosity errors run around 10% for organic liquids (Guevara-Carrion reports <8% for alcohols); flexible esters are harder, so ~15%. · measured in anchor ($20 spent by then) · gate MD viscosity MAPE on the two anchor esters ≤ 22.5 in verify_100 (now 15, passes; uncut plan at it $984.16), else stop: MD is no more accurate than the ML viscosity model, so verification adds nothing. · budget not reached within 1000×
           measured A100 throughput on the real ester box 268 ns/day [g] rests on: same 20,000-atom size class as the NHR@FAU system-1 benchmark. · measured in anchor ($20 spent by then) · gate measured A100 throughput on the real ester box ≥ 150 in verify_300 (now 268, passes; uncut plan at it $984.16), else throughput too low to afford 300 candidates in budget; run top-100 only and stop. · budget not reached within 1000×
           best cooling figure at 300 vs 100 candidates 1.08 ratio [g] rests on: the 461-candidate pool spans a wide viscosity range and ML's 22.5% viscosity error should hide better candidates that MD uncovers. · measured in verify_300 ($984.16 spent by then) · gate best cooling figure at 300 vs 100 candidates ≥ 1.05 in verify_1000 (now 1.08, passes; uncut plan at it $984.16), else the best figure already plateaued at 300 candidates; the 1000-candidate run is not justified. · budget not reached within 1000×
Scenarios  the ester box runs at half the proxy throughput → $2,025.06 (over budget) · MD viscosity MAPE on the anchors equals Org-Mol's 22.5% → $984.16
Buys       top-100 tier size: 100 [d] · the ester box runs at half the proxy throughput: 100 · MD viscosity MAPE on the anchors equals Org-Mol's 22.5%: 100
           cumulative candidates through top-300 tier: 300 [d] · the ester box runs at half the proxy throughput: 300 · MD viscosity MAPE on the anchors equals Org-Mol's 22.5%: 300
           total production ns simulated through 300 candidates: 5,400 [=] · the ester box runs at half the proxy throughput: 5,400 · MD viscosity MAPE on the anchors equals Org-Mol's 22.5%: 5,400
           anchor simulation ns: 112 [d] · the ester box runs at half the proxy throughput: 112 · MD viscosity MAPE on the anchors equals Org-Mol's 22.5%: 112
Flags      error (quote) at numbers.ml_k_mae.quote: 0.003878 does not appear in the quote "our work 0.726 0.568 0.190 8.794 3.878E−03"; a value transformed from the page belongs in a DERIVED number
           thin headroom: the budget is reached if GROMACS throughput on A100 for a 20,000-atom liquid is 1.0× lower
Full scale MD-verify the full top-1000 candidates (301-1000 extra): $2,249.63 = 2.25× budget = 7.5× cumulative candidates through top-300 tier · inputs 1 c, 1 p, 3 d ([p] GROMACS throughput on A100 for a 20,000-atom liquid)
           top-1000 candidates at 100 ns each (5x longer sampling per candidate): $17,900 = 17.9× budget = 17.9× cumulative candidates through top-1000 tier · inputs 1 c, 1 p, 1 d ([p] GROMACS throughput on A100 for a 20,000-atom liquid)
Outside    computational chemist time: pipeline build, OPLS parameter assignment, Green-Kubo analysis, result review: 60 person-hours
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
gpu_h_per_candidate = ns_per_candidate / a100_ns_day * 24 = 18 / 267.5 * 24 = 1.61495 h
usd_per_candidate = gpu_h_per_candidate * a100_usd_gpu_h = 1.61495 * 1.99 = 3.21376 USD
usd_anchor = anchor_ns / a100_ns_day * 24 * a100_usd_gpu_h = 112 / 267.5 * 24 * 1.99 = 19.9967 USD
usd_100 = n_100 * usd_per_candidate = 100 * 3.21376 = 321.376 USD
usd_300_extra = (n_300 - n_100) * usd_per_candidate = (300 - 100) * 3.21376 = 642.751 USD
usd_1000_extra = (n_1000 - n_300) * usd_per_candidate = (1000 - 300) * 3.21376 = 2249.63 USD
usd_storage = 2 * fs_usd_gib_month * 60 / 720 = 2 * 0.2 * 60 / 720 = 0.0333333 USD
ns_simulated_300 = n_300 * ns_per_candidate = 300 * 18 = 5400 ns
md_mape_gate = ml_nu_mape = 22.467 = 22.467 %
l_anchor.hours = anchor_ns / a100_ns_day * 24 / node_gpus = 112 / 267.5 * 24 / 8 = 1.25607 h
l_anchor.need = anchor_ns / a100_ns_day * 24 / node_gpus = 112 / 267.5 * 24 / 8 = 1.25607 h
l_100.hours = n_100 * ns_per_candidate / a100_ns_day * 24 / node_gpus = 100 * 18 / 267.5 * 24 / 8 = 20.1869 h
l_100.need = n_100 * ns_per_candidate / a100_ns_day * 24 / node_gpus = 100 * 18 / 267.5 * 24 / 8 = 20.1869 h
l_300.hours = (n_300 - n_100) * ns_per_candidate / a100_ns_day * 24 / node_gpus = (300 - 100) * 18 / 267.5 * 24 / 8 = 40.3738 h
l_300.need = (n_300 - n_100) * ns_per_candidate / a100_ns_day * 24 / node_gpus = (300 - 100) * 18 / 267.5 * 24 / 8 = 40.3738 h
l_storage.usd = 2 * fs_usd_gib_month * 60 / 720 = 2 * 0.2 * 60 / 720 = 0.0333333 usd
fs_1000 = usd_1000_extra = 2249.63 = 2249.63 usd
fs_1000_long = n_1000 * 100 / a100_ns_day * 24 * a100_usd_gpu_h = 1000 * 100 / 267.5 * 24 * 1.99 = 17854.2 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:hypothesis` UNSUPPORTED · page: "N/A — no source cited" · note: The prediction ('MD will reorder...') needs no source, but the factual premise 'machine-learning viscosity error (22.5% MAPE)' has no cited source and no fetched page states a 22.5% MAPE (the article lists MAPE only as a metric definition, giving R2/MAE for viscosity, not 22.5%).
- sample 1 · `card:test_summary` PARTIAL · page: "Based on the aforementioned criteria of the kinematic viscosity and thermal conductivity, 461 monoesters are finally filtered out." · note: The plan steps (8-GPU A100, OPLS-AA Green-Kubo, 100 then 300 candidates, 45 ns vs 5 ns, rank correlation) need no source. However, the factual claim 'Org-Mol's 461 monoesters' is not cited by any source in this item; it happens to match the nature.com page ('461 monoesters are finally filtered out').
- sample 1 · `card:left_open` UNSUPPORTED · page: "N/A — no source cited" · note: Negative literature claim ('No published work runs Green-Kubo viscosity and thermal conductivity over a 100-to-1000 candidate ester shortlist') has no cited source and cannot be confirmed from the fetched pages.

**Critic.**
- stakes 3 · `card:limits` "Shows single-phase ranking only, under one force field and 15 ns sampling; no synthesis, dielectric, flammability, compatibility, or stability checks." · Choice to synthesize or scale depends on unchecked dielectric, flammability, compatibility, stability and real testing.
- lever 5 · `plan:compute_axis` "{"quantity":"MD-verified monoester candidates","unit":"candidates","levels":[100,300,1000]}" · 100→1000 candidates is 10x compute alone; pools, force field and temperature fixed; predicted Spearman gap exceeds bootstrapped noise with 3x-length rerun check.
- verifiable 5 · `plan:scored_against` "MD viscosity and thermal conductivity are compared with Org-Mol's measured values for Ester 1 (6.41 cSt, 0.141 W/m K) and Ester 2 (9.67 cSt, 0.138 W/m K); the best candidates' Mouromtseff number is compared with 3M Novec 649 (0.40 cSt, 0.05…" · Scored against published measured viscosities of Ester 1/2 and Novec 649 datasheet values, never predictors; anchor phase reproduces 6.41 cSt within ±25% first.
- open 5 · `card:left_open` "No published work runs Green-Kubo viscosity and thermal conductivity over a 100-to-1000 candidate ester shortlist, so whether MD reorders the ML ranking is untested." · Org-Mol ML-screened 461 candidates and synthesized two; no Green-Kubo MD reorder test over this range; plan states gap.
- reshape 5 · `plan:restructuring.method` "Run each candidate as parallel short replicas on separate GPUs and block-average the Green-Kubo integrals, so wall-clock shrinks by the replica count." · Long trajectory dependency replaced by concurrent replicas; block-average condition checked in anchor before GPU spend.
- baseline 3 · `plan:anchor` "Green-Kubo MD (OPLS-AA) reproduces Org-Mol Ester 1's measured 40 C viscosity 6.41 cSt Tolerance: ±25% on viscosity; ±20% on thermal conductivity 0.141 W/m K." · Anchor times sequential and replica baselines but lacks stated tolerance comparing parallel accuracy to sequential result.

**Producer says (not judged).** expected if_lever (The machine-learning model's 22.5% viscosity error is far larger than molecular dynamics' expected error, so verification must reshuffle the list.); compute_tested yes (Verifying more candidates is bought directly with more GPU-hours; the number of candidates is the axis, and wall-clock is compressed by running 8 candidates at once on the 8-GPU node.); decides no; searched yes.

**Annotations.**
- quote at numbers.ml_k_mae.quote: 0.003878 does not appear in the quote "our work 0.726 0.568 0.190 8.794 3.878E−03"; a value transformed from the page belongs in a DERIVED number
- thin headroom: the budget is reached if GROMACS throughput on A100 for a 20,000-atom liquid is 1.0× lower
- prior_max_level 0 is not in the quote of s1
- restructuring.condition_phase anchor has no gate
- question: a sentence of 24 words
- hypothesis: a sentence of 22 words
- restructuring.method: a sentence of 22 words
- predictions.if_lever: a sentence of 21 words
- predictions.if_not: a sentence of 22 words
- test_summary: a sentence of 45 words
- novelty.closest_prior: a sentence of 24 words
- novelty.left_open: a sentence of 24 words
- prose over 280 words (284)

**Root question (null).** generative pipeline for discovery of single phase immersion coolants

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/immersion-coolants/20261018-0231-card/out/work/seed-1/seed/idea/4e6d66bb/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: quote at numbers.ml_k_mae.quote: 0.003878 does not appear in the quote "our work 0.726 0.568 0.190 8.794 3.878E−03"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: thin headroom: the budget is reached if GROMACS throughput on A100 for a 20,000-atom liquid is 1.0× lower
seed:idea:seed: prior_max_level 0 is not in the quote of s1
seed:idea:seed: restructuring.condition_phase anchor has no gate
seed:idea:seed: question: a sentence of 24 words
seed:idea:seed: hypothesis: a sentence of 22 words
seed:idea:seed: restructuring.method: a sentence of 22 words
seed:idea:seed: predictions.if_lever: a sentence of 21 words
seed:idea:seed: predictions.if_not: a sentence of 22 words
seed:idea:seed: test_summary: a sentence of 45 words
seed:idea:seed: novelty.closest_prior: a sentence of 24 words
seed:idea:seed: novelty.left_open: a sentence of 24 words
seed:idea:seed: dramaturg-2: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:sequential_part; degenerate: card:method; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:limits
seed:idea:seed: prose over 280 words (284)
```