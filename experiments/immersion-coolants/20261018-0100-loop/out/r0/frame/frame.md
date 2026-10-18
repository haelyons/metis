# Frame check: card

Root question: generative pipeline for discovery of single phase immersion coolants

Models: research opencode-go/deepseek-v4-pro; dramaturgs opencode-go/deepseek-v4.1-flash, opencode-go/glm-5.3-flash; critics opencode-go/qwen3.8-flash, opencode-go/mimo-v2.6-flash, opencode-go/minimax-m3.
Cost $0.1644 · 402,994 tokens · 11.1 min wall time.

**Best fit:** Ewen group (Imperial College London / University of Bath) — MD benchmarking of organic-liquid thermophysical properties, at "The GPU molecular-dynamics verification of candidate fluids' viscosity and thermal conductivity — the exact step the card scales to 100/300/1000 candidates. Today the group runs equilibrium MD (EMD) on a handful of representative molecules and benchmarks it against ML predictors for density, viscosity and thermal conductivity of C10–C50 organics (lubricants and cooling fluids).". Fit 4, change 3, new 4: 11 of 15.

## 1. Ewen group (Imperial College London / University of Bath) — MD benchmarking of organic-liquid thermophysical properties

https://doi.org/10.1039/D6DD00260A

**Step:** The GPU molecular-dynamics verification of candidate fluids' viscosity and thermal conductivity — the exact step the card scales to 100/300/1000 candidates. Today the group runs equilibrium MD (EMD) on a handful of representative molecules and benchmarks it against ML predictors for density, viscosity and thermal conductivity of C10–C50 organics (lubricants and cooling fluids).

