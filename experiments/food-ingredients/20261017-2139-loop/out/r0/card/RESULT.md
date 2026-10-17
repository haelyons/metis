# Result

Picks 1 · PASS 0 · on-goal cards U4 0 · U3 0 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) Industrial food ingredient replacement for sustainability | REJECT (3 blocking) | seed | if_lever | 3 | — → 5 | — → 3 | 5 | — | — → 1 | — | $104 at sweep · plan $104 · 2 GUESS |

## Frontier (listed, not produced)

None.

## Cards

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

**Judges.** Dramaturg: REJECT (3 blocking). Decides at: $104 at sweep · plan $104 · 2 GUESS (critic: Sweep yields Hit@1 at widths 64 and 512 with seeds, allowing the decision rule; anchor only reproduces baseline).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-17 · filesystem $0.20/GiB-month [q]
Spend      anchor  Reproduce GISMo: 5 training runs on one A100  1x NVIDIA A100 SXM 40GB $1.99/h  12 h [d]  $23.88  time box; need 5 h (margin 2.40×)
           sweep  Capacity sweep: 20 runs across 4 A100s  4x NVIDIA A100 PCIe 40GB 4×$1.99=$7.96/h  10 h [d]  $79.60  time box; need 5 h (margin 2.00×)
           setup  Dataset and checkpoint filesystem, 5 GiB for a month  [=]  $1
           sustain  Evaluate the best width on the high-footprint subset  1x NVIDIA A100 SXM 40GB $1.99/h  2 h [d]  $3.98  time box; need 1 h (margin 2.00×)  optional
           stretch  Optional stretch: fine-tune a small pretrained transformer encoder  1x NVIDIA A100 SXM 40GB $1.99/h  24 h [d]  $47.76  time box; need 8 h (margin 3.00×)  optional
           Planned $104.48 · unallocated $895.52 · with options $156.22 · cap $1,000
Rests on   wall-clock per training run on one A100 40GB 1 hours [g] rests on: one GISMo run trains 49,044 tuples over a 6,653-node graph with two GIN layers and a contrastive loss; small-GNN runs of this size typically finish in under an hour on an A100 · measured in anchor ($24.88 spent by then) · gate wall-clock per training run on one A100 40GB ≤ 2 in anchor (now 1, passes; uncut plan at it $104.48), else halve the sweep to widths 64 and 128 with 3 seeds each and re-check the budget · budget reached at 20.1 (20× higher) · box overflows at 2.0×
           high-footprint source ingredients in the test split 2,000 samples [g] rests on: high-impact ingredients (butter, egg, milk, cream, beef, pork, chicken, cheese, oil) are common in home recipes, so roughly 15 to 25 percent of the 10,747 test tuples likely have one as the source · measured in setup ($1 spent by then) · gate high-footprint source ingredients in the test split ≥ 100 in sustain (now 2,000, passes; uncut plan at it $104.48), else skip the sustainability evaluation · budget not reached within 1000×
Scenarios  pessimistic: each training run takes 2 hours → $104.48 · optimistic: each training run takes 0.5 hours → $104.48
Buys       sweep training runs: 20 [=] · pessimistic: each training run takes 2 hours: 20 · optimistic: each training run takes 0.5 hours: 20
           test substitution samples: 10,700 [c] · pessimistic: each training run takes 2 hours: 10,700 · optimistic: each training run takes 0.5 hours: 10,700
           high-footprint source ingredients in the test split: 2,000 [g] · pessimistic: each training run takes 2 hours: 2,000 · optimistic: each training run takes 0.5 hours: 2,000
Flags      none
Full scale Fine-tune a 7B LLM on Recipe1MSubs plus Recipe1M instructions for substitution ranking: $6,000 = 6× budget = 0.122× training substitution samples
           Rank substitutes across all 1,029,720 Recipe1M recipes, not just the benchmark tuples: $2,000 = 2× budget = 0.0408× training substitution samples
