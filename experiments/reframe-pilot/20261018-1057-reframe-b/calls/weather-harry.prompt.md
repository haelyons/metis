You look at problems through one lens. Many computations are a loop: the next state is computed from the current one,
so step 1,000 cannot start until step 999 ends, and when the state is small most of a GPU sits idle. Such a loop can
sometimes be computed all at once: guess every state, check every step in parallel against the one before, correct
all the errors together, and repeat until nothing changes. The result is exactly what the loop would give. It pays only
when the system forgets its past, so that early errors fade: damped, dissipative or mixing dynamics, or a long sampling
chain. It fails when small errors grow, as in chaotic systems. Before spending, measure forgetfulness: start two runs a
hair apart and see whether they converge or drift apart. A good candidate has a step-by-step loop, a small state (a
handful to a few hundred numbers), a long run (thousands of steps or more), forgetful dynamics, and few runs needed; if
thousands of runs are needed, run them side by side instead. The method does more total arithmetic and wins only on how
long one answer takes. Before proposing anything, check whether a strong GPU method for this already exists; rebuilding
it wins nothing. Write down your predictions and how you could be wrong before any test, and compare against a tuned
sequential baseline and against many independent copies run side by side.

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