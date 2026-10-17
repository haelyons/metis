# Working notes — FD1 programme scan

## Card summary
- Question: does scaling the ingredient-encoder width of a neural ingredient-substitution ranker improve Hit@1 on Recipe1MSubs?
- Compute axis: substitution-ranker capacity = ingredient-encoder embedding width, 64–512 dim (4 levels).
- Two predicted outcomes:
  1. Lever: Hit@1 rises with width, ≥22% at width 512, above GISMo's 20.56.
  2. Not lever: Hit@1 plateaus near GISMo's 20.56 at every width.
- Check first: reproduce GISMo MRR 31.51 / Hit@1 20.56 within ±2 MRR (mean over 5 seeds).
- Key sources cited in card: src_gismo_sizes, src_gismo_gismo, src_llm.

## Search process
1. Found GISMo paper (arXiv:2302.07960, Fatemi et al., Google Research + Meta AI), official code facebookresearch/gismo.
2. Found Rita et al. 2024 (MDPI Mach. Learn. Knowl. Extr. 6, 2738–2752; "Optimizing Ingredient Substitution Using Large Language Models to Enhance Phytochemical Content in Recipes"), Imperial College London (Veselkov lab).
3. Found Hyperfoods ERC programme (CORDIS 899932) behind Rita et al.
4. Verified GISMo's fixed ingredient-encoder width = 300 (`hidden=300 emb_d=300`) in gismo/README.md.
5. Verified Rita et al. reimplementation at embedding dim 300, 2 layers × 300 hidden units, Hit@1 34.53 → 38.03 (GPT-3.5), TinyLlama 20.93.

## Programme 1 — Meta AI (FAIR): GISMo / Recipe1MSubs (facebookresearch/gismo)
- URL: https://github.com/facebookresearch/gismo
- Card targets: GISMo ingredient encoder (IE), GIN-based, whose embedding width (`emb_d`/`hidden`) is the capacity axis.
- Today: fixed at width 300 (`hidden=300 emb_d=300`), 2 GIN layers, 400 epochs, negative sampling; PyTorch + DGL; 6,653-ingredient FlavorGraph vocab; Recipe1MSubs 49,044 train pairs.
- Published: MRR 31.51, Hit@1 20.56 (test, 5 runs).
- Repo archived read-only Nov 1, 2024.
- Already done: single width 300 only; no width sweep → "partly".

## Programme 2 — Imperial College London (Veselkov lab) / Hyperfoods / iAnalytica (Rita et al. 2024)
- URL: https://www.mdpi.com/2504-4990/6/4/131
- Card targets: the GISMo baseline/reimplementation step of their substitution pipeline (the benchmark vs which LLMs are compared).
- Today: GISMo re-run at embedding dim 300, 2 GCN layers × 300 hidden units, 400 epochs, negative sampling; then fine-tune DaVinci-002 / TinyLlama-1.1B / GPT-3.5-Turbo-1106.
- Numbers: GISMo Hit@1 34.53 ± 0.10% (original), GPT-3.5 38.03 ± 0.28%, TinyLlama 20.93 ± 0.29%.
- Funded partly by Hyperfoods (ERC 899932); code on iAnalytica Bitbucket.
- Already done: single 300-dim width only; no 64–512 sweep → "no".

## Gaps / discrepancies to flag
- Hit@1 discrepancy: Rita's GISMo reimplementation = 34.53 vs Meta's published = 20.56 for the same benchmark. Card's reproduction check must resolve this.
- Meta repo archived: result feeds literature, not a live product.
- No industrial sustainability programme changes practice on Hit@1 alone (card's "would not show").
