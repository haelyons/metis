# Working notes — programmes that would use the immersion-coolant MD-verification scaling result

Root question: generative pipeline for discovery of single-phase immersion coolants.
Card: does MD-verifying more candidates (100 -> 300 -> 1000) keep raising the best cooling FOM
above commercial fluids, or plateau? Target step = GPU-MD verification of viscosity + thermal
conductivity on a ranked ML shortlist, compared against commercial fluids.

## Candidate programmes found

1. Ewen group (Imperial College London / University of Bath) — runs equilibrium/non-equilibrium MD
   on organic liquids and just benchmarked MD vs ML for thermophysical properties.
   - Digital Discovery (29 Sep 2026): "Benchmarking machine learning and molecular dynamics
     methods for the prediction of the thermophysical properties of organic liquids",
     DOI 10.1039/D6DD00260A. Authors Egheosa Ogbomo, Fionn Carman, Daniele Dini, James Patrick Ewen.
   - Abstract: ~4,700 reference values / 835 molecules C10-C50; XGBoost best; "Equilibrium
     molecular dynamics (EMD) simulations of eight representative molecules reproduce density
     accurately but show systematic, chemistry-dependent force-field errors for the viscosity and
     thermal conductivity." Only 8 molecules MD-verified -> no scaling curve.
   - ChemRxiv preprint (22 Apr 2026) DOI 10.26434/chemrxiv.15002312/v1, hydrocarbon version.
   - This is the closest thing to the card's MD step: they literally EMD-verify viscosity/thermal
     conductivity but at tiny scale, and found the ~force-field-error cap the card worries about.

2. Sinton Lab / FL01 (University of Toronto + Acceleration Consortium) — self-driving lab for
   coolant discovery, experimental high-throughput verification.
   - CSME paper 2025 "Accelerated fluid discovery for data center immersion cooling",
     DOI 10.82417/pw8c-8z69. "analyzes up to five samples per hour, achieving a 100x higher
     throughput than conventional methods"; ML benchmarked on >1,000 points / ten liquids + mixtures.
   - FL01 startup launched Nov 2025 (Acceleration Consortium news, Sep 1 2026). Patented sensors;
     "One of our devices can generate 10,000 data points in two months."
   - FOM for immersion coolants: Rezaei et al., J. Energy Storage 2025 (CFD + active learning,
     screened >1600 mixtures; active learning drove FOM with 15 data points).
   - They verify candidates experimentally, not with MD -> the card's MD-scaling result would
     tell them whether GPU-MD is a viable pre-filter before their wet-lab loop.

3. Org-Mol team (SINOPEC Research Institute of Petroleum Processing + DP Technology + AI for
   Science Institute) — the ML screening pipeline the card extends ([orgmol]).
   - npj Computational Materials 11, 224 (2025), published 11 July 2025.
     DOI/URL https://www.nature.com/articles/s41524-025-01720-4.
   - Screened >6 million esters -> 8569 monoesters (dielectric) -> 461 (viscosity + thermal
     conductivity) -> 2 synthesized and measured. Never MD-verified hundreds-to-thousands.
   - Funded by China Petroleum & Chemical Corp (124014) and National Key R&D Program of China
     (2024YFA1510200).

## Why these three

- Ewen group = the MD-verification step itself (the card's exact lever), at 8-molecule scale.
- Sinton/FL01 = the "verify + rank many candidates" step done experimentally at scale; the card
  tests whether a cheap MD pre-filter could feed their loop.
- Org-Mol = the generate+ML-filter step immediately upstream of the card's MD step; the card
  directly extends their pipeline (they stopped at 2 manual syntheses).

## Already done? (per programme)

- Ewen: partly — EMD benchmarked on 8 molecules, but no best-FOM vs N-verified scaling study.
- Sinton/FL01: no — verification is experimental/CFD, not MD; no MD scaling curve.
- Org-Mol: no — ML + 2 experimental validations, no MD verification at scale.

## Gaps the card fills

- Nobody measures whether the best MD-ranked coolant keeps improving as MD-verified candidates
  grow 100 -> 1000 (the card's exact question).
- Ewen's MD benchmark is 8 molecules, single fluids, no immersion-coolant FOM vs commercial fluids.
- Sinton verifies experimentally (5 samples/hr), so the "is GPU-MD a valid cheap pre-filter"
  question is open.
- Org-Mol never MD-verified its shortlist.

## Notes on uncertainty

- Org-Mol "active" is inferred from a July 2025 paper + multi-year funding; no follow-on release
  found by Oct 2026, so activity could be "unknown".
- RSC Digital Discovery landing page returned 403 to direct fetch; quotes taken from the RSC
  abstract surfaced via search and cross-checked with the ChemRxiv preprint and Imperial profile.
