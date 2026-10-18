# Frame check: card

Root question: Do more members of a machine-learned weather ensemble buy better forecasts of rare extremes, or does error shared by all members cap the skill?

Models: research opencode-go/deepseek-v4-pro; dramaturgs opencode-go/deepseek-v4.1-flash, opencode-go/glm-5.3-flash; critics opencode-go/qwen3.8-flash, opencode-go/mimo-v2.6-flash, opencode-go/minimax-m3.
Cost $0.2172 · 462,593 tokens · 10 min wall time.

**Best fit:** ECMWF — AIFS ENS (operational machine-learned ensemble), at "Generating exchangeable ensemble members from one afCRPS/multi-scale-trained distribution and verifying them (including top-percentile events) to set the operational ensemble size. Today ECMWF draws 51 members (50 perturbed + control) and scores 50-member ensembles against IFS, flagging extreme-event skill as still-unassessed.". Fit 5, change 5, new 5: 15 of 15.

## 1. ECMWF — AIFS ENS (operational machine-learned ensemble)

https://huggingface.co/ecmwf/aifs-ens-2.0

**Step:** Generating exchangeable ensemble members from one afCRPS/multi-scale-trained distribution and verifying them (including top-percentile events) to set the operational ensemble size. Today ECMWF draws 51 members (50 perturbed + control) and scores 50-member ensembles against IFS, flagging extreme-event skill as still-unassessed.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] Operational AIFS ENS runs 51 members on the N320 (~31 km) grid, 15-day, 6-hourly, four times per day; it is trained on 32 GH200 GPUs via the Anemoi framework by ECMWF's AIFS team (Lang, Leutbecher, Clare, Chantry, et al.). (https://huggingface.co/ecmwf/aifs-ens-2.0)
- VERIFIED [SUPPORTED, SUPPORTED] ECMWF verifies AIFS-CRPS as 50-member ensembles against the 50-member physics-based IFS ensemble, using analysis and radiosonde/SYNOP observations — the same 50-member baseline the card proposes to exceed. (https://www.nature.com/articles/s44387-026-00073-7)
- VERIFIED [SUPPORTED, SUPPORTED] ECMWF has explicitly not yet assessed AIFS-CRPS skill for extreme events, noting CRPS's limited sensitivity to distribution tails — exactly the gap the card's top-percentile scoring targets. (https://www.nature.com/articles/s44387-026-00073-7)
- VERIFIED [SUPPORTED, SUPPORTED] The card's 'check first' reproduction target comes from ECMWF's own reported N320 member runtime: about 4 minutes for a 15-day member on an A100 40 GB GPU. (https://www.nature.com/articles/s44387-026-00073-7)

**Activity:** active [SUPPORTED, PARTIAL] AIFS ENS has been operational since 1 July 2025 and was upgraded from v1 (afCRPS) to v2 on 12 May 2026, alongside IFS Cycle 50r1.

**If the lever:** If 1,000 exchangeable members keep improving top-percentile wind/temperature/rain scores past 50, ECMWF gets cheap direct evidence to raise operational AIFS ENS membership (or add a high-member extreme-event product such as percentiles/EFI), because members are near-free draws of one trained model — changing the current 51-member operational and verification choice.

**If not:** If skill flattens near 50 members, it confirms shared model error from the single trained distribution — not sampling — caps tail sharpness, so ECMWF would keep ~51 members and spend effort on better uncertainty representation instead (e.g., the multi-scale loss already adopted in v2, perturbed initial conditions, or perturbed-parameter ensembles).

**Already done:** partly [SUPPORTED, UNREACHABLE] ECMWF has studied ensemble-size convergence for the physics-based IFS ensemble (up to 200 members, Leutbecher 2017) but has not run a 10–1,000-member AIFS-ENS exchangeable-member rare-extreme saturation study; its own paper lists extreme-event skill as a next step.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 5 | 5, 5, 5 | 0 |
| change | 5 | 5, 5, 5 | 0 |
| new | 5 | 5, 5, 5 | 0 |

- fit, opencode-go/qwen3.8-flash: Card directly measures AIFS-ENS extreme-event skill versus member count, the quantity operational sizing depends on.
- fit, opencode-go/mimo-v2.6-flash: Card measures extreme-event skill vs member count for AIFS-ENS on the operational N320/A100 setup, exactly the quantity the 51-member sizing decision depends on.
- fit, opencode-go/minimax-m3: Card measures exchangeable AIFS-ENS extreme-event skill past 50 members on the same N320 system ECMWF's ensemble-size step depends on.
- change, opencode-go/qwen3.8-flash: Either outcome changes operational choice: scale AIFS-ENS members for extremes or confirm saturation and redirect uncertainty work.
- change, opencode-go/mimo-v2.6-flash: Both outcomes alter current practice: raise operational membership or keep ~51 and invest in uncertainty representation; programme is active.
- change, opencode-go/minimax-m3: Both outcomes change ECMWF's operational ensemble size: raise >51 if lever; keep ~51 and invest in uncertainty methods if not. Supported.
- new, opencode-go/qwen3.8-flash: Supported practice says ECMWF has not assessed AIFS-CRPS extreme-event skill beyond the 50-member baseline.
- new, opencode-go/mimo-v2.6-flash: Supported claims confirm extreme-event skill unassessed and no 10–1,000-member AIFS-ENS saturation study run; IFS-only convergence work does not answer it.
- new, opencode-go/minimax-m3: ECMWF flagged extreme-event skill as unassessed; no 10–1,000-member AIFS-ENS exchangeable saturation study done. Supported claim confirms gap.

## 2. HENS (Huge ENSembles) — NVIDIA Earth-2 / SFNO huge-ensemble project

https://github.com/NVIDIA/earth2studio/tree/main/recipes/hens

**Step:** Generating very large ensembles and sampling their tails for extreme-event statistics. Today HENS builds members from bred-vector initial-condition perturbations plus 29 independently trained SFNO checkpoints (real model uncertainty), not from exchangeable draws of a single distribution, and measures information gain vs member count.

**Practice claims and checks:**
- VERIFIED [PARTIAL, PARTIAL] HENS (Mahesh et al., NVIDIA with LBNL, UC Berkeley, Colorado State, UC Irvine, PNNL) ran 7,424 members per day over 92 summer-2023 dates — the card's 'closest prior' scale, but with a different ensemble scheme. (https://gmd.copernicus.org/articles/18/5605/2025/)
- VERIFIED [SUPPORTED, SUPPORTED] Their member-generation step is 256 bred-vector initial-condition perturbations per each of 29 independently trained checkpoints — the expensive multi-checkpoint machinery the card would test against cheap exchangeable draws. (https://gmd.copernicus.org/articles/18/5605/2025/)
- VERIFIED [SUPPORTED, SUPPORTED] HENS already measured tail-sampling (information gain ~4, i.e. 4-sigma events) as a function of ensemble size, showing bigger ensembles sharpen tails — but only for SFNO-BVMC, not for exchangeable draws. (https://gmd.copernicus.org/articles/18/5605/2025/)

**Activity:** active [SUPPORTED, SUPPORTED] The HENS recipe is maintained on the main branch of NVIDIA Earth2Studio, which released v0.19.0 on 30 September 2026.

**If the lever:** If exchangeable members of one CRPS-trained distribution keep gaining extreme-event skill past 50, it shows huge ensembles can be built from a single model's exchangeable draws — far cheaper than 29 checkpoints plus bred vectors — so the HENS approach could simplify to one trained model while retaining its tail-sampling benefit.

**If not:** If skill saturates near 50 for exchangeable draws, it vindicates HENS's design premise that genuine model uncertainty (multiple independently trained checkpoints) is what lets added members sample the tails, reinforcing the need for the multi-checkpoint/bred-vector machinery rather than plain member scaling.

**Already done:** partly [SUPPORTED, SUPPORTED] HENS already ran the 'more members sample the tails' experiment, but with SFNO-BVMC (bred vectors + 29 checkpoints); it does not test whether a single afCRPS-trained distribution's exchangeable members saturate, which is the card's question.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 3 | 3, 3, 3 | 0 |
| change | 5 | 3, 5, 5 | 2 |
| new | 3 | 3, 3, 3 | 0 |

- fit, opencode-go/qwen3.8-flash: Card tests tail-sampling scaling, but on AIFS-ENS, a stand-in for HENS's SFNO bred-vector/checkpoint system.
- fit, opencode-go/mimo-v2.6-flash: Card tests exchangeable AIFS-ENS draws, not HENS's bred-vector plus 29-checkpoint SFNO scheme; outcome feeds HENS's tail-sampling step only via a stand-in model.
- fit, opencode-go/minimax-m3: Card tests AIFS-ENS exchangeable draws; HENS uses SFNO-BVMC (bred vectors + 29 checkpoints), a different system serving as stand-in.
- change, opencode-go/qwen3.8-flash: Outcome could simplify HENS if transferred to SFNO; that bridge is not done, so change needs further work.
- change, opencode-go/mimo-v2.6-flash: Either result changes HENS design: simplify to one model's exchangeable draws, or justify keeping expensive multi-checkpoint machinery; programme is active.
- change, opencode-go/minimax-m3: If lever works, HENS could simplify to one model retaining tail benefit; if not, multi-checkpoint/bred-vector design is vindicated.
- new, opencode-go/qwen3.8-flash: HENS already measured tail-information gain versus member count for SFNO-BVMC, not for AIFS-ENS exchangeable draws.
- new, opencode-go/mimo-v2.6-flash: HENS already showed bigger ensembles sharpen 4-sigma tails, but only for SFNO-BVMC; exchangeable-draw saturation remains untested, so partly answered.
- new, opencode-go/minimax-m3: HENS ran 'more members sample tails' with SFNO-BVMC, not exchangeable draws — card's specific question partly answered.

## 3. Anemoi — ECMWF open-source ML weather framework (co-developed with European national meteorological services)

https://github.com/ecmwf/anemoi

**Step:** Running AIFS-ENS ensemble inference (reproducing the member runtime/memory the card checks first) and evaluating the forecasts — the framework and its verification tooling through which the card's 10–1,000-member sweep and scoring would be executed and documented.

**Practice claims and checks:**
- DISPUTED [UNSUPPORTED, PARTIAL] AIFS ENS is run through Anemoi's inference package (anemoi-inference), which is what the card's 'check first' step uses to reproduce the published 4-minute N320 member time and 38 GB memory on external hardware. (https://huggingface.co/ecmwf/aifs-ens-2.0)
- VERIFIED [SUPPORTED, SUPPORTED] Anemoi's verification is served by evaluation pipelines (e.g., MeteoSwiss's evalml) that run standard and diagnostic verification for Anemoi-built models — the tooling that would score the card's top-percentile wind/temperature/rain probabilities. (https://github.com/MeteoSwiss/evalml)
- VERIFIED [SUPPORTED, SUPPORTED] anemoi-training recently added ensemble 'graph scores' (energy/CRPS/variogram) for spatial ensemble scoring, showing active work on ensemble-verification tooling adjacent to the card. (https://github.com/ecmwf/anemoi-core/commit/11e8498e4b3fa38c32e80089f521387f7d2f19ec)

**Activity:** active [SUPPORTED, PARTIAL] anemoi-core is under active development, publishing graphs v0.9.8 and training-0.17.1 on 1 October 2026; the anemoi-inference package was last pushed 16 October 2026.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** Anemoi's documentation and reference configs could gain a reproducible ensemble-size guideline: how many exchangeable members to draw for top-percentile products, and reference verification configs running >51 members for extreme-event scoring across the ECMWF-and-national-met-service user community.

**If not:** Anemoi could document ~50 members as sufficient for its AIFS-ENS users, keeping effort on improving model uncertainty (multi-scale loss, graph/energy scores) rather than scaling member counts in inference and evaluation workflows.

**Already done:** no [SUPPORTED, SUPPORTED] Anemoi is a framework and tooling project, not an ensemble-size research programme; neither it nor its evaluation tooling has published a 10–1,000-member AIFS-ENS extreme-tail saturation experiment.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 3 | 3, 3, 3 | 0 |
| change | 3 | 3, 3, 5 | 2 |
| new | 5 | 5, 5, 5 | 0 |

- fit, opencode-go/qwen3.8-flash: Its step is stated only in card terms; AIFS-ENS runtime/scoring is a stand-in use of Anemoi tooling.
- fit, opencode-go/mimo-v2.6-flash: Step stated in card's terms, capping at 3; inference-runtime claim only PARTIAL, and Anemoi provides tooling rather than depending on the skill outcome.
- fit, opencode-go/minimax-m3: Step framed in card's terms (Anemoi as AIFS-ENS runtime/eval tool); Anemoi's own step is framework tooling, capped at 3.
- change, opencode-go/qwen3.8-flash: Outcome might add Anemoi documentation/config guidance, but this requires work and is not a current operational decision.
- change, opencode-go/mimo-v2.6-flash: Either outcome could inform member-count documentation and reference configs, but converting results into framework guidance is further work the card does not do.
- change, opencode-go/minimax-m3: Outcomes change Anemoi docs and reference configs: ensemble-size guideline and >51-member verification configs, or documenting ~50 sufficient.
- new, opencode-go/qwen3.8-flash: Supported claims say Anemoi has not published a 10–1,000-member AIFS-ENS extreme-tail saturation study.
- new, opencode-go/mimo-v2.6-flash: Supported checks confirm neither Anemoi nor its evaluation tooling has published a 10–1,000-member AIFS-ENS extreme-tail saturation experiment.
- new, opencode-go/minimax-m3: Supported claim: Anemoi is framework/tooling, has not published this 10–1,000-member AIFS-ENS extreme-tail saturation experiment.

## Gaps named by the researcher

- No published work has run the card's exact experiment: 10–1,000 exchangeable AIFS-ENS (afCRPS) members scored for top-percentile wind/temperature/rain against ERA5. ECMWF's ensemble-size convergence work is for the physics-based IFS ensemble, and HENS's is for SFNO-BVMC (bred vectors + 29 checkpoints), so the exchangeable-draw saturation question is open.
- AIFS-ENS v2 (implemented 12 May 2026) replaced the afCRPS loss with a multi-scale loss; members remain exchangeable draws, so a v1 result would need re-checking against v2 before any programme changes practice.
