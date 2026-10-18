Here is a research card, written to answer this root question: Do more members of a machine-learned weather ensemble buy better forecasts of rare extremes, or does error shared by all members cap the skill?

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

Find the existing research or industrial programmes this card's result would feed: named labs, companies, open-source projects or consortia doing this work now. Pick one to three. For each, use its own pages, papers or repositories to describe the step of its pipeline the card targets, and how it handles that step today: at what scale, with which tools or people. Describe that step in the programme's own words, and copy the sentence from its own page that describes it (step_url, step_quote). Say whether the programme is active now: cite its most recent release, commit, paper or announcement, or a statement that it was archived or stopped (activity). Say what each of the card's two predicted outcomes would change in that programme's practice, or that it would change nothing. Check whether that programme, or work it relies on, has already run this experiment. Cite a URL for every factual claim and copy the sentence from that page that supports it. If no programme would use the result, return no programmes and say why. Write your working notes to notes.md in your working directory.
Return only JSON: {"programmes": [{"name": "", "url": "", "step": "", "step_url": "", "step_quote": "", "activity": {"state": "active | inactive | unknown", "claim": "", "url": "", "quote": ""}, "practice": [{"claim": "", "url": "", "quote": ""}], "if_lever_changes": "", "if_not_changes": "", "already_done": {"status": "yes | partly | no | unknown", "claim": "", "url": "", "quote": ""}}], "gaps": [""], "no_programme_reason": ""}