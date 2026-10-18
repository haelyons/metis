# Working notes — programmes that would use the "ml-ensemble-extremes" card result

Root question: Do more members of a machine-learned weather ensemble (AIFS-ENS) buy better
forecasts of rare extremes, or does shared model error cap the skill?

## Card summary
- Model under test: ECMWF's AIFS-ENS v1 (afCRPS-trained, exchangeable members of one trained
  distribution). Test: 7 dates x 1,000 members, subsample 10-1,000, score top-percentile
  wind/temp/rain vs ERA5 with fair CRPS and Brier; check whether skill keeps rising past 50 members.
- Closest prior cited by the card: HENS Part 2 (7,424 SFNO members, summer 2023) [s_hens].
- Check-first references ECMWF's AIFS-CRPS paper [s_crps_paper] and the 4-minute N320 member time.

## Programmes identified (3)

### 1. ECMWF — AIFS ENS (operational ML ensemble)
- The card's model is literally ECMWF's. The lever the card tests (ensemble size) is ECMWF's
  operational decision: it runs 51 members (50 perturbed + 1 control), 15-day, 6-hourly, 4x daily.
- Members are exchangeable draws of one afCRPS-trained distribution (noise injected in the
  processor). This is exactly the "shared model error caps tail" hypothesis the card's "if not"
  branch encodes.
- Activity: AIFS ENS v2 implemented 12 May 2026 (supersedes v1 which went operational 1 Jul 2025);
  AIFS-CRPS paper published in npj AI 2 Feb 2026.
- Already done (partly): ECMWF studied ensemble-size sensitivity and fair scores for physics-based
  IFS ENS up to 200 members (Leutbecher, "How many ensemble members are desirable?", Newsletter
  157, 2018), and that fair-score theory underlies afCRPS — but no published 1,000-member AIFS-ENS
  top-percentile extreme experiment.
- Key URLs:
  - https://www.ecmwf.int/en/newsletter/185/earth-system-science/aifs-ens-becomes-operational
  - https://confluence.ecmwf.int/pages/viewpage.action?pageId=620418893  (AIFS ENS v2)
  - https://huggingface.co/ecmwf/aifs-ens-2.0
  - https://www.nature.com/articles/s44387-026-00073-7  (AIFS-CRPS npj)
  - https://www.ecmwf.int/en/newsletter/157/news/how-many-ensemble-members-are-desirable

### 2. HENS (Huge Ensembles) — LBNL x NVIDIA x NERSC
- The card's direct prior [s_hens]. HENS Part 2 (GMD, 4 Sep 2025) ran 7,424 members =
  29 independently-trained SFNO checkpoints x 256 bred-vector IC perturbations, 92 summer-2023
  dates, 15-day rollouts; found huge ensembles sample ~4-sigma tails, reduce outliers, improve
  best-member RMSE up to 50%.
- CRITICAL distinction: HENS represents model uncertainty via 29 checkpoints; AIFS-ENS is a single
  trained distribution. The card asks whether HENS's "more members help" conclusion survives when
  there is no multi-checkpoint model perturbation — i.e., whether shared model error caps the tails.
- Activity: paper published 4 Sep 2025; method maintained as the "HENS recipe" in NVIDIA earth2studio
  (active repo, v0.19.0 on 30 Sep 2026, commits through 12 Oct 2026). Original LBNL forks
  (earth2mip-fork, modulus-makani-fork) are the archived reference (last push early 2025).
- Already done (partly): ran the huge-ensemble extreme-scoring experiment for SFNO-BVMC, not AIFS-ENS.
- Key URLs:
  - https://gmd.copernicus.org/articles/18/5605/2025/
  - https://arxiv.org/abs/2408.01581
  - https://github.com/NVIDIA/earth2studio/tree/main/recipes/hens
  - https://github.com/ankurmahesh/earth2mip-fork

### 3. NVIDIA Earth-2 (earth2studio)
- Open-source framework (NVIDIA PhysicsNeMo Team) that already ships first-class wrappers to RUN
  ECMWF's AIFS ENS (v0.11.0 "ECMWF AIFSENS ensemble prognostic model wrapper"; v0.16.0 "AIFS 2.0
  ensemble prognostic model (AIFS2ENS) with stochastic noise injection"; v0.10.0 "IFS_ENS, AIFS,
  AIFS_ENS data sources") and the ensemble verification metrics the card uses (Brier, CRPS, fair CRPS,
  energy score).
- The card's exact workflow (run AIFS-ENS 10-1,000 members, score top-percentile extremes) is a
  natural earth2studio recipe/scorecard feature.
- Already done (no): tooling exists, but no published 1,000-member AIFS-ENS extreme-scoring study.
- Key URLs:
  - https://github.com/NVIDIA/earth2studio
  - https://github.com/NVIDIA/earth2studio/blob/main/CHANGELOG.md
  - https://github.com/NVIDIA/earth2studio/releases
  - https://pypi.org/project/earth2studio/

## Not included
- Google DeepMind GenCast / FGN: probabilistic ML ensembles, but a different model (not AIFS-ENS);
  would not consume an AIFS-ENS-specific ensemble-size result directly.
- Physics-based huge-ensemble efforts (UNSEEN, IFS extended-range 101-member): not AIFS-ENS.

## Gaps / uncertainties
- Unknown whether ECMWF has run unpublished internal >51-member AIFS-ENS experiments for extremes;
  only the 51-member operational config and the physics-based IFS studies (<=200 members) are public.
- Did not capture the exact latest commit date of the HENS recipe folder inside earth2studio; activity
  inferred from earth2studio's overall v0.19.0 release (30 Sep 2026) and commits through 12 Oct 2026.