Outside    researcher time to wire the benchmark, run seeds, and read results: 30 hours · free 4-core CPU host for dataset download and checks: 2 hours
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
n_runs_sweep = n_widths * n_seeds = 4 * 5 = 20 runs
anchor_need_h = n_seeds * t_run_h = 5 * 1 = 5 hours
sweep_wall_h = ceil(n_runs_sweep / n_gpus_sweep) * t_run_h = ceil(20 / 4) * 1 = 5 hours
line_anchor.need = anchor_need_h = 5 = 5 h
line_sweep.need = sweep_wall_h = 5 = 5 h
line_storage.usd = 5 * fs_usd_gib_month = 5 * 0.2 = 1 usd
fs_llm = 6 * budget_usd = 6 * 1000 = 6000 usd
fs_all = 2 * budget_usd = 2 * 1000 = 2000 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:hypothesis` PARTIAL · page: "Our approach improved Hit@1 accuracy on ingredient substitution tasks, from the baseline 34.53 ± 0.10% to 38.03 ± 0.28% on the original GISMo dataset, and from 40.24 ± 0.36% to 54.46 ± 0.29% on a refined version of the same dataset." · note: The quote supports the direction (a larger/LLM model raises Hit@1 vs baseline), but the specific mechanism 'larger encoders capture finer ingredient context' is not stated anywhere on the page, so that part of the hypothesis is unsupported.
- sample 1 · `card:if_lever` UNSUPPORTED · page: "GISMo (Ours) 31.51±0.10 20.56±0.14 35.89±0.16 54.27±0.19" · note: The prediction (Hit@1 rising with width) needs no source, but it embeds a factual claim 'GISMo's Hit@1 = 20.56' with no cited source in this item. GISMo Table 1 does report 20.56±0.14, so the number is accurate, but the item cites no source for it.
- sample 1 · `card:if_not` UNSUPPORTED · page: "GISMo (Ours) 31.51±0.10 20.56±0.14 35.89±0.16 54.27±0.19" · note: The prediction (plateau near GISMo's baseline) needs no source, but it embeds a factual claim 'GISMo's Hit@1 = 20.56' with no cited source. Table 1 does state 20.56±0.14, but this item cites no source.
- sample 1 · `card:test_summary` UNSUPPORTED · page: "GISMo (Ours) 31.51±0.10 20.56±0.14 35.89±0.16 54.27±0.19" · note: The method/plan (reproduce, train at four widths/seeds) is what the plan will build/measure and needs no source, but it references 'GISMo's Recipe1MSubs result' and 'the 20.56 baseline' as facts with no cited source. The 20.56 number does appear in Table 1.
- sample 1 · `card:left_open` UNSUPPORTED · page: "" · note: 'The only scaling evidence is cross-protocol' is a factual claim about the state of the literature with no cited source; it cannot be verified from the fetched pages (the Rita abstract shows one cross-protocol LLM improvement, and neither page demonstrates a within-protocol capacity sweep, but 'only' cannot be established from these two pages).
- sample 1 · `card:limits` UNSUPPORTED · page: "" · note: The factual claims ('home recipes, not industrial formulations' and 'never measures environmental footprint or sensory quality') have no cited source in this item. They are consistent with the GISMo paper (Recipe1M home recipes; MRR/Hit@k ranking metrics only), but the item cites no source.
- sample 2 · `card:hypothesis` PARTIAL · page: "Our approach improved Hit@1 accuracy on ingredient substitution tasks, from the baseline 34.53 plus-minus 0.10% to 38.03 plus-minus 0.28% on the original GISMo dataset, and from 40.24 plus-minus 0.36% to 54.46 plus-minus 0.29% on a refined version of the same dataset." · note: Quote appears in the abstract (± rendered as 'plus-minus') and shows fine-tuned LLMs improved Hit@1 on the GISMo dataset, which is consistent with 'as LLM results suggest'. However, the page attributes the gain to the fine-tuned LLM approach for optimizing phytochemical content (GPT-3.5 over the GISMo baseline), never to model capacity, and the paper's other fine-tuned LLMs (DaVinci-002 20.09±0.31%, TinyLlama-1.1B 20.93±0.29% on the original dataset) underperformed the 34.53 baseline, so 'larger encoders capture finer ingredient context' is the plan's causal interpretation not carried by the source.
- sample 2 · `card:closest_prior` PARTIAL · page: "Our approach improved Hit@1 accuracy on ingredient substitution tasks, from the baseline 34.53 plus-minus 0.10% to 38.03 plus-minus 0.28% on the original GISMo dataset, and from 40.24 plus-minus 0.36% to 54.46 plus-minus 0.29% on a refined version of the same dataset." · note: Quote appears (± rendered as 'plus-minus') and confirms Rita 2024 (arXiv 2409.08792, 13 Sep 2024) fine-tuned GPT-3.5 and TinyLlama and improved Hit@1 from 34.53 to 38.03 on the original GISMo dataset, which the paper's results table labels 'Recipe1MSubs Dataset'. The clause 'no capacity sweep within one protocol exists' is an absence claim the cited abstract never states or evidences, so that part is unverified; the paper's model comparison across sizes is attributed to the fine-tuning approach, not presented as a capacity sweep.

**Critic.**
- stakes 3 · `card:limits` "Shows ranking accuracy on home recipes, not industrial formulations, and never measures actual environmental footprint or sensory quality of the substitute." · Outcomes only affect scaling a recipe ranker; sustainability choice depends on unmeasured footprint and sensory validation.
- lever 3 · `plan:compute_axis.levels` "[64,128,256,512]" · Width 64 to 512 spans 8x, not 10x; data held fixed and predicted gap exceeds noise, but one condition fails.
- verifiable 5 · `card:anchor` "Reproduce GISMo's published test-set MRR of 31.51 and Hit@1 of 20.56 using the official code, within 2 MRR points [src_gismo_gismo]. Tolerance: plus or minus 2.0 MRR points (mean over 5 seeds)." · Anchor reproduces GISMo Hit@1/MRR within tolerance; Hit@1 scores against Recipe1MSubs targets independent of the trained ranker.
- open 5 · `card:closest_prior` "Rita 2024 fine-tuned GPT-3.5 and TinyLlama on Recipe1MSubs, lifting Hit@1 from 34.53 to 38.03; no capacity sweep within one protocol exists [src_llm]." · Prior reports cross-protocol LLM Hit@1, not a one-protocol width sweep; card explicitly states the unmeasured range gap.
- reshape 1 · `card:sequential_part` "Each training run waits on its own gradient epochs, roughly 30 per run; the runs themselves are independent." · Runs are independent copies batched across GPUs; method is none, so no step-after-step dependency is removed.
- baseline NA · `card:method` "none" · restructuring.method is none, so baseline criterion not applicable.

**Producer says (not judged).** expected if_lever (Published LLM fine-tuning lifted Hit@1 on this benchmark family from 34.53 to 38.03, so larger encoders should lift it here too [src_llm].); compute_tested yes (The test varies the ranker's embedding width, which sets model size and per-step FLOPs; wider models need more GPU memory and compute, so more GPUs buy the larger widths.); decides no; searched yes.

**Annotations.**
- question: a sentence of 22 words
- hypothesis: a sentence of 21 words
- test_summary: a sentence of 35 words
- novelty.closest_prior: a sentence of 22 words
- novelty.left_open: a sentence of 22 words
- limits: a sentence of 21 words

**Root question (null).** Industrial food ingredient replacement for sustainability? Industrial food recipe replacement for sustainability?

**Producer file.** [producer.md](/home/hal/dev/interp/latent_open/runs/loop/food/20261017-213943/r0/card/work/seed-1/seed/idea/5adf8c42/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: question: a sentence of 22 words
seed:idea:seed: hypothesis: a sentence of 21 words
seed:idea:seed: test_summary: a sentence of 35 words
seed:idea:seed: novelty.closest_prior: a sentence of 22 words
seed:idea:seed: novelty.left_open: a sentence of 22 words
seed:idea:seed: limits: a sentence of 21 words
```