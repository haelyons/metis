# Working notes — IC-V3 (MD verification inserted into Org-Mol's ester shortlist)

## Card summary
- Root question: generative pipeline for discovery of single-phase immersion coolants.
- Card tests whether Green-Kubo (OPLS-AA) MD verification of viscosity + thermal conductivity
  *reorders* the Org-Mol ML ester shortlist (461 monoesters) vs merely confirming it.
- Scale: 100 -> 300 -> 1000 candidates, 8-GPU A100 node, GROMACS.
- "Check first": OPLS-AA reproduces Org-Mol Ester 1's measured 40 C viscosity 6.41 cSt within ±25%.

## Who the result would feed (candidates considered)
1. Org-Mol team = SINOPEC Research Institute of Petroleum Processing (RIPP) + DP Technology + AI for Science Institute (Beijing). The source of the 461-ester shortlist [s1]. PICKED.
2. LG AI Research — GATE framework, AI screening of immersion cooling fluids per OCP spec. PICKED.
3. Imperial College London Tribology Group (Dini) + James Ewen (Bath) — "Benchmarking ML and MD methods for thermophysical properties of organic liquids" (Digital Discovery, 2026). Closest prior / "already done" check. PICKED.
4. Open Compute Project (OCP) Immersion sub-project — defines the spec, not a discovery pipeline; mentioned only as the spec source in GATE paper.
5. David Sinton (U. Toronto) self-driving lab for immersion coolant discovery (2025). Not picked; overlaps with #2/#3.

## Programme 1 — Org-Mol (SINOPEC RIPP / DP Technology / AI for Science Institute)
- URL: https://www.nature.com/articles/s41524-025-01720-4 (DOI 10.1038/s41524-025-01720-4)
- Paper: Ou, Q., Wang, H., Zhuang, M. et al. "High-accuracy physical property prediction for pure organics via molecular representation learning: bridging data to discovery." npj Comput Mater 11, 224 (2025). Published 11 July 2025.
- Affiliations: SINOPEC Research Institute of Petroleum Processing Co., Ltd, Beijing; DP Technology, Beijing; AI for Science Institute, Beijing.
- Step the card targets: the gap between the 461-monoester ML shortlist and the manual pick of 2 candidates for synthesis.
  Quote: "By further incorporating manual synthetic feasibility assessments based on experimental expertise, we select two candidates for synthesis, and their physical properties are experimentally measured."
- How it handles the step today: ML-only (kinetic viscosity model then thermal conductivity model), then manual synthetic-feasibility pick; no MD.
  - "Monoesters with dielectric constants lower than 3.20 are then fed to the kinetic viscosity model and then the thermal conductivity model."
  - "Based on the aforementioned criteria of the kinematic viscosity and thermal conductivity, 461 monoesters are finally filtered out."
  - Their stated reason for avoiding MD: "It can be seen that predicting these physical properties via MD is time-consuming for a single system and becomes unaffordable in a high-throughput screening scenario with thousands of candidates".
- Activity: paper published 11 July 2025 (version of record). Active as of then; no later release found.
- already_done: no MD verification of the shortlist — they measured two esters experimentally, not by MD.

## Programme 2 — LG AI Research (GATE)
- URL: https://arxiv.org/abs/2510.23371 ; HTML https://arxiv.org/html/2510.23371v2
- Paper: "Towards a Generalizable AI for Materials Discovery: Validation through Immersion Coolant Screening" (arXiv:2510.23371), LG AI Research + Kyonggi University.
- Step the card targets: final validation stage of their 5-stage AI screening workflow (Fig. 2f).
  Quote: "Finally, experimental and literature validation confirm the physicochemical properties of selected candidates (Fig. 2 f), ensuring their suitability as single-phase immersion cooling fluids."
- How it handles the step today: TGA/DSC experimental + literature values; no MD of viscosity/thermal conductivity.
  - "Decomposition temperature was measured using thermogravimetric analysis (TGA, onset point) and specific heat using differential scanning calorimetry (DSC, 20℃). For other properties that could not be measured with our available instrumentation, we surveyed the literature and incorporated reported values into Fig. 3 d."
  - Scale: "Across the 41 million purchasable compounds and 2.54 billion in-silico reaction products examined, this screening yielded 356 candidates satisfying Criterion 1, and a total of 92,861 compounds meeting at least one of Criteria 1–6."
  - "From these, we selected four final candidates for experimental verification."
- Activity: arXiv v2 last revised 31 Oct 2025: "[Submitted on 27 Oct 2025 (v1), last revised 31 Oct 2025 (this version, v2)]".
- already_done: no MD verification — experimental + literature only.

## Programme 3 — Imperial College London Tribology Group (Dini) / Ewen (Bath)
- URL: https://pubs.rsc.org/dd/article/doi/10.1039/D6DD00260A/1362876/Benchmarking-Machine-Learning-and-Molecular ; DOI 10.1039/d6dd00260a ; also spiral.imperial.ac.uk (open PDF).
- Paper: Ogbomo, Carman, Dini, Ewen. "Benchmarking Machine Learning and Molecular Dynamics Methods for the Prediction of the Thermophysical Properties of Organic Liquids." Digital Discovery, first published 29 Sep 2026.
- Affiliations: Department of Mechanical Engineering, Imperial College London; James P. Ewen also Department of Mechanical Engineering, University of Bath.
- Step the card targets: the ML-vs-EMD benchmark of density/viscosity/thermal conductivity for organic liquids — the exact property pair + force-field family the card uses (Green-Kubo, OPLS/LOPLS-AA).
  Quote: "In this study, we benchmark ML models for the prediction of the density, viscosity, and thermal conductivity of lubricant-relevant organic liquids, and use MD simulations on a representative subset as an independent, physics-based assessment of the same properties."
- How it handles the step today: Green-Kubo EMD on 8 molecules (2 per chemical family: alkyl cycloalkanes, alkyl aromatics, esters, ethers) at 40 and 100 C, LOPLS-AA in LAMMPS.
  - "Finally, we apply Green–Kubo MD simulations to eight molecules, two from each of the four principal chemical families of the dataset, at 40 °C and 100 °C."
  - "All simulations were performed using the LOPLS-AA force field."
  - Key finding: "Viscosity errors are small for the pure hydrocarbons with LOPLS, but this property is consistently under-predicted for the oxygen-containing molecules; the reference ranking of the fluids is nonetheless largely preserved."
  - Conclusion: "At an inference cost orders of magnitude lower than EMD simulations, the ML models are well suited to high-throughput screening of new candidate molecules for lubricants and other formulated products."
- Activity: first published 29 Sep 2026: "Received: 05 May 2026 Accepted: 18 September 2026 First published: 29 September 2026".
- already_done: PARTLY — they ran Green-Kubo EMD viscosity/thermal conductivity on 8 organic liquids (incl. esters) and benchmarked vs ML, but not over a 100–1000 candidate shortlist and not the Org-Mol 461 esters. Their finding (ester/oxygenated viscosity under-prediction by LOPLS) directly bears on the card's "check first" OPLS-AA tolerance.

## Gaps found
- No published Green-Kubo viscosity + thermal conductivity over a 100–1000 candidate shortlist (closest is 8 molecules).
- Nobody has MD-verified the Org-Mol 461-monoester ranking; the card's check-first (reproducing Ester 1's 6.41 cSt) is untested.
- LG AI validates immersion-coolant candidates by literature/TGA/DSC, not by MD of transport properties.
- Force-field (LOPLS-AA) systematic under-prediction of ester viscosity is documented at n=8 but unquantified at shortlist scale.
