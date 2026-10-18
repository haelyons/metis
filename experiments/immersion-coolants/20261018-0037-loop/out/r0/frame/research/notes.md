# Working notes — programmes that would feed on the "generative single-phase immersion coolant" card

## Card in one line
Test: ML-filter a million PFAS-free esters/hydrocarbons, then GPU-MD verify viscosity + thermal conductivity of the top 100/300/1000, and compare cooling FOM to commercial fluids — does best FOM keep rising or plateau?

## Programmes found (3)

### 1. ENEOS Holdings (industrial) — NVIDIA ALCHEMI + Matlantis PFP
- URL: https://www.hd.eneos.co.jp/english/news/release_information/year/2025/20251205_02_01_mr03/
- Markets single-phase immersion coolants ("ENEOS IX series").
- Dec 5 2025 release: screened ~10M molecular candidates against dielectric/thermal properties, identified ~1,000 for further experimental evaluation.
- Toolchain: NVIDIA ALCHEMI NIMs (BCS = conformer/dipole, BMD = bulk MD, batched DFT), KPGT for flash point, Matlantis PFP MLIP (Preferred Networks + ENEOS), PFP accelerated "several tens of times".
- KEY: their MD step (BMD NIM) computes bulk **dielectric constant**, NOT viscosity/thermal conductivity. Card's GPU-MD of viscosity+TC at 100→1000 is the missing tier.
- Activity: active — Dec 2025 release; SC25 presentation Nov 2025; further results at NVIDIA GTC 2026 (session P81185).

### 2. Org-Mol (Sinopec RIPP / DP Technology / AI for Science Institute) — the card's "[orgmol]"
- URL: https://www.nature.com/articles/s41524-025-01720-4 (also arXiv:2501.09896)
- Authors: Qi Ou (Sinopec RIPP), Hongshuai Wang + Zhifeng Gao (DP Technology / AI for Science Institute).
- Screened >6M esters; ML predicts dielectric const → viscosity → thermal conductivity; 461 monoesters pass; 2 synthesized + experimentally measured.
- Explicitly says MD for these properties is "unaffordable in a high-throughput screening scenario with thousands of candidates" and accuracy depends on force field — exactly the gap the card fills.
- Activity: active — open-access npj publication 11 July 2025; structures on Zenodo.

### 3. GATE (LG AI Research / Kyonggi University)
- URL: https://arxiv.org/abs/2510.23371
- Generalizable AI, 34 properties, 10 relevant to OCP immersion-cooling spec (incl. dynamic viscosity, density, dielectric constant).
- Screened 41M purchasable + 2.54B in-silico; 92,861 candidates; 4 validated via TGA/DSC + literature.
- Activity: active — arXiv v1 27 Oct 2025, v2 31 Oct 2025.

## Already done?
- ENEOS: partly — runs large-scale MLIP-MD (BMD NIM/PFP) screening on dielectric/thermal, but not MD viscosity+TC FOM-vs-N scaling.
- Org-Mol: no — ML + 2 experimental validations, no MD at scale.
- GATE: no — ML + 4 experimental/literature validations, no MD at scale.
- No programme found has published the specific "best cooling FOM vs number of MD-verified candidates (100→1000)" plateau experiment.

## Key verbatim quotes (with source)
- ENEOS release: "For immersion cooling fluids aimed at data center thermal management, the workflow screened on the order of ten million molecular candidates against dielectric and thermal properties and identified approximately 1,000 molecules that met or exceeded the target performance envelope for further experimental evaluation."
- NVIDIA dev blog: "Next, the BMD NIM was used to calculate bulk dielectric constants and identify candidates with low dielectric constants. Finally, flash point predictions were made using a KPGT model."
- Org-Mol (arXiv): "predicting these physical properties via MD is time-consuming for a single system and become unaffordable in a high-throughput screening scenario with thousands of candidates"
- GATE (arXiv): "Finally, experimental and literature validation confirm the physicochemical properties of selected candidates (Fig. 2 f), ensuring their suitability as single-phase immersion cooling fluids."

## Decision
All three are returned. No programme currently runs the exact experiment, so all already_done = partly/no.
