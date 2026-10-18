# Working notes — programmes fed by the ml-ensemble-extremes card

Card: does 10–1,000 AIFS-ENS members beat 50 for top-percentile wind/temperature/rain
probabilities, or does shared model error (exchangeable draws of one afCRPS-trained
distribution) cap the skill? Test runs AIFS-ENS v1, 7 dates x 1,000 members, scores
top-percentile fields vs ERA5 with fair CRPS + Brier, checks whether skill rises past 50.

## Programme 1 — ECMWF, AIFS ENS (operational machine-learned ensemble)
- This is the direct target. The card reproduces AIFS-ENS v1 (afCRPS) and sweeps 10–1,000 members.
- Operational model page / model card: https://huggingface.co/ecmwf/aifs-ens-2.0
- Science paper (AIFS-CRPS): https://arxiv.org/abs/2412.15832 ; journal: https://www.nature.com/articles/s44387-026-00073-7
- Step targeted: member generation (exchangeable draws) + verification of extreme-event skill + the operational
  ensemble-size choice. Today: 51 members (50 + control), N320, 15-day, 4x/day; scored as 50-member ensembles vs IFS.
- Key quotes:
  - "The trained model is stochastic and can generate as many exchangeable members as desired and computationally feasible in inference." (arxiv 2412.15832 abstract)
  - "It is run operationally by ECMWF, generating a 51-member 15-day (6-hourly) global forecast four times per day." (HF card)
  - "We compare 50-member 15-day AIFS-CRPS ensemble forecasts with the 9-km 50-member ECMWF IFS (Integrated Forecasting System) ensemble forecasts." (nature)
  - "An important next step is the assessment of the forecast skill of extreme events. Here, CRPS can have limited sensitivity to tail properties of distributions." (nature)
  - "a single member 15 day forecast is created in about one minute for AIFS-CRPS O96 and four minutes for AIFS-CRPS N320 on an NVIDIA A100 40 GB GPU, including the time spent reading the initial state and writing the forecast to disk." (nature) — the card's reproduction target.
- Activity: active. "The ensemble model has been running operationally since 1 July 2025 and was upgraded from AIFS ENS v1 to AIFS ENS v2 on 12 May 2026." (https://www.ecmwf.int/en/forecasts/datasets/aifs-machine-learning-data)
- Already done? partly. ECMWF has done ensemble-size convergence for the physics-based IFS ensemble (Leutbecher 2017,
  up to 200 members), not for AIFS-ENS exchangeable members; extreme-event skill explicitly flagged as next step.
  - https://www.ecmwf.int/sites/default/files/elibrary/2017/17621-ensemble-size-how-suboptimal-less-infinity.pdf
    "50 and 200 members are 2% and 0.5% worse than ∞ , respectively"

## Programme 2 — HENS (Huge ENSembles), NVIDIA Earth-2 / SFNO project
- The card's "closest prior" [s_hens]. HENS already ran a 7,424-member huge ensemble but with a different
  ensemble-generation scheme (bred vectors + 29 independently trained SFNO checkpoints = genuine model uncertainty),
  not exchangeable draws of a single afCRPS-trained distribution.
- Recipe home (current, maintained): https://github.com/NVIDIA/earth2studio/tree/main/recipes/hens
- Paper: https://gmd.copernicus.org/articles/18/5605/2025/
- Step targeted: huge-ensemble generation + tail/outlier sampling for extreme events.
- Key quotes:
  - "HENS uses customized bred vectors for initial condition perturbations and multiple independently trained model checkpoints to represent model uncertainty, specifically designed for better representation of extreme weather events." (recipes/hens README)
  - "Here in Part 2, we generate a huge ensemble (HENS), with 7424 members initialized each day of summer 2023." (GMD)
  - "Here, we combine these two perturbation techniques to create a 7424-member ensemble: 256 initial condition perturbations for each of the 29 SFNO checkpoints." (GMD)
  - "The 7424-member ensemble has an information gain of 4. This means that HENS is large enough to have at least one ensemble member that is 4 standard deviations away from the ensemble mean (on average)." (GMD)
  - "We use this estimate of 7000 to guide our choice of ensemble size for HENS." (GMD)
- Activity: active. Earth2Studio v0.19.0 released 2026-09-30 (https://github.com/NVIDIA/earth2studio/releases/tag/0.19.0).
- Already done? partly — analogous experiment but SFNO-BVMC, not AIFS-ENS exchangeable draws.

## Programme 3 — Anemoi (ECMWF open-source ML weather framework, co-developed with European NMS)
- Where AIFS-ENS is actually run/reproduced (anemoi-inference) and where verification tooling lives.
- https://github.com/ecmwf/anemoi ; inference: https://github.com/ecmwf/anemoi-inference ; core: https://github.com/ecmwf/anemoi-core
- Step targeted: running AIFS-ENS ensemble inference (reproducing member runtime/memory) + evaluation/verification tooling.
- Key quotes:
  - "As an 'end to end' framework, it provides a comprehensive toolkit that spans data preparation, model training, and inference, enabling meteorological organizations to leverage their own data for ML-based weather prediction." (github ecmwf/anemoi README)
  - "AIFS ENS v2 is implemented using the Anemoi framework. Anemoi consists of open source components, enabling the user community to run AIFS themselves." (HF aifs-ens-2.0 card)
  - "Run evaluation pipelines for data-driven weather models built with Anemoi." (https://github.com/MeteoSwiss/evalml)
  - "These ensemble scores assess spatial structure across graph neighbourhoods, edge differences, global fields, variables (global energy) and spectral amplitudes" (anemoi-core commit 11e8498e, "graph scores", 2026-08-20)
- Activity: active. anemoi-core released graphs v0.9.8 / training-0.17.1 on 2026-10-01; anemoi-inference pushed 2026-10-16.
- Already done? no — Anemoi is tooling; it has not run the 10–1,000-member AIFS-ENS extreme-tail saturation experiment.

## Gaps
- Nobody has run the exact experiment: 10–1,000 exchangeable AIFS-ENS (afCRPS) members scored for top-percentile
  wind/temp/rain vs ERA5. ECMWF's ensemble-size work is for physics-based IFS; HENS's is for SFNO-BVMC.
- AIFS-ENS v2 (12 May 2026) swapped afCRPS for a multi-scale loss; members are still exchangeable draws, so a v1
  result would need re-checking on v2 before changing practice.
