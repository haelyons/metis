# Frame check: card

Root question: generative pipeline for discovery of single phase immersion coolants

Models: research opencode-go/deepseek-v4-pro; dramaturgs opencode-go/deepseek-v4.1-flash, opencode-go/glm-5.3-flash; critics opencode-go/qwen3.8-flash, opencode-go/mimo-v2.6-flash, opencode-go/minimax-m3.
Cost $0.1591 · 413,699 tokens · 11.6 min wall time.

**Best fit:** Org-Mol — SINOPEC Research Institute of Petroleum Processing / DP Technology / AI for Science Institute, at "The hand-off from the Org-Mol machine-learning shortlist to synthesis: after screening over 6 million esters and filtering 461 monoesters on predicted dielectric constant, viscosity and thermal conductivity, they pick candidates for synthesis manually. This is exactly the slot where the card inserts Green-Kubo MD verification of viscosity and thermal conductivity before synthesis.". Fit 5, change 5, new 5: 15 of 15.

## 1. Org-Mol — SINOPEC Research Institute of Petroleum Processing / DP Technology / AI for Science Institute

https://www.nature.com/articles/s41524-025-01720-4

**Step:** The hand-off from the Org-Mol machine-learning shortlist to synthesis: after screening over 6 million esters and filtering 461 monoesters on predicted dielectric constant, viscosity and thermal conductivity, they pick candidates for synthesis manually. This is exactly the slot where the card inserts Green-Kubo MD verification of viscosity and thermal conductivity before synthesis.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] The shortlist-to-synthesis step is handled today with machine-learning property models only — the kinetic viscosity model then the thermal conductivity model — with no molecular-dynamics verification in between. (https://www.nature.com/articles/s41524-025-01720-4)
- VERIFIED [SUPPORTED, SUPPORTED] The working shortlist is 461 monoesters, of which only two are actually synthesized and measured; the rest are never independently verified. (https://www.nature.com/articles/s41524-025-01720-4)
- VERIFIED [SUPPORTED, SUPPORTED] The team's stated reason for not running MD is cost at screening scale — a claim the card directly tests by parallelising Green-Kubo runs. (https://www.nature.com/articles/s41524-025-01720-4)

**Activity:** active [SUPPORTED, SUPPORTED] The Org-Mol paper (the source of the 461-monoester shortlist) was published in npj Computational Materials on 11 July 2025; no later release from this collaboration was found.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If MD reorders the shortlist, the team would stop selecting two candidates by manual synthetic feasibility from an unverified ML ranking: they would run Green-Kubo viscosity/thermal conductivity over the top 100–300 (or all 461) monoesters and synthesize MD-verified leaders, likely surfacing esters better than the two they measured, and the MD-verified points would become training data to correct the 22.5% MAPE viscosity model.

**If not:** If MD merely confirms the ML ranking unchanged from 100 through 1000 candidates, the published ML-only screening stays as-is and MD is demoted to an optional spot-check, so their practice changes nothing beyond a one-off validation of the pipeline.

**Already done:** no [SUPPORTED, SUPPORTED] This team has not run the card's experiment: the 461 monoesters were ranked by ML models and only two were verified, experimentally by synthesis rather than by MD; no Green-Kubo viscosity/thermal conductivity verification of the shortlist was performed.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 5 | 3, 5, 5 | 2 |
| change | 5 | 3, 5, 5 | 2 |
| new | 5 | 5, 5, 5 | 0 |

- fit, opencode-go/qwen3.8-flash: Outcome feeds ML-to-synthesis shortlist, but step framed via card terms; capped at three.
- fit, opencode-go/mimo-v2.6-flash: Card measures MD viscosity/thermal conductivity on Org-Mol's exact 461-monoester shortlist, the quantity their ML models use at the shortlist-to-synthesis step.
- fit, opencode-go/minimax-m3: Card measures Green-Kubo viscosity/thermal conductivity on Org-Mol's exact 461 monoester system, feeding the shortlist-to-synthesis step directly.
- change, opencode-go/qwen3.8-flash: Reordering would change synthesis choice; confirmation leaves ML-only practice unchanged, so only one outcome.
- change, opencode-go/mimo-v2.6-flash: Reordering changes which esters get synthesized and adds MD training data; confirming demotes MD to spot-check — either outcome alters a current choice.
- change, opencode-go/minimax-m3: Both outcomes change which two candidates get synthesized and whether ML training data gets corrected from 22.5% MAPE.
- new, opencode-go/qwen3.8-flash: Supported practice lacks Green-Kubo verification; Org-Mol has not tested MD-vs-ML shortlist reordering.
- new, opencode-go/mimo-v2.6-flash: Both checkers supported that no Green-Kubo verification of the 461-monoester shortlist was performed; only two candidates verified by synthesis.
- new, opencode-go/minimax-m3: Supported claims confirm no Green-Kubo MD was run on this shortlist; only two of 461 esters were ever verified.

## 2. LG AI Research — GATE (Geometrically Aligned Transfer Encoder)

https://arxiv.org/abs/2510.23371

**Step:** The final validation stage (Fig. 2f) of their five-stage AI-enabled high-throughput screening workflow for single-phase immersion cooling fluids: after GATE screens billions of candidates down to a shortlist, the chosen few are validated before deployment. The card's MD verification of viscosity and thermal conductivity targets this validation step.

**Practice claims and checks:**
- VERIFIED [PARTIAL, SUPPORTED] Validation today is experimental (TGA, DSC) plus literature values; transport properties like viscosity and thermal conductivity that their instruments cannot measure are taken from the literature rather than computed by MD. (https://arxiv.org/html/2510.23371v2)
- VERIFIED [SUPPORTED, SUPPORTED] The screening operates at billion-molecule scale but narrows to only four experimentally verified candidates, so most shortlisted molecules never get a physics-based check of their viscosity/thermal conductivity. (https://arxiv.org/html/2510.23371v2)
- VERIFIED [SUPPORTED, SUPPORTED] Four finalists are the extent of their verification stage; the pipeline is run by LG AI Research with Kyonggi University. (https://arxiv.org/html/2510.23371v2)

**Activity:** active [SUPPORTED, SUPPORTED] LG AI Research's GATE immersion-coolant paper was posted to arXiv on 27 October 2025 and last revised 31 October 2025 (v2), the most recent release found.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If MD reorders a 100–1000 candidate shortlist, LG AI Research would gain a physics-based verification stage to insert between GATE's 92,861-molecule shortlist and its 4-candidate experimental validation — re-ranking viscosity/thermal conductivity by Green-Kubo before purchase/synthesis and catching candidates GATE mis-orders, rather than relying on literature values.

**If not:** If MD only confirms GATE's ranking, the existing literature-plus-TGA/DSC validation remains sufficient and MD verification would not earn a permanent place in their pipeline, so their practice would be unchanged.

**Already done:** no [SUPPORTED, SUPPORTED] LG AI Research has not run MD verification of viscosity/thermal conductivity on their shortlist; their validation stage is experimental measurement and literature survey only.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 4 | 3, 4, 4 | 1 |
| change | 3 | 3, 3, 5 | 2 |
| new | 5 | 5, 5, 5 | 0 |

- fit, opencode-go/qwen3.8-flash: Card validates Org-Mol esters, not LG candidates; LG would bridge molecules, scale, and validation stage.
- fit, opencode-go/mimo-v2.6-flash: Card measures exactly the transport properties LG takes from literature at validation, but on Org-Mol esters, not LG's shortlist — a bridgeable stand-in system.
- fit, opencode-go/minimax-m3: Card measures the exact property pair (viscosity, thermal conductivity) GATE's validation stage needs, but on esters not GATE's broader organic space.
- change, opencode-go/qwen3.8-flash: Reorder adds physics-based verification stage; confirmation leaves literature/TGA-DSC validation unchanged, so only one outcome.
- change, opencode-go/mimo-v2.6-flash: Only a reordering outcome would justify inserting an MD stage; if MD merely confirms, their literature-plus-TGA/DSC validation stays, so one outcome changes practice.
- change, opencode-go/minimax-m3: If MD reorders, physics-based verification replaces literature-based validation; if not, MD is demoted to spot-check — practice changes either way.
- new, opencode-go/qwen3.8-flash: Supported practice uses literature and experiments, not MD; it has not answered shortlist reordering.
- new, opencode-go/mimo-v2.6-flash: Both checkers supported that LG's validation is experimental and literature-based, with no MD verification of viscosity or thermal conductivity performed.
- new, opencode-go/minimax-m3: Supported claims confirm LG has not run MD viscosity/thermal conductivity verification; their validation is experimental and literature-only.

## 3. Imperial College London Tribology Group (Dini) / Ewen (Bath) — MD-vs-ML thermophysical benchmarking

https://doi.org/10.1039/d6dd00260a

**Step:** Their head-to-head benchmark of machine-learning models against equilibrium molecular-dynamics (Green-Kubo) simulations for density, viscosity and thermal conductivity of organic liquids (lubricant- and cooling-fluid-sized molecules) — the exact property pair and force-field family the card deploys at shortlist scale.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] Their MD practice today is Green-Kubo equilibrium MD on only eight molecules — two each from four chemical families including esters — at 40 and 100 °C, i.e. n=8 rather than the card's 100–1000. (https://spiral.imperial.ac.uk/server/api/core/bitstreams/fa07c113-8958-4f1e-a010-0ef2bfc39e17/content)
- VERIFIED [SUPPORTED, SUPPORTED] They use the same OPLS-family force field the card specifies, run in LAMMPS. (https://spiral.imperial.ac.uk/server/api/core/bitstreams/fa07c113-8958-4f1e-a010-0ef2bfc39e17/content)
- VERIFIED [SUPPORTED, SUPPORTED] They already found chemistry-dependent force-field error for the property pair the card targets: viscosity is under-predicted for oxygen-containing (ester/ether) molecules, though the reference ranking is largely preserved. (https://spiral.imperial.ac.uk/server/api/core/bitstreams/fa07c113-8958-4f1e-a010-0ef2bfc39e17/content)

**Activity:** active [SUPPORTED, SUPPORTED] The paper was published in Digital Discovery (RSC) with version of record dated 29 September 2026, a few weeks before this search.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If MD measurably reorders a 100–1000 candidate shortlist, their current conclusion that ML alone is 'well suited to high-throughput screening' would need revision: they would have to recommend MD as a verification stage before synthesis for immersion coolants, contradicting their n=8 finding that MD adds little over ML for ranking.

**If not:** If MD merely confirms the ML ranking, it corroborates their existing result that 'the reference ranking of the fluids is nonetheless largely preserved' by MD — so their practice stays as published: ML for screening, MD only as an extrapolation/force-field sanity check.

**Already done:** partly [SUPPORTED, SUPPORTED] This group has already run a smaller version of the card's experiment — Green-Kubo EMD viscosity and thermal conductivity of organic liquids (including esters) benchmarked against ML — but on eight molecules, not a 100–1000 candidate shortlist and not the Org-Mol 461 esters; their finding that LOPLS-AA under-predicts ester viscosity bears directly on the card's OPLS-AA check-first tolerance.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 4 | 3, 4, 4 | 1 |
| change | 3 | 3, 3, 4 | 1 |
| new | 3 | 3, 3, 3 | 0 |

- fit, opencode-go/qwen3.8-flash: Outcome directly feeds their MD-vs-ML benchmark, but step is card-framed, so capped at three.
- fit, opencode-go/mimo-v2.6-flash: Same Green-Kubo/OPLS-family property pair the card deploys, but on eight molecules vs 100–1000 shortlist scale and different specific esters — a scale bridge.
- fit, opencode-go/minimax-m3: Card uses identical property pair, Green-Kubo method, and OPLS-family force field on ester-containing molecules — direct extension of their benchmark.
- change, opencode-go/qwen3.8-flash: Reordering would revise their screening recommendation; confirmation merely corroborates their published ranking result.
- change, opencode-go/mimo-v2.6-flash: Reordering would force revising their 'ML well suited to screening' conclusion; confirmation only corroborates their published ranking-preserved finding, changing nothing.
- change, opencode-go/minimax-m3: If MD reorders, their 'ML well-suited' conclusion needs revision; if not, it corroborates — either way, published recommendation changes.
- new, opencode-go/qwen3.8-flash: Partly answered: they benchmarked Green-Kubo and ML, but only eight molecules, not shortlist scale.
- new, opencode-go/mimo-v2.6-flash: Partly answered: they already ran Green-Kubo vs ML on eight molecules including esters, finding preserved ranking and ester viscosity under-prediction — smaller scale.
- new, opencode-go/minimax-m3: Already partly answered: they ran Green-Kubo on n=8 organics including esters; card extends question to n=100–1000 and Org-Mol shortlist.

## Gaps named by the researcher

- No published work runs Green-Kubo viscosity and thermal conductivity over a 100–1000 candidate ester shortlist; the closest prior (Imperial/Dini-Ewen) covers only eight molecules, two of which are esters.
- Nobody has MD-verified the Org-Mol 461-monoester ranking, so the card's check-first (OPLS-AA reproducing Ester 1's 6.41 cSt within ±25%) is untested.
- LG AI Research validates immersion-coolant candidates by TGA/DSC and literature only, leaving viscosity/thermal conductivity of the ~92,861 shortlist physically unverified before selection.
- LOPLS-AA's systematic under-prediction of viscosity for oxygen-containing (ester) molecules is documented at n=8 but unquantified at shortlist scale, so whether MD actually reorders a large ester ranking is genuinely open.
