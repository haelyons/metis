Here is a research idea, the card a planner wrote for it, and a check of which existing research or industrial programmes would use its result, with the gaps that check found.

Root question: Do more members of a machine-learned weather ensemble buy better forecasts of rare extremes, or does error shared by all members cap the skill?
Idea: {"title":"Ensemble size for rare extremes in a machine-learned weather ensemble","text":"ECMWF runs its machine-learned ensemble, AIFS-ENS, operationally with 50 members, and the model weights are public. An extra member needs one GPU run rather than a supercomputer slot, so ensembles of hundreds or thousands look affordable. Study whether 10 to 1,000 members improve probability forecasts of rare extremes, such as top-percentile wind, temperature or rainfall. Score against ERA5 reanalysis and station observations, which the model did not produce. The open question is whether more members keep helping or whether error shared by every member caps the skill.","root_link":"SAME: the director's C1 question made concrete on one open, operational model.","compute_open":"Ensemble members per forecast, from about 10 to 1,000. Unknown: whether skill on top-percentile events keeps rising past the operational 50 members, or flattens because members share model error. The closest prior, HENS, ran 7,424 members of a different model (SFNO) for summer 2023.","sequential":"not given"}
Card:
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

Card verdict: PASS 2/2
Programme check: []
Gaps found: []

Propose three close variants of the idea. Each changes one thing (the system studied, the quantity more compute buys, the comparison it is judged against, or the programme it is aimed at) so that its result would matter more to a named programme or close a named gap. Keep the rest of the idea. Name only systems, tools and programmes that appear above or that you are sure exist. Decide only from the text above; do not use tools.
Return only JSON: {"variants": [{"id": "V1", "title": "", "text": "the idea in three to five sentences, in the form of the original", "root_link": "", "compute_open": "", "sequential": "", "changes": "what differs from the original and which gap or programme it answers"}]}