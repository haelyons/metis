# Result

Picks 1 · PASS 1 · on-goal cards U4 0 · U3 1 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) Ensemble size for rare extremes in a machine-learned weather ensemble | PASS 2/2 | seed | if_lever | 3 | — → 5 | — → 5 | 5 | — | — → 1 | — | $963 at p_score · plan $963 · 1 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**ml-ensemble-extremes · Ensemble size for rare extremes in a machine-learned weather ensemble.** seed pick · compute tested: yes · plan expects: the lever · PASS

**Question.** Does 10 to 1,000 AIFS-ENS members beat 50 for top-percentile wind, temperature, and rain probability forecasts, or does shared model error cap the skill?

**What is known.** HENS Part 2: 7,424 SFNO members per day for 92 summer-2023 dates; showed huge ensembles sample 4-sigma tails and reduce outliers. Whether AIFS-ENS, whose members are exchangeable draws of one afCRPS-trained distribution, keeps gaining skill past 50 members or saturates from shared model error.

**Hypothesis.** More members keep helping: 1,000 members sample top-percentile tails far better than 50, so extreme-event scores keep improving [s_hens].

**If compute is the lever.** Skill on top-percentile wind, temperature, and rain keeps rising past 50 members: 1,000 members sharpen the tails and improve extreme-event scores.

**If not.** Skill flattens near 50 members: members are exchangeable draws of one trained distribution, so shared model error caps tail sharpness and extra members add nothing.

**Test.** Run 7,000 fifteen-day AIFS-ENS v1 forecasts (7 dates x 1,000 members) on eight A100 40 GB GPUs; subsample 10-1,000 members, score top-percentile wind/temperature/rain probabilities against ERA5 with fair CRPS and Brier scores, and test whether skill still rises past 50 members.

*Compute axis.* Ensemble members per forecast: 10–1,000 members, 6 levels. Closest prior: 7,424 [s_hens], not beyond it.

*Restructuring.* none.

**Check first.** Reproduce the published 4-minute N320 member time and 38 GB memory; one control run must match ECMWF open data within ensemble spread [s_crps_paper]. Tolerance: timing within +/-25% of 4 min; 38 GB memory fits; control field within the ensemble's own member-to-member spread at each lead time (GPUs are non-deterministic, so exact reproduction is not expected).

**Would not show.** Applies to AIFS-ENS v1 medium-range extremes on 7 dates; not a multi-season reforecast, other models, subseasonal leads, or direct proof that shared error causes any saturation.

*Cost.* Plans $963.17 of the $1,000 budget over 74.3 machine-hours, leaving $36.83. Main guess: peak filesystem usage [g], measured after $19.90 of spend; the budget is reached if it is 15× higher. Full scale: A 30-date multi-season reforecast at 1,000 members, $3,980, 3.98× the budget.

**Judges.** Dramaturg: PASS 2/2. Decides at: $963 at p_score · plan $963 · 1 GUESS (critic: Fair CRPS/Brier skill versus member count and bootstrap intervals are computed only in p_score).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-18 · filesystem $0.20/GiB-month [q]
Spend      p_pilot  One A100 40 GB: install anemoi-inference, time ~2 members, verify 38 GB and ~4 min, anchor one control run  1x NVIDIA A100 SXM 40GB $1.99/h  10 h [=]  $19.90  time box; need 5 h (margin 2.00×)
           p_main  Eight A100 40 GB: 7 dates x 1,000 members = 7,000 fifteen-day forecasts (466.7 total GPU-hours = 58.3 wall hours)  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  58.3 h [=]  $928.67
           p_score  One A100 40 GB (CPU): subsample, fair CRPS + Brier vs N, bootstrap confidence intervals  1x NVIDIA A100 SXM 40GB $1.99/h  6 h [=]  $11.94  time box; need 3 h (margin 2.00×)
           p_score  Filesystem for checkpoint, ERA5, and transient GRIB  [=]  $2.67
           p_station  SYNOP station verification of top-percentile events  1x NVIDIA A100 SXM 40GB $1.99/h  4 h [=]  $7.96  time box; need 2 h (margin 2.00×)  optional
           Planned $963.17 · unallocated $36.83 · with options $971.13 · cap $1,000
Rests on   peak filesystem usage 100 GiB [g] rests on: aifs-ens checkpoint (~4 GB) plus ERA5 climatology and 7 verification dates (~20 GB) plus transient member GRIB buffered before streaming scores · measured in p_pilot ($19.90 spent by then) · budget reached at 1,480 (15× higher)
           gate AIFS-CRPS N320 15-day per-member inference time ≤ 10 in p_pilot (now 4, passes; uncut plan at it $2,356.17), else re-plan: reduce members-per-date to 500 and double dates to hold the budget