**Practice claims and checks:**
- VERIFIED [PARTIAL, SUPPORTED] The group's ML-first screening toolchain is built on a ~4,700-value experimental database for 835 organic molecules, with XGBoost as the best model — i.e. MD is used only as a spot-check, not at screening scale. (https://doi.org/10.1039/D6DD00260A)
- VERIFIED [SUPPORTED, SUPPORTED] MD verification is run on only eight molecules, and the group already concluded that ML (orders of magnitude cheaper than EMD) is the right tool for high-throughput screening — the assumption the card tests. (https://doi.org/10.1039/D6DD00260A)
- VERIFIED [SUPPORTED, SUPPORTED] The work is done by Egheosa Ogbomo, Fionn Carman, Daniele Dini and James Patrick Ewen (Imperial College London; Ewen now Lecturer at University of Bath), using supercomputer molecular simulation of solid-liquid interfaces. (https://profiles.imperial.ac.uk/j.ewen)

**Activity:** active [SUPPORTED, PARTIAL] Most recent output is the Digital Discovery paper benchmarking ML vs MD for organic-liquid thermophysical properties, dated 29 Sep 2026, following a 22 Apr 2026 ChemRxiv preprint on the hydrocarbon version.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If the best MD-ranked coolant keeps improving as verified candidates grow 100→1000, the group has a concrete reason to build a GPU-MD verification stage as a genuine ranking/filter (not an 8-molecule benchmark), investing in throughput and force-field refinement so MD — rather than XGBoost alone — decides which candidates advance.

**If not:** If the best FOM plateaus by a few hundred candidates, it confirms their published conclusion that ML predictors at orders-of-magnitude lower cost are the right screening tool and that MD's force-field error (~chemistry-dependent bias in viscosity/thermal conductivity) caps its ranking value; their MD stays a spot-check rather than a scaled verification layer.

**Already done:** partly [SUPPORTED, SUPPORTED] They have EMD-verified thermophysical properties but only for a fixed set of eight representative molecules; they have not run the card's scaling experiment (best MD-ranked FOM vs number of MD-verified candidates from 100 to 1000, compared to commercial fluids).

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 4 | 5, 3, 4 | 2 |
| change | 3 | 3, 3, 5 | 2 |
| new | 4 | 5, 4, 4 | 1 |

- fit, opencode-go/qwen3.8-flash: Card measures GPU-MD organic-liquid viscosity/conductivity, exactly the EMD step and systems programme currently spot-checks.
- fit, opencode-go/mimo-v2.6-flash: Card reports ranking and hit rate, explicitly not absolute fluid accuracy; Ewen benchmarking needs absolute viscosity/thermal-conductivity accuracy — a stand-in.
- fit, opencode-go/minimax-m3: Measures MD-verified viscosity/thermal conductivity FOM at scale on C10–C50 organics matching their practice; scale differs from current 8 molecules.
- change, opencode-go/qwen3.8-flash: Only rising FOM would make it scale MD from spot-check to ranking; plateau confirms ML-first practice, no change.
- change, opencode-go/mimo-v2.6-flash: Plateau outcome only confirms their published ML-first conclusion; only the climbing outcome would change what they build or scale.
- change, opencode-go/minimax-m3: If lever holds, group builds scaled GPU-MD verification; if not, MD stays spot-check—both outcomes change current MD practice.
- new, opencode-go/qwen3.8-flash: Practice verifies only eight molecules and uses ML screening; it lacks MD-verified FOM over 100–1000 candidates.
- new, opencode-go/mimo-v2.6-flash: They MD-verified only eight molecules and never scaled candidate count, but that partial verification overlaps the card's mechanism.
- new, opencode-go/minimax-m3: Group MD-verified 8 molecules but has not run scaling experiment (best MD-FOM vs 100→1000 candidates vs commercial fluids).

## 2. Sinton Lab / FL01 (University of Toronto + Acceleration Consortium) — self-driving lab for immersion coolant discovery

https://acceleration.utoronto.ca/news/ac-u-of-t-startup-tackles-the-growing-challenge-of-cooling-powerful-technologies

**Step:** The verification/ranking of many candidate coolants — the same pipeline stage the card runs with GPU-MD, which Sinton/FL01 run instead with a wet-lab self-driving lab measuring viscosity, density, heat capacity, thermal conductivity and dielectric constant.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] Their verification throughput is 5 samples/hour (claimed 100× conventional), i.e. thousands of measurements per device per month, but still a wet-lab loop rather than computation. (https://doi.org/10.82417/pw8c-8z69)
- VERIFIED [SUPPORTED, SUPPORTED] Data-generation scale is the explicit selling point: one device produces 10,000 data points in two months, versus ~4,000 publicly available data points over the prior century. (https://acceleration.utoronto.ca/news/ac-u-of-t-startup-tackles-the-growing-challenge-of-cooling-powerful-technologies)
- VERIFIED [PARTIAL, SUPPORTED] The group already uses a figure of merit (FOM) for immersion coolants and screens >1600 fluid mixtures by coupling CFD with active learning (15 data points to drive the FOM, 10× efficiency). People: David Sinton, Mohammad Zargartalebi, Hanie Rezaei, Maryam Ebrahimiazar (U of T Mechanical & Industrial Engineering); FL01 CEO Zargartalebi. (https://ui.adsabs.harvard.edu/abs/2025JEnSt.14019036R/abstract)

**Activity:** active [SUPPORTED, SUPPORTED] FL01 launched November 2025 and, as of a 1 Sep 2026 Acceleration Consortium article, is prototyping its self-driving lab with several industry partners.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If more MD verification keeps raising the best FOM, FL01/Sinton gains a cheap GPU pre-filter: MD could rank a million candidates before any fluid is ever synthesized, letting their 5-samples/hour wet-lab loop spend effort only on the MD-verified top tier — shrinking the 'years to weeks' R&D timeline further and de-risking which chemistries to buy/synthesize.

**If not:** If MD FOM plateaus, their experimental self-driving lab remains the only trustworthy verifier (their Nature Communications microfluidic method already argues computational thermal-conductivity models carry ~10% errors and 'necessitate experimental verification'), so they keep investing in sensor/SDL throughput rather than GPU-MD, and the card's MD stage is not added to their loop.

**Already done:** no [PARTIAL, PARTIAL] Sinton/FL01 verify and rank candidates experimentally (self-driving lab, microfluidics, CFD+active learning), not via GPU molecular dynamics, and they have not run the card's MD-verification scaling experiment (best MD-ranked FOM vs number of MD-verified candidates).

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 3 | 3, 3, 3 | 0 |
| change | 3 | 3, 3, 3 | 0 |
| new | 5 | 5, 5, 4 | 1 |

- fit, opencode-go/qwen3.8-flash: Outcome concerns GPU-MD ranking, not SDL wet-lab verification; they would bridge computation to 5-sample/hour experimental selection.
- fit, opencode-go/mimo-v2.6-flash: Card's MD ranking substitutes for their wet-lab measurement of the same properties; their own work says computation needs experimental verification.
- fit, opencode-go/minimax-m3: Card measures computational MD-FOM as stand-in for their experimental wet-lab verification; bridges computation to experiment.
- change, opencode-go/qwen3.8-flash: Only rising MD FOM justifies adding a GPU pre-filter before SDL; plateau keeps SDL throughput investment unchanged.
- change, opencode-go/mimo-v2.6-flash: Only the climbing outcome would add an MD pre-filter; plateau merely reconfirms their wet-lab-first investment, changing nothing.
- change, opencode-go/minimax-m3: If lever holds, they add GPU-MD pre-filter before wet-lab; if not, status quo—only lever case changes practice.
- new, opencode-go/qwen3.8-flash: SDL verifies candidates experimentally via FOM/CFD, not by GPU-MD scaling, so the MD plateau question lacks evidence.
- new, opencode-go/mimo-v2.6-flash: Both checkers confirm they verify experimentally, never via GPU-MD, and have not run the candidate-count scaling experiment.
- new, opencode-go/minimax-m3: Group verifies experimentally via SDL/microfluidics; has not run card's MD-verification scaling experiment.

## 3. Org-Mol team (SINOPEC Research Institute of Petroleum Processing + DP Technology + AI for Science Institute)

https://www.nature.com/articles/s41524-025-01720-4

**Step:** The post-ML-filter down-selection the card replaces with MD verification: Org-Mol ML-screens millions of esters, filters to a 461-candidate shortlist, then manually picks only two to synthesize and measure — exactly where the card would insert GPU-MD verification of the top 100–1000.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] Generation + ML filter runs at millions scale: >6 million saturated mono-/dibasic esters are constructed and screened by dielectric constant, yielding 8569 monoesters. (https://www.nature.com/articles/s41524-025-01720-4)
- VERIFIED [SUPPORTED, SUPPORTED] The downstream filter collapses the shortlist to 461 by predicted viscosity and thermal conductivity, then to 2 by human synthetic-feasibility judgement — no computational verification of hundreds of candidates exists. (https://www.nature.com/articles/s41524-025-01720-4)
- VERIFIED [SUPPORTED, SUPPORTED] People/institutions: Qi Ou, Minyang Zhuang, Lele Liu, Ning Wang (SINOPEC Research Institute of Petroleum Processing, Beijing); Hongshuai Wang, Shangqian Chen, Zhifeng Gao (DP Technology, Beijing); Zhifeng Gao (AI for Science Institute, Beijing). The model is a Uni-Mol-derived 3D transformer (Org-Mol). (https://www.nature.com/articles/s41524-025-01720-4)

**Activity:** active [SUPPORTED, SUPPORTED] The pipeline was published 11 July 2025 and is backed by multi-year funding from China Petroleum & Chemical Corp and the National Key R&D Program of China (grant 2024YFA1510200), indicating an ongoing effort rather than an archived one.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If MD verification keeps raising the best FOM, the Org-Mol pipeline would add a GPU-MD verification stage (100–1000 candidates) between the 461-candidate ML shortlist and synthesis, replacing the manual 2-candidate pick with an MD-ranked list — likely producing a verified coolant that beats commercial fluids and turning their 'two validated candidates' proof-of-concept into a scalable discovery engine.

**If not:** If MD FOM plateaus, their current practice is confirmed as already near-optimal: ML filtering to a few hundred then hand-picking two to synthesize is sufficient, and spending compute on MD-verifying hundreds-to-thousands of candidates would be a waste, so the pipeline stays ML-plus-sparse-experiment.

**Already done:** no [SUPPORTED, SUPPORTED] Org-Mol ML-screened millions of esters and experimentally validated two synthesized candidates; it never MD-verified hundreds-to-thousands of candidates' viscosity and thermal conductivity, so the card's scaling experiment has not been run by this team.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 3 | 3, 4, 3 | 1 |
| change | 3 | 3, 3, 3 | 0 |
| new | 5 | 5, 5, 4 | 1 |

- fit, opencode-go/qwen3.8-flash: Outcome suggests MD verification for esters, but current down-selection depends on predictions plus synthesis; a computational bridge is needed.
- fit, opencode-go/mimo-v2.6-flash: Card's MD ranks ester viscosity/thermal conductivity between their 461-shortlist and synthesis — same chemistry and quantities, but omits their dielectric filter.
- fit, opencode-go/minimax-m3: Card's MD verification step replaces their manual 2-candidate pick; step is in card terms, not theirs.
- change, opencode-go/qwen3.8-flash: Only rising FOM changes their ML-plus-hand-pick pipeline to add MD ranking; plateau confirms current two-candidate practice.
- change, opencode-go/mimo-v2.6-flash: Climbing outcome would insert an MD stage replacing their manual two-candidate pick; plateau only endorses current ML-plus-sparse-experiment practice.
- change, opencode-go/minimax-m3: If lever holds, they insert MD verification between ML shortlist and synthesis; if not, ML+sparse experiment confirmed—only lever changes.
- new, opencode-go/qwen3.8-flash: Org-Mol ML-screened millions and validated two experimentally; it never MD-verified hundreds-to-thousands candidates for the scaling question.
- new, opencode-go/mimo-v2.6-flash: Both checkers support that they never MD-verified hundreds-to-thousands of candidates — the card's scaling experiment is unrun by this team.
- new, opencode-go/minimax-m3: Group ML-screened millions and validated 2 experimentally; never MD-verified hundreds-to-thousands candidates' thermophysical properties.

## Gaps named by the researcher

- No programme measures the card's exact quantity: whether the best MD-ranked coolant's cooling FOM keeps improving as the number of MD-verified candidates grows from ~100 to ~1000 (vs. plateauing).
- Ewen group's MD verification covers only 8 representative molecules with no immersion-coolant FOM compared against commercial fluids; Sinton/FL01 verify experimentally and via CFD, not with MD; Org-Mol never MD-verified its shortlist.
- Activity of the Org-Mol/SINOPEC team is inferred from a July 2025 paper plus multi-year funding; no follow-on release was found by Oct 2026, so its 'active' state is weaker evidence than for the Ewen (Sep 2026 paper) and Sinton/FL01 (Nov 2025 launch, Sep 2026 prototyping) programmes.
