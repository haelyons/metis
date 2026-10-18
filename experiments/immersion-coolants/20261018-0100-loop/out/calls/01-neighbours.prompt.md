Here is a research idea, the card a planner wrote for it, and a check of which existing research or industrial programmes would use its result, with the gaps that check found.

Root question: generative pipeline for discovery of single phase immersion coolants
Idea: {"title":"Generative search for single-phase immersion coolants","text":"Data-centre immersion cooling needs dielectric liquids with low viscosity, high thermal conductivity and heat capacity, a low dielectric constant and a high flash point. PFAS rules and the end of Novec production are pushing the field towards PFAS-free hydrocarbons and esters. Study whether a generative search over molecules and mixtures finds candidates that beat known commercial single-phase fluids on a cooling figure of merit. More compute buys more candidates checked by GPU molecular dynamics after predictor filtering, and longer simulations per candidate. Score against measured viscosity, thermal conductivity and dielectric data for known fluids held out of training, never against the predictors themselves.","root_link":"SAME: a concrete version of the asker's line, kept on discovery and on transport properties (viscosity, thermal conductivity).","compute_open":"Candidates checked by GPU molecular dynamics (about 10^2 to 10^4) and simulation length per candidate. Unknown: whether the hit rate against known commercial fluids keeps rising with more candidates, or whether predictor and force-field error caps it.","sequential":"not given"}
Card:
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

Card verdict: REJECT (2 blocking)
Programme check: [{"name":"Ewen group (Imperial College London / University of Bath) — MD benchmarking of organic-liquid thermophysical properties","step":"The GPU molecular-dynamics verification of candidate fluids' viscosity and thermal conductivity — the exact step the card scales to 100/300/1000 candidates. Today the group runs equilibrium MD (EMD) on a handful of representative molecules and benchmarks it against ML predictors for density, viscosity and thermal conductivity of C10–C50 organics (lubricants and cooling fluids).","sum":11},{"name":"Sinton Lab / FL01 (University of Toronto + Acceleration Consortium) — self-driving lab for immersion coolant discovery","step":"The verification/ranking of many candidate coolants — the same pipeline stage the card runs with GPU-MD, which Sinton/FL01 run instead with a wet-lab self-driving lab measuring viscosity, density, heat capacity, thermal conductivity and dielectric constant.","sum":11},{"name":"Org-Mol team (SINOPEC Research Institute of Petroleum Processing + DP Technology + AI for Science Institute)","step":"The post-ML-filter down-selection the card replaces with MD verification: Org-Mol ML-screens millions of esters, filters to a 461-candidate shortlist, then manually picks only two to synthesize and measure — exactly where the card would insert GPU-MD verification of the top 100–1000.","sum":11}]
Gaps found: ["No programme measures the card's exact quantity: whether the best MD-ranked coolant's cooling FOM keeps improving as the number of MD-verified candidates grows from ~100 to ~1000 (vs. plateauing).","Ewen group's MD verification covers only 8 representative molecules with no immersion-coolant FOM compared against commercial fluids; Sinton/FL01 verify experimentally and via CFD, not with MD; Org-Mol never MD-verified its shortlist.","Activity of the Org-Mol/SINOPEC team is inferred from a July 2025 paper plus multi-year funding; no follow-on release was found by Oct 2026, so its 'active' state is weaker evidence than for the Ewen (Sep 2026 paper) and Sinton/FL01 (Nov 2025 launch, Sep 2026 prototyping) programmes."]

Propose three close variants of the idea. Each changes one thing (the system studied, the quantity more compute buys, the comparison it is judged against, or the programme it is aimed at) so that its result would matter more to a named programme or close a named gap. Keep the rest of the idea. Name only systems, tools and programmes that appear above or that you are sure exist. Decide only from the text above; do not use tools.
Return only JSON: {"variants": [{"id": "V1", "title": "", "text": "the idea in three to five sentences, in the form of the original", "root_link": "", "compute_open": "", "sequential": "", "changes": "what differs from the original and which gap or programme it answers"}]}