Scenarios  Per-member time doubles to 8 min: main cost ~$1,857, so halve dates to stay under budget → $1,891.84 (over budget) · 3 min per member: afford 10 dates at 1,000 members → $1,029.51 (over budget)
Buys       total member forecasts: 7,000 [=] · Per-member time doubles to 8 min: main cost ~$1,857, so halve dates to stay under budget: 7,000 · 3 min per member: afford 10 dates at 1,000 members: 10,000
           initialization dates: 7 [d] · Per-member time doubles to 8 min: main cost ~$1,857, so halve dates to stay under budget: 7 · 3 min per member: afford 10 dates at 1,000 members: 10
Flags      error (quote) at numbers.n_infer_min_member.quote: 4 does not appear in the quote "a single member 15 day forecast is created in about one minute for AIFS-CRPS O96 and four minutes for AIFS-CRPS N320 on an NVIDIA A100 40 GB GPU, including the time spent reading the initial state and writing the forecast to disk."; a value transformed from the page belongs in a DERIVED number
           uncut plan at the p_pilot gate threshold costs $2,356.17, over budget; the plan relies on: re-plan: reduce members-per-date to 500 and double dates to hold the budget
Full scale One AIFS-ENS date at HENS size (7,424 members) - about the whole budget: $984.92 = 0.985× budget = 1.06× main-run cost · inputs 3 c
           A 30-date multi-season reforecast at 1,000 members: $3,980 = 3.98× budget = 4.29× main-run cost · inputs 2 c, 1 d
