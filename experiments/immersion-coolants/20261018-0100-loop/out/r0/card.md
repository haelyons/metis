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
