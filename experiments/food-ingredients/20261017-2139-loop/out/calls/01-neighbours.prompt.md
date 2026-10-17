Here is a research idea, the card a planner wrote for it, and a check of which existing research or industrial programmes would use its result, with the gaps that check found.

Root question: Industrial food ingredient replacement for sustainability? Industrial food recipe replacement for sustainability?
Idea: {"title":"Industrial food ingredient replacement for sustainability","text":"Industrial food ingredient replacement for sustainability? Industrial food recipe replacement for sustainability? (from the user's notes; no further detail given)","root_link":"is the root question","compute_open":"not given (seed idea from notes)","sequential":"not given (seed idea from notes)"}
Card:
<a id="card-seed-idea-1"></a>**FD1 · Industrial food ingredient replacement for sustainability.** seed pick · compute tested: yes · plan expects: the lever · REJECT

**Question.** Does increasing the capacity of a neural ingredient-substitution model measurably improve its ranking of sustainable replacements, measured as Hit@1 on Recipe1MSubs [src_gismo_sizes]?

**What is known.** Rita 2024 fine-tuned GPT-3.5 and TinyLlama on Recipe1MSubs, lifting Hit@1 from 34.53 to 38.03; no capacity sweep within one protocol exists [src_llm]. Whether ranking quality keeps rising with model capacity inside one fixed protocol on Recipe1MSubs is unmeasured; the only scaling evidence is cross-protocol.

**Hypothesis.** More capacity in a substitution ranker improves substitution ranking because larger encoders capture finer ingredient context, as LLM results suggest [src_llm].

**If compute is the lever.** Hit@1 rises with width, reaching at least 22 percent at width 512, above GISMo's 20.56, and still climbing.

**If not.** Hit@1 plateaus near GISMo's 20.56 at every width; extra capacity adds nothing, so wider models are not the lever.

**Test.** Reproduce GISMo's Recipe1MSubs result, then train the ranker at four widths 64, 128, 256, 512 with five seeds each on four GPUs; if Hit@1 climbs past the 20.56 baseline with width, compute is the lever.

*Compute axis.* Substitution-ranker capacity (ingredient-encoder embedding width): 64–512 dimension, 4 levels. Closest prior: not on this axis.

*Restructuring.* none.

**Check first.** Reproduce GISMo's published test-set MRR of 31.51 and Hit@1 of 20.56 using the official code, within 2 MRR points [src_gismo_gismo]. Tolerance: plus or minus 2.0 MRR points (mean over 5 seeds).

**Would not show.** Shows ranking accuracy on home recipes, not industrial formulations, and never measures actual environmental footprint or sensory quality of the substitute.

*Cost.* Plans $104.48 of the $1,000 budget over 22 machine-hours, leaving $895.52. Main guess: wall-clock per training run on one A100 40GB [g], measured after $24.88 of spend; the budget is reached if it is 20× higher.

Card verdict: REJECT (3 blocking)
Programme check: [{"name":"Meta AI (FAIR) — GISMo / Recipe1MSubs (facebookresearch/gismo)","step":"The GISMo ingredient encoder (IE): the GIN-based node encoder whose embedding width (the `emb_d`/`hidden` dimensions) is exactly the capacity axis the card sweeps (64–512) before the ingredient-substitution decoder ranks candidate substitutes.","sum":15},{"name":"Imperial College London — Veselkov Lab / Hyperfoods (Rita et al. 2024, iAnalytica)","step":"The GISMo baseline/reimplementation step of their ingredient-substitution pipeline: they re-run GISMo as the benchmark ranker against which fine-tuned LLMs (DaVinci, TinyLlama, GPT-3.5) are compared, so the card's width axis targets this baseline ranker's ingredient-encoder width.","sum":15}]
Gaps found: ["No programme connects this home-recipe ranking metric to industrial formulation or environmental footprint: the card itself notes it 'Shows ranking accuracy on home recipes, not industrial formulations, and never measures actual environmental footprint,' so no industrial ingredient-replacement-for-sustainability programme (e.g., plant-based formulation companies) would change practice purely on a Hit@1 number from Recipe1MSubs.","The Meta GISMo repository is archived and read-only (Nov 1, 2024), so the primary pipeline the card targets is no longer actively maintained; the result would feed the research literature more than a live product.","Unresolved discrepancy: Rita et al.'s GISMo reimplementation reports Hit@1 34.53 ± 0.10% on the original Recipe1MSubs, while Meta's published GISMo test Hit@1 is 20.56 ± 0.14% — the card's 'reproduce 20.56 within 2 MRR points' check will have to explain this gap before any width-scaling conclusion transfers between the two programmes."]

Propose three close variants of the idea. Each changes one thing (the system studied, the quantity more compute buys, the comparison it is judged against, or the programme it is aimed at) so that its result would matter more to a named programme or close a named gap. Keep the rest of the idea. Name only systems, tools and programmes that appear above or that you are sure exist. Decide only from the text above; do not use tools.
Return only JSON: {"variants": [{"id": "V1", "title": "", "text": "the idea in three to five sentences, in the form of the original", "root_link": "", "compute_open": "", "sequential": "", "changes": "what differs from the original and which gap or programme it answers"}]}