Outside    engineer time (design, data prep, scoring, writeup): 3 person-days · ECMWF Open Data, ERA5, and SYNOP data access: 0 USD (free under open data licenses)
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
n_rollout_steps = n_lead_hours / n_step_hours = 360 / 6 = 60 steps
n_total_members = n_members_per_date * n_dates = 1000 * 7 = 7000 members
n_member_hours = n_infer_min_member / 60 = 4 / 60 = 0.0666667 h
n_total_gpu_hours = n_total_members * n_member_hours = 7000 * 0.0666667 = 466.667 h
n_main_usd = n_total_gpu_hours * n_a100_usd_h = 466.667 * 1.99 = 928.667 USD
n_wall_hours = n_total_gpu_hours / n_gpus = 466.667 / 8 = 58.3333 h
n_storage_usd = n_storage_gib * fs_usd_gib_month * n_wall_days / 30 = 100 * 0.2 * 4 / 30 = 2.66667 USD
L_pilot.hours = n_pilot_hours = 10 = 10 h
L_main.hours = n_wall_hours = 58.3333 = 58.3333 h
L_score.hours = n_score_hours = 6 = 6 h
L_storage.usd = n_storage_usd = 2.66667 = 2.66667 usd
L_station.hours = n_station_hours = 4 = 4 h
f_hens_ai = n_hens_members * n_member_hours * n_a100_usd_h = 7424 * 0.0666667 * 1.99 = 984.917 usd
f_reforecast = 30 * n_members_per_date * n_member_hours * n_a100_usd_h = 30 * 1000 * 0.0666667 * 1.99 = 3980 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:anchor` PARTIAL · page: "This makes inference computationally cheap: a single member 15 day forecast is created in about one minute for AIFS-CRPS O96 and four minutes for AIFS-CRPS N320 on an NVIDIA A100 40 GB GPU, including the time spent reading the initial state and writing the forecast to disk." · note: The '4-minute N320 member time' is on the page and supported. The '38 GB memory' value is not stated anywhere on the page (it only mentions the A100 40 GB GPU), so that part is unsupported.
- sample 2 · `card:left_open` UNSUPPORTED · page: "arXiv:2412.15832 abstract: "The trained model is stochastic and can generate as many exchangeable members as desired and computationally feasible in inference." (on a *different* page than the one cited)" · note: The 'whether skill saturates' part is the plan's open question and needs no source, but the item factually asserts that AIFS-ENS members are 'exchangeable draws of one afCRPS-trained distribution' with no source cited on the card. That design fact appears on the AIFS-CRPS paper and model-card pages, which were not cited by the card, so it is UNSUPPORTED as cited.
- sample 2 · `card:anchor` PARTIAL · page: ""AIFS-CRPS requires one single model evaluation to produce a 6 h forecast step for one ensemble member. This makes inference computationally cheap: a single member 15 day forecast is created in about one minute for AIFS-CRPS O96 and four minutes for AIFS-CRPS N320 on an NVIDIA A100 40 GB GPU, including the time spent reading the initial state and writing the forecast to disk."" · note: The 4-minute N320 member time on an NVIDIA A100 40 GB GPU is stated verbatim on the cited page and supports the timing anchor. However, the '38 GB memory' value is not stated on the cited s_crps_paper page (it appears on the HuggingFace ecmwf/aifs-ens-1.0 model card, which the card does not cite); the reproduce-and-match engineering steps themselves need no source.

**Critic.**
- stakes 5 · `card:question` "Does 10 to 1,000 AIFS-ENS members beat 50 for top-percentile wind, temperature, and rain probability forecasts, or does shared model error cap the skill?" · Outcome directly tells whether buying extra GPU members beats keeping operational 50 for AIFS-ENS extremes.
- lever 3 · `plan:predictions.noise_rule` "Bootstrap over which members are sampled and over the 7 dates; a real difference exceeds the 95% paired confidence interval, and the fair-CRPS correction separates genuine tail information from finite-ensemble-size bias." · No power analysis shows the 0.01 skill difference exceeds bootstrap noise over only seven dates.
- verifiable 5 · `plan:scored_against` "ERA5 reanalysis (independent truth the model was not fit to produce for these forecast dates) and SYNOP station observations, for top-percentile 10 m wind, 2 m temperature, and 24 h precipitation." · ERA5 and SYNOP observations are independent truth, and the anchor reproduces published per-member timing plus ECMWF control fields within stated tolerance.
- open 5 · `card:left_open` "Whether AIFS-ENS, whose members are exchangeable draws of one afCRPS-trained distribution, keeps gaining skill past 50 members or saturates from shared model error." · HENS used SFNO; left_open names AIFS-ENS exchangeable-draw saturation as still unknown.
- reshape 1 · `card:method` "none" · method:none; only independent members and dates run side by side, each forecast's sequential steps remain.
- baseline NA · `card:method` "none" · Restructuring method is none, so the baseline throughput comparison is not applicable.

**Producer says (not judged).** expected if_lever (A 50-member estimate of a top-percentile probability carries roughly 1/sqrt(50) sampling error that 1,000 members reduces threefold, and HENS showed huge ensembles sample tails better.); compute_tested yes (The test varies ensemble size (members per forecast), which is exactly what more parallel GPUs buy: more members in the same wall time.); decides partly; searched yes.

**Annotations.**
- cost record repaired: 1 expression(s) rewritten
- quote at numbers.n_infer_min_member.quote: 4 does not appear in the quote "a single member 15 day forecast is created in about one minute for AIFS-CRPS O96 and four minutes for AIFS-CRPS N320 on an NVIDIA A100 40 GB GPU, including the time spent reading the initial state and writing the forecast to disk."; a value transformed from the page belongs in a DERIVED number
- uncut plan at the p_pilot gate threshold costs $2,356.17, over budget; the plan relies on: re-plan: reduce members-per-date to 500 and double dates to hold the budget
- question: a sentence of 24 words
- predictions.if_lever: a sentence of 21 words
- predictions.if_not: a sentence of 25 words
- test_summary: a sentence of 41 words
- novelty.closest_prior: a sentence of 21 words
- novelty.left_open: a sentence of 23 words
- anchor.what: a sentence of 23 words
- limits: a sentence of 26 words
- dramaturg findings failed G-find after a resample; decided as returned
- prose over 240 words (273)

**Root question (null).** Do more members of a machine-learned weather ensemble buy better forecasts of rare extremes, or does error shared by all members cap the skill?

**Producer file.** [producer.md](/home/hal/dev/interp/latent_open/experiments/ml-ensemble-extremes/20261018-0059-loop/out/r0/card/work/seed-1/seed/idea/97773b52/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: G-plan repair: planned $7463.84 over $1000.00 while stated $963.18 is not
seed:idea:seed: cost record repaired: 1 expression(s) rewritten
seed:idea:seed: quote at numbers.n_infer_min_member.quote: 4 does not appear in the quote "a single member 15 day forecast is created in about one minute for AIFS-CRPS O96 and four minutes for AIFS-CRPS N320 on an NVIDIA A100 40 GB GPU, including the time spent reading the initial state and writing the forecast to disk."; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: uncut plan at the p_pilot gate threshold costs $2,356.17, over budget; the plan relies on: re-plan: reduce members-per-date to 500 and double dates to hold the budget
seed:idea:seed: question: a sentence of 24 words
seed:idea:seed: predictions.if_lever: a sentence of 21 words
seed:idea:seed: predictions.if_not: a sentence of 25 words
seed:idea:seed: test_summary: a sentence of 41 words
seed:idea:seed: novelty.closest_prior: a sentence of 21 words
seed:idea:seed: novelty.left_open: a sentence of 23 words
seed:idea:seed: anchor.what: a sentence of 23 words
seed:idea:seed: limits: a sentence of 26 words
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:if_lever; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:left_open; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: prose over 240 words (273)
```