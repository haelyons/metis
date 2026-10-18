You look for the assumption that makes a problem slow, or makes extra compute buy only more of the same. Ask which part
of the work waits on another part, and whether it must. Ask which quantity is measured, and whether a different but
related quantity would be cheaper to compute, easier to split, or more informative. Ask whether the unit of work is the
right one, or whether the work could be cut, merged or reordered. Ask whether the objective is the right one: the single
best answer, a ranking, a distribution, a rare tail, or a yes or no. Ask what is held fixed that need not be. Prefer
changes that alter what more compute buys over changes that only run the same work more times.

Here is a research problem as it was first written down, with the question it belongs to.
Root question: Do more members of a machine-learned weather ensemble buy better forecasts of rare extremes, or does error shared by all members cap the skill?
Problem:
**ml-ensemble-extremes · Ensemble size for rare extremes in a machine-learned weather ensemble.** seed pick · compute tested: yes · plan expects: the lever · PASS

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

Find where this problem stops more compute from helping, or where more compute only buys more of the same. Then look for reframings: changes to what is measured, the unit of work, the objective or the order of steps that would let more compute change the answer. Give up to three. End each with one question someone could investigate: specific, answerable by a measurement, and naming what is measured. For each, give the cheapest measurement that would answer it or show it is not worth pursuing, with a rough cost. Decide from the text above and what you know; do not use tools.

Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","required":["reframes"],"properties":{"reframes":{"type":"array","items":{"type":"object","required":["bottleneck","assumption","reframe","question","measure","compute_after","exact","expected","fails_if","closest_prior"],"properties":{"bottleneck":{"type":"string"},"assumption":{"type":"string"},"reframe":{"type":"string"},"question":{"type":"string"},"measure":{"type":"string"},"compute_after":{"type":"string"},"exact":{"type":"string"},"expected":{"type":"string"},"fails_if":{"type":"string"},"closest_prior":{"type":"string"}}}}}}