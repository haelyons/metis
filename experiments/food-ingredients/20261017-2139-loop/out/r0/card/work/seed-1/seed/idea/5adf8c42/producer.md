# PLAN — FD1: Industrial food ingredient replacement for sustainability

Working file for the producer. The machine-readable record is returned separately.

## Option

- id: FD1
- title: Industrial food ingredient replacement for sustainability
- root question: "Industrial food ingredient replacement for sustainability? Industrial food recipe replacement for sustainability?"
- seed idea from notes; compute_open / sequential not given.

## What to build

A neural **ingredient-substitution ranker** trained on the public **Recipe1MSubs** benchmark
(Fatemi et al. 2023, arXiv:2302.07960, code at github.com/facebookresearch/gismo). Given a
recipe context and a source ingredient, it scores every ingredient in a fixed 6,653-ingredient
vocabulary and ranks them; the correct substitute should rank high. Metric: **MRR and Hit@1/3/10**
on the 10,747-sample test split.

The test varies the ranker's **embedding width** (64 / 128 / 256 / 512), i.e. model capacity,
and measures whether Hit@1 keeps rising. This is the compute lever: a wider encoder costs more
FLOPs and GPU memory per step, so more GPUs buy the larger widths.

Sustainability tie-in: the benchmark's substitutions cover high-footprint ingredients (butter,
egg, milk, cream, beef, pork, chicken, cheese, oil). The final (optional) phase re-evaluates the
best width on the test tuples whose source ingredient is in a curated high-footprint list, which
is exactly the "replace this ingredient for sustainability" use case. Stakes: palm oil alone is
used in 50% of consumer goods (RAN) and food is ~90% of palm-oil use (Riau/PLOS ONE).

## Baseline and anchor

- Baseline to beat (non-neural): LT+Freq, MRR 27.66, Hit@1 18.10 (Table 1 of the GISMo paper).
- Anchor to reproduce first: GISMo test MRR 31.51, Hit@1 20.56 (Table 1), averaged over 5 runs.
  Reproduce with the official gismo code within ±2.0 MRR points before spending on the sweep.

## How to check it is right

1. Downloaded splits match 49,044 / 10,729 / 10,747 samples.
2. Ranking is over the 6,653-ingredient vocabulary, matching GISMo.
3. Anchor mean MRR lands within 2 points of 31.51 (else the pipeline is wrong; stop).
4. Each width averaged over 5 seeds; a real effect exceeds twice the pooled std (GISMo's Hit@1 std is 0.14).
5. Decision rule: Hit@1(width 512) − Hit@1(width 64) ≥ 2.0 points and > 2× pooled std → compute is the lever.

## Compute axis

quantity: substitution-ranker capacity (ingredient-encoder embedding width)
unit: dimension
levels: [64, 128, 256, 512]

held fixed: Recipe1MSubs benchmark + test split; FlavorGraph + 6,653 vocabulary; contrastive
loss, Adam, early stopping on validation MRR; 5 seeds per width; MRR/Hit@k metrics.

## Predictions

- if_lever: Hit@1 rises with width, reaching at least 22% at width 512 (above GISMo's 20.56), and still climbing.
- if_not: Hit@1 plateaus near GISMo's 20.56 at every width; wider models are not the lever.
- expected: if_lever — published LLM fine-tuning lifted Hit@1 on this benchmark family (34.53 → 38.03), so capacity should help.

## Cost (Lambda on-demand, price sheet read 2026-10-17)

- r_a100_1: 1× NVIDIA A100 SXM 40GB, $1.99/GPU/h
- r_a100_4: 4× NVIDIA A100 PCIe 40GB, $1.99/GPU/h (instance $7.96/h)

| line | phase | kind | rate | hours (box) | need | usd |
|---|---|---|---|---|---|---|
| line_anchor | anchor | work | r_a100_1 | 12 | 5 | 23.88 |
| line_sweep | sweep | work | r_a100_4 | 10 | 5 | 79.60 |
| line_storage | setup | storage | — | — | — | 1.00 (5 GiB × fs) |
| line_sustain | sustain | work | r_a100_1 | 2 | 1 | 3.98 (optional) |
| line_llm | stretch | work | r_a100_1 | 24 | 8 | 47.76 (optional) |

Base total = $104.48; with both optionals = $156.22. spend_cap_usd = 1000.

## Restructuring

sequential_part: each training run waits on its own gradient epochs (~30 per run); the runs are independent.
method: none (independent model widths/seeds run side by side; each batch splits across the 4 GPUs).

## Sources (exact sentences relied on)

- src_gismo_sizes (arXiv:2302.07960): "we get 49,044, 10,729 and 10,747 substitution samples for training, validation, and test sets respectively."
- src_gismo_vocab (arXiv:2302.07960): "our ingredient vocabulary contains 6,653 ingredients."
- src_gismo_gismo (arXiv:2302.07960, Table 1): "GISMo (Ours) 31.51±0.10 20.56±0.14 35.89±0.16 54.27±0.19"
- src_gismo_ltfreq (arXiv:2302.07960, Table 1): "LT+Freq 27.66±0.00 18.10±0.00 32.26±0.00 47.50±0.00"
- src_llm (arXiv:2409.08792): "Our approach improved Hit@1 accuracy on ingredient substitution tasks, from the baseline 34.53 ± 0.10% to 38.03 ± 0.28% on the original GISMo dataset, and from 40.24 ± 0.36% to 54.46 ± 0.29% on a refined version of the same dataset."
- src_palm (ran.org/palm_oil_fact_sheet): "Palm oil is a globally traded agricultural commodity that is used in 50 percent of all consumer goods, from lipstick and packaged food to body lotion and biofuels."
- src_foodshare (PMC3728220): "Ninety % of the palm oil is used in food products such as margarine, shortening, and vegetable cooking oil, while the remaining 10% is used by various industries [5]."
