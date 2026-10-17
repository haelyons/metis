# Frame check: card

Root question: Industrial food ingredient replacement for sustainability? Industrial food recipe replacement for sustainability?

Models: research opencode-go/deepseek-v4-pro; dramaturgs opencode-go/deepseek-v4.1-flash, opencode-go/glm-5.3-flash; critics opencode-go/qwen3.8-flash, opencode-go/mimo-v2.6-flash, opencode-go/minimax-m3.
Cost $0.1465 · 316,794 tokens · 7.4 min wall time.

**Best fit:** Meta AI (FAIR) — GISMo / Recipe1MSubs (facebookresearch/gismo), at "The GISMo ingredient encoder (IE): the GIN-based node encoder whose embedding width (the `emb_d`/`hidden` dimensions) is exactly the capacity axis the card sweeps (64–512) before the ingredient-substitution decoder ranks candidate substitutes.". Fit 5, change 5, new 5: 15 of 15.

## 1. Meta AI (FAIR) — GISMo / Recipe1MSubs (facebookresearch/gismo)

https://github.com/facebookresearch/gismo

**Step:** The GISMo ingredient encoder (IE): the GIN-based node encoder whose embedding width (the `emb_d`/`hidden` dimensions) is exactly the capacity axis the card sweeps (64–512) before the ingredient-substitution decoder ranks candidate substitutes.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] The reference GISMo training command fixes the ingredient-encoder width at 300 dimensions (`hidden=300 emb_d=300`), with 2 GIN layers, 400 epochs and regular negative sampling — the single width the card would vary. (https://github.com/facebookresearch/gismo/blob/main/gismo/README.md)
- VERIFIED [SUPPORTED, SUPPORTED] GISMo's published Recipe1MSubs test result — MRR 31.51 and Hit@1 20.56, averaged over 5 runs — is the exact baseline the card's 'Check first' reproduction targets. (https://ar5iv.labs.arxiv.org/html/2302.07960)
- VERIFIED [SUPPORTED, SUPPORTED] The model is implemented in PyTorch with the Deep Graph Library (DGL) for sparse graph operations, over a 6,653-ingredient FlavorGraph-derived vocabulary and the ~49k-pair Recipe1MSubs training split — the scale and tooling the card would reuse. (https://ar5iv.labs.arxiv.org/html/2302.07960)
- VERIFIED [SUPPORTED, SUPPORTED] The project is an archived, read-only open-source benchmark (Meta AI authors), not an actively developed product, and GISMo feeds a personalized inverse-cooking (image-to-recipe) pipeline. (https://github.com/facebookresearch/gismo)

**If the lever:** It would overturn the project's fixed-width default: the archived 300-dim GIN ingredient encoder would be shown to leave ranking quality on the table, so any future GISMo-style substitution ranker (including the personalized inverse-cooking integration) should scale the ingredient-encoder width; width would become a published scaling curve rather than an untested hyperparameter.

**If not:** It would confirm GISMo's 300-dim ingredient encoder was already at the plateau, validating the original fixed-width configuration and telling future work to seek gains from graph structure, context, or training data (the paper's own ablations) rather than from model capacity.

**Already done:** partly [CONTRADICTED, CONTRADICTED] Meta only ever trained and evaluated GISMo at a single ingredient-encoder width (hidden=300, emb_d=300); the paper's 5-run average is at that one width and no 64–512 sweep exists in the paper or repo.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 5 | 5, 5, 5 | 0 |
| change | 5 | 5, 5, 5 | 0 |
| new | 5 | 5, 3, 5 | 2 |

- fit, opencode-go/qwen3.8-flash: Card directly measures GISMo ingredient-encoder width effect on Recipe1MSubs Hit@1, exactly the quantity its fixed-width baseline step depends on.
- fit, opencode-go/mimo-v2.6-flash: Card measures Hit@1 versus encoder width on GISMo itself, the exact system and metric the reference command and published baseline depend on.
- fit, opencode-go/minimax-m3: Card directly measures GISMo encoder width (64-512) versus Hit@1 on Recipe1MSubs, the exact axis this step sweeps.
- change, opencode-go/qwen3.8-flash: Either scaling-up or plateauing would decide whether future GISMo rankers should scale encoder width or pursue graph/data gains.
- change, opencode-go/mimo-v2.6-flash: Both outcomes alter a build choice: publish a width scaling curve or validate the fixed 300-dim default for future rankers.
- change, opencode-go/minimax-m3: Either outcome changes the GISMo fixed-width default: validates or replaces the 300-dim encoder configuration.
- new, opencode-go/qwen3.8-flash: Supported claims show current GISMo practice uses only width 300; no verified width-sweep measurement feeds that step.
- new, opencode-go/mimo-v2.6-flash: Both checkers contradicted the no-sweep claim; supported claims show only a fixed 300-dim default, leaving whether it's answered unclear.
- new, opencode-go/minimax-m3: Supported practice shows GISMo only evaluated at 300 dim; the width scaling curve has never been measured.

## 2. Imperial College London — Veselkov Lab / Hyperfoods (Rita et al. 2024, iAnalytica)

https://www.mdpi.com/2504-4990/6/4/131

**Step:** The GISMo baseline/reimplementation step of their ingredient-substitution pipeline: they re-run GISMo as the benchmark ranker against which fine-tuned LLMs (DaVinci, TinyLlama, GPT-3.5) are compared, so the card's width axis targets this baseline ranker's ingredient-encoder width.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] They re-implemented and re-ran GISMo as their benchmark, fixing the ingredient embedding dimension at 300 with two 300-hidden-unit graph convolutional layers, a dropout of 0.25, and 400 epochs with negative sampling. (https://www.mdpi.com/2504-4990/6/4/131)
- VERIFIED [SUPPORTED, SUPPORTED] Their reimplemented GISMo baseline scores Hit@1 34.53 ± 0.10% on the original Recipe1MSubs, and fine-tuned GPT-3.5-Turbo-1106 lifts this to 38.03 ± 0.28%, while TinyLlama-1.1B reaches only 20.93 ± 0.29%. (https://www.mdpi.com/2504-4990/6/4/131)
- VERIFIED [SUPPORTED, SUPPORTED] The work sits inside the Hyperfoods ERC programme (coordinated by Imperial College London), which applies graph-based ML to computationally design personalised nutrition and which funded Rita et al. (https://cordis.europa.eu/project/id/899932)
- VERIFIED [SUPPORTED, SUPPORTED] The re-run GISMo and fine-tuned models (plus the dataset-filtering and fine-tuning scripts) are released on the iAnalytica Bitbucket repository, so the card's width-sweep could be reproduced against their released baseline. (https://www.mdpi.com/2504-4990/6/4/131)

**If the lever:** Their headline comparison would be confounded: they conclude LLMs beat GISMo (38.03 vs 34.53 Hit@1) against a GISMo baseline fixed at 300 dim, so if a wider GISMo keeps climbing that baseline is under-parameterized and they would need to re-benchmark GPT-3.5/TinyLlama against a width-scaled GISMo before attributing the gain to LLM capability; their phytochemically-enriched recipe-generation step would inherit whichever ranker actually wins.

**If not:** Their 300-dim GISMo baseline stands as a fair reference, so the LLM advantage (GPT-3.5-Turbo's 38.03 Hit@1) is a real model effect rather than a capacity artifact; this strengthens their choice of fine-tuned LLMs for generating phytochemically enriched substitutions and lets them skip a wider GISMo.

**Already done:** no [SUPPORTED, SUPPORTED] Rita et al. re-implemented GISMo at a single 300-dim embedding width (averaged over 5 runs) and swept model families (DaVinci/TinyLlama/GPT-3.5), but never swept the GISMo encoder width across 64–512.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 5 | 5, 4, 5 | 1 |
| change | 5 | 5, 4, 5 | 1 |
| new | 5 | 5, 5, 5 | 0 |

- fit, opencode-go/qwen3.8-flash: Card measures GISMo encoder-width Hit@1 effects, exactly the fixed-300 GISMo baseline step Rita et al. compare fine-tuned LLMs against.
- fit, opencode-go/mimo-v2.6-flash: Card measures the baseline ranker's Hit@1 versus width, but its 20.56 reproduction target differs from their 34.53 re-run, needing reconciliation.
- fit, opencode-go/minimax-m3: Card measures their reimplemented GISMo baseline's encoder width scaling on Recipe1MSubs; same system and metric they use.
- change, opencode-go/qwen3.8-flash: A width gain would force re-benchmarking LLMs against scaled GISMo; a plateau would validate the 300-dim comparison.
- change, opencode-go/mimo-v2.6-flash: Either outcome bears on the LLM-vs-GISMo confound, but applying it requires re-benchmarking under their protocol, work the card does not do.
- change, opencode-go/minimax-m3: Lever would confound LLM-vs-GISMo comparison; no-lever validates baseline—either outcome changes their current practice.
- new, opencode-go/qwen3.8-flash: Supported claims say Rita et al. never swept GISMo encoder width, only fixed 300 while comparing LLM families.
- new, opencode-go/mimo-v2.6-flash: Supported claims confirm they swept model families but never the GISMo encoder width 64-512, so the question is unanswered.
- new, opencode-go/minimax-m3: Supported claim confirms no 64-512 width sweep exists; they only swept model families, never encoder width.

## Gaps named by the researcher

- No programme connects this home-recipe ranking metric to industrial formulation or environmental footprint: the card itself notes it 'Shows ranking accuracy on home recipes, not industrial formulations, and never measures actual environmental footprint,' so no industrial ingredient-replacement-for-sustainability programme (e.g., plant-based formulation companies) would change practice purely on a Hit@1 number from Recipe1MSubs.
- The Meta GISMo repository is archived and read-only (Nov 1, 2024), so the primary pipeline the card targets is no longer actively maintained; the result would feed the research literature more than a live product.
- Unresolved discrepancy: Rita et al.'s GISMo reimplementation reports Hit@1 34.53 ± 0.10% on the original Recipe1MSubs, while Meta's published GISMo test Hit@1 is 20.56 ± 0.14% — the card's 'reproduce 20.56 within 2 MRR points' check will have to explain this gap before any width-scaling conclusion transfers between the two programmes.
