Here is a research card, written to answer this root question: generative pipeline for discovery of single phase immersion coolants

**immersion-coolants · Generative search for single-phase immersion coolants.** seed pick · compute tested: yes · plan expects: unsure · REJECT

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

Find the existing research or industrial programmes this card's result would feed: named labs, companies, open-source projects or consortia doing this work now. Pick one to three. For each, use its own pages, papers or repositories to describe the step of its pipeline the card targets, and how it handles that step today: at what scale, with which tools or people. Describe that step in the programme's own words, and copy the sentence from its own page that describes it (step_url, step_quote). Say whether the programme is active now: cite its most recent release, commit, paper or announcement, or a statement that it was archived or stopped (activity). Say what each of the card's two predicted outcomes would change in that programme's practice, or that it would change nothing. Check whether that programme, or work it relies on, has already run this experiment. Cite a URL for every factual claim and copy the sentence from that page that supports it. If no programme would use the result, return no programmes and say why. Write your working notes to notes.md in your working directory.
Return only JSON: {"programmes": [{"name": "", "url": "", "step": "", "step_url": "", "step_quote": "", "activity": {"state": "active | inactive | unknown", "claim": "", "url": "", "quote": ""}, "practice": [{"claim": "", "url": "", "quote": ""}], "if_lever_changes": "", "if_not_changes": "", "already_done": {"status": "yes | partly | no | unknown", "claim": "", "url": "", "quote": ""}}], "gaps": [""], "no_programme_reason": ""}