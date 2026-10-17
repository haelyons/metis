# Result

Picks 1 · PASS 1 · on-goal cards U4 0 · U3 1 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) Battery crystal discovery | PASS 1/2 | seed | if_lever | 5 | — → 5 | — → 3 | 3 | — | — → 2 | — | $576 at p_validate · plan $576 · 5 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**B1 · Battery crystal discovery.** seed pick · compute tested: yes · plan expects: the lever · PASS

**Question.** Can a crystal foundation model fine-tuned on a transport proxy generate Li-ion solid electrolytes with higher conductivity than unconditioned generation or database screening?

**What is known.** Ferrogen (NeurIPS 2026) fine-tuned MatterGen on a polarization proxy with ML labels, achieving ~80x search efficiency over exhaustive screening; it never targeted ionic conductivity. No published result fine-tunes a crystal foundation model to generate battery materials conditioned on a transport property like ionic conductivity.

**Hypothesis.** Conditioning MatterGen's adapter on predicted ionic conductivity gives low-barrier candidates at higher hit rate than screening; transport labels are scarce but learnable.

**Restructuring.** The fine-tune, generate, screen, validate loop, ~3 rounds; each diffusion sample's ~1,000 sequential denoising timesteps. None: the loop's costly steps (generating, screening, NEB-validating thousands of candidates) are embarrassingly parallel; the plan splits each across GPUs, no reordering.

**If compute is the lever.** Scaling candidates to 100,000 makes the conditioned generator's hit-rate advantage over both baselines significant; at 1,000 it is within noise.

**If not.** Scaling candidates does not separate conditioned from baseline hit rates; the gap stays within seed noise at every level, so fine-tuning adds nothing.

**Test.** Fine-tune the adapter of the open-source MatterGen crystal model on predicted log conductivity; generate and screen 1k-100k candidates in each arm; NEB-validate the top ten; compare hit rate against unconditioned generation and screening of the ICSD database (about $576).

*Compute axis.* Generated candidate crystal structures screened per arm: 1,000–100,000 candidates, 3 levels. Closest prior: not on this axis.

**Check first.** Reproduce MatterGen's 38.57% S.U.N. and 0.021 Angstrom RMSD on 1,024 samples; reproduce the npj predictor's 0.85 log10 sigma MAE. Tolerance: S.U.N. within +/-3 percentage points; RMSD <= 0.1 Angstrom; predictor MAE within +/-0.1 log10 sigma..

**Would not show.** Shows predicted-conductivity and migration-barrier rankings, not measured sigma; Li conductors only; no synthesis, cycle-life, or interface data.

*Cost.* Plans $575.76 of the $1,000 budget over 174 machine-hours, leaving $424.24. Main guess: DFT-NEB cost per material [g], measured after $575.76 of spend; the budget is reached if it is 1.0× higher. 7 cost flags in the block.

**Judges.** Dramaturg: PASS 1/2. Decides at: $576 at p_validate · plan $576 · 5 GUESS (critic: Decision needs 100k hit rates and top-10 CHGNet-NEB barriers, both available only after validation).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-17 · filesystem $0.20/GiB-month [q]
Spend      p_data  Fetch mattergen_base checkpoint and npj dataset; map 403 compositions to ICSD/MP structures; anchor the S.U.N. rate.  1x NVIDIA A100 SXM 40GB $1.99/h  2 h  $23.98  L_anchor need 2 h in a 2 h box
           p_predictor  Train composition conductivity regressor/classifier; anchor held-out MAE.  1x NVIDIA A10 24GB $1.29/h  10 h  $12.90  L_predictor need 6 h in a 10 h box
           p_finetune  Fine-tune MatterGen adapter on predicted log10 sigma (time-boxed).  1x NVIDIA A100 SXM 40GB $1.99/h  24 h  $47.76  L_finetune need 4 h in a 24 h box
           p_generate  Generate and screen arms A/B at 1k/10k/100k and arm C; measure hit rates.  8x NVIDIA Tesla V100 16GB 8×$0.79=$6.32/h  50 h  $316  L_generate need 400 h in a 50 h box
           p_validate  CHGNet-NEB on top-50, then DFT-NEB on top-10.  1x NVIDIA A100 SXM 40GB $1.99/h  88 h  $175.12  L_chgnet need 5 h in a 8 h box  L_dft need 80 h in a 80 h box
           p_generate  Stretch: +200k candidates (100k/arm) if the 100k gap is promising but under 2x  8x NVIDIA Tesla V100 16GB 8×$0.79=$6.32/h  50 h [=]  $316  time box; need 400 h (margin 0.13×)  optional
           Planned $575.76 · unallocated $424.24 · with options $891.76 · cap $1,000
Rests on   DFT-NEB cost per material 8 GPU-hours per material [g] rests on: VASP CI-NEB, ~5 images on a ~100-atom supercell, ~100 ionic steps per image, on one A100 · measured in p_validate ($575.76 spent by then) · budget reached at 8 (1.0× higher)
           CHGNet-NEB cost per material 0.1 GPU-hours per material [g] rests on: ML-potential NEB (CHGNet) is orders of magnitude cheaper than DFT-NEB, per s_chgnet_ht · measured in p_validate ($575.76 spent by then) · budget reached at 0.1 (1.0× higher) · box overflows at 1.6×
           Fine-tune GPU work 4 GPU-hours [g] rests on: adapter-only fine-tune on ~400 labels; one 600K-sample epoch is 0.8 GPU-hours, so 500 epochs on 400 labels is <1 GPU-hour plus restart/checkpoint overhead · measured in p_finetune ($84.64 spent by then) · budget reached at 4 (1.0× higher) · box overflows at 6.0×
           Expected held-out predictor MAE 0.9 log10 sigma [g] rests on: npj reports 0.85 MAE on the same 403 compositions · measured in p_predictor ($36.88 spent by then) · gate Expected held-out predictor MAE ≤ 1 in p_predictor (now 0.9, passes; uncut plan at it $2,787.76), else fall back to classifier-only conditioning on P(log10 sigma >= -4) as the label · budget reached at 0.9 (1.0× higher)
           gate Expected median CHGNet-NEB barrier of top candidates ≤ 0.5 in p_validate (now 0.4, passes; uncut plan at it $2,787.76), else skip DFT-NEB and report CHGNet-NEB only (conditioning failed to yield low-barrier candidates)
           +1 more: Expected median CHGNet-NEB barrier of top candidates
Scenarios  2x slower V100 sampling and 12 GPU-hours per DFT-NEB → $5,395.36 (over budget)
Buys       Total generated candidates: 200,000 [=] · 2x slower V100 sampling and 12 GPU-hours per DFT-NEB: 200,000
           DFT-NEB validated candidates: 10 [d] · 2x slower V100 sampling and 12 GPU-hours per DFT-NEB: 10
           CHGNet-NEB validated candidates: 50 [d] · 2x slower V100 sampling and 12 GPU-hours per DFT-NEB: 50
Flags      error (quote) at numbers.mattergen_params.quote: 46.8 does not appear in the quote "MatterGen contains 46.8M parameters"; a value transformed from the page belongs in a DERIVED number
           error (quote) at numbers.sample_v100_h_per_1k.quote: 2 does not appear in the quote "Sampling 1,000 structures takes around two hours using a single NVIDIA V100 GPU"; a value transformed from the page belongs in a DERIVED number
           error (quote) at numbers.cond_threshold.quote: -4 does not appear in the quote "We develop supervised regression and classification models to predict the lithium ion conductivity and assess whether a material will possess an ionic conductivity log10(sigma) >= 4 at room temperature, where the conductivity is reported in units of S cm-1."; a value transformed from the page belongs in a DERIVED number
           uncut plan at the p_predictor gate threshold costs $2,787.76, over budget; the plan relies on: fall back to classifier-only conditioning on P(log10 sigma >= -4) as the label
           uncut plan at the p_validate gate threshold costs $2,787.76, over budget; the plan relies on: skip DFT-NEB and report CHGNet-NEB only (conditioning failed to yield low-barrier candidates)
           thin headroom: the budget is reached if DFT-NEB cost per material is 1.0× higher
           thin headroom: the budget is reached if CHGNet-NEB cost per material is 1.0× higher
           thin headroom: the budget is reached if Fine-tune GPU work is 1.0× higher
           thin headroom: the budget is reached if Expected held-out predictor MAE is 1.0× higher
           thin headroom: the budget is reached if Expected median CHGNet-NEB barrier of top candidates is 1.0× higher
Full scale Generate 1M candidates (2 arms x 500k) and DFT-NEB validate 50: $2,396 = 2.4× budget = 0.012× Total generated candidates
           AIMD ionic-conductivity validation of 20 candidates (assumed ~20x NEB cost each): $6,388 = 6.39× budget = 639× DFT-NEB validated candidates
Outside    Researcher time (structure mapping, glue code, curation): 40 hours · Expert literature check of labeled conductivities: 20 hours
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
epoch_gpu_h = epoch_min_8a100 / 60 * 8 = 6 / 60 * 8 = 0.8 GPU-hours
n_cand_total = n_arms_gen * cand_level_max = 2 * 100000 = 200000 candidates
gen_gpu_h = n_cand_total / 1000 * sample_v100_h_per_1k = 200000 / 1000 * 2 = 400 V100 GPU-hours
dft_gpu_h = n_validate_dft * dft_neb_gpu_h_per = 10 * 8 = 80 GPU-hours
chgnet_gpu_h = n_validate_chgnet * chgnet_neb_gpu_h_per = 50 * 0.1 = 5 GPU-hours
L_storage.usd = fs_gib * fs_usd_gib_month = 100 * 0.2 = 20 usd
L_finetune.need = finetune_need_gpu_h = 4 = 4 h
L_generate.hours = gen_gpu_h / 8 = 400 / 8 = 50 h
L_generate.need = gen_gpu_h = 400 = 400 h
L_chgnet.need = chgnet_gpu_h = 5 = 5 h
L_dft.hours = dft_gpu_h = 80 = 80 h
L_dft.need = dft_gpu_h = 80 = 80 h
L_gen_extra.hours = gen_gpu_h / 8 = 400 / 8 = 50 h
L_gen_extra.need = gen_gpu_h = 400 = 400 h
f1 = (1000000/1000*2*0.79) + (50*8*1.99) + (100*fs_usd_gib_month) = 1000000 / 1000 * 2 * 0.79 + 50 * 8 * 1.99 + 100 * 0.2 = 2396 usd
f2 = (20*8*20*1.99) + (100*fs_usd_gib_month) = 20 * 8 * 20 * 1.99 + 100 * 0.2 = 6388 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:sequential_part` PARTIAL · page: "" · note: '~3 rounds' of the loop is the plan's own design (needs no source). The claim 'each diffusion sample's ~1,000 sequential denoising timesteps' is a specific factual claim about MatterGen's sampler with no cited source and is not stated on the fetched pages.
- sample 1 · `card:left_open` UNSUPPORTED · page: "" · note: Factual claim about the literature (no published result does X) with no source cited; cannot be verified from the fetched pages.
- sample 1 · `card:anchor` PARTIAL · page: "MatterGen achieves 38.57 % S.U.N. rate among generated structures, and the average RMSD of its samples is 0.021 Angstrom." · note: S.U.N. 38.57%, RMSD 0.021 Angstrom, and the 1,024-sample basis are supported by MODEL_CARD.md ('among 1,024 generated samples'); value 38.57 matches. The 'npj predictor's 0.85 log10 sigma MAE' claim has no cited source.
- sample 2 · `card:sequential_part` UNSUPPORTED · page: "Sampling 1,000 structures takes around two hours using a single NVIDIA V100 GPU (MODEL_CARD.md)." · note: The '~3 rounds' is a plan decision needing no source. But the claim that MatterGen's diffusion sampler has ~1,000 sequential denoising timesteps is a factual claim about the model, and the item cites no source; the MODEL_CARD.md page states nothing about the number of denoising timesteps, so it is unsupported. · page value 1000
- sample 2 · `card:test_summary` PARTIAL · page: "Sampling 1,000 structures takes around two hours using a single NVIDIA V100 GPU (MODEL_CARD.md)." · note: The workflow steps are the plan's own and need no source; the MODEL_CARD.md page supports that MatterGen is diffusion-based, fine-tunable for property-conditioned generation, evaluated on 1,024 generated samples. But the '(about $576)' cost input is a factual/cost claim with no cited source, so that number is unsupported.
- sample 2 · `card:left_open` UNSUPPORTED · page: "..." · note: This is a negative claim about the state of published literature (no published result fine-tunes a crystal foundation model conditioned on a transport property) with no cited source. The Ferrogen poster shows a close published precedent on a different transport-adjacent property, but establishing the absence of any such published result requires a source the item does not cite.
- sample 2 · `card:anchor` PARTIAL · page: "MatterGen achieves 38.57 % S.U.N. rate among generated structures, and the average RMSD of its samples is 0.021 Angstrom. ... The percentage of stable, novel, and unique (S.U.N.) structures among 1,024 generated samples." · note: The cited MODEL_CARD.md page supports 38.57 % S.U.N. (matching the value 38.57), 0.021 Angstrom RMSD, and the 1,024-sample setting verbatim. However, 'reproduce the npj predictor's 0.85 log10 sigma MAE' is a factual claim about a published predictor with no cited source, so that part is unsupported.

**Critic.**
- stakes 3 · `card:limits` "Shows predicted-conductivity and migration-barrier rankings, not measured sigma; Li conductors only; no synthesis, cycle-life, or interface data." · The choice depends on measured conductivity and synthesis; the test only checks model-predicted rankings.
- lever 5 · `card:if_lever` "Scaling candidates to 100,000 makes the conditioned generator's hit-rate advantage over both baselines significant; at 1,000 it is within noise." · 100× compute span, seeds/predictor/checkpoint held fixed, and the ≥2× gap exceeds the stated bootstrap noise rule; quantity is the asked hit rate.
- verifiable 3 · `card:limits` "Shows predicted-conductivity and migration-barrier rankings, not measured sigma; Li conductors only; no synthesis, cycle-life, or interface data." · Hit labels come from the conductivity predictor and NEB simulations, with published anchors but no exact measured truth.
- open 5 · `card:left_open` "No published result fine-tunes a crystal foundation model to generate battery materials conditioned on a transport property like ionic conductivity." · Ferrogen conditions on ferroelectric polarization, not battery transport; the plan states this gap.
- reshape 2 · `card:method` "None: the loop's costly steps (generating, screening, NEB-validating thousands of candidates) are embarrassingly parallel; the plan splits each across GPUs, no reordering." · It only splits independent candidates across GPUs within each step; the sequential generate-screen-validate chain remains.
- baseline NA · `card:method` "None: the loop's costly steps (generating, screening, NEB-validating thousands of candidates) are embarrassingly parallel; the plan splits each across GPUs, no reordering." · Criterion allows NA when restructuring.method is none; card:method states no restructuring, all steps run in original order.

**Producer says (not judged).** expected if_lever (Conditioned generation has repeatedly beaten screening (MatterGen, Ferrogen's 80x), and the conductivity proxy is learnable (MCC 0.63).); compute_tested yes (The test varies the number of generated candidates (the quantity parallel GPUs buy: 1k/10k/100k) and measures whether the conditioned-vs-baseline hit-rate gap emerges above noise; the fine-tuning method is held fixed across levels.); decides no; searched yes.

**Annotations.**
- quote at numbers.mattergen_params.quote: 46.8 does not appear in the quote "MatterGen contains 46.8M parameters"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.sample_v100_h_per_1k.quote: 2 does not appear in the quote "Sampling 1,000 structures takes around two hours using a single NVIDIA V100 GPU"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.cond_threshold.quote: -4 does not appear in the quote "We develop supervised regression and classification models to predict the lithium ion conductivity and assess whether a material will possess an ionic conductivity log10(sigma) >= 4 at room temperature, where the conductivity is reported in units of S cm-1."; a value transformed from the page belongs in a DERIVED number
- uncut plan at the p_predictor gate threshold costs $2,787.76, over budget; the plan relies on: fall back to classifier-only conditioning on P(log10 sigma >= -4) as the label
- uncut plan at the p_validate gate threshold costs $2,787.76, over budget; the plan relies on: skip DFT-NEB and report CHGNet-NEB only (conditioning failed to yield low-barrier candidates)
- thin headroom: the budget is reached if DFT-NEB cost per material is 1.0× higher
- thin headroom: the budget is reached if CHGNet-NEB cost per material is 1.0× higher
- thin headroom: the budget is reached if Fine-tune GPU work is 1.0× higher
- thin headroom: the budget is reached if Expected held-out predictor MAE is 1.0× higher
- thin headroom: the budget is reached if Expected median CHGNet-NEB barrier of top candidates is 1.0× higher
- restructuring.condition is empty
- restructuring.condition_phase is empty
- restructuring.baseline_sequential is empty
- restructuring.baseline_copies is empty
- question: a sentence of 23 words
- hypothesis: a sentence of 22 words
- restructuring.method: a sentence of 22 words
- predictions.if_not: a sentence of 23 words
- test_summary: a sentence of 28 words
- novelty.closest_prior: a sentence of 24 words
- test_summary: rewritten by the field repair
- card field test_summary still fails: dollar figure
- dramaturg findings failed G-find after a resample; decided as returned
- dramaturg-2 findings failed G-find after a resample; decided as returned
- critique failed G-crit after a resample; shown as returned

**Root question (null).** Battery crystal discovery? Crystal foundation models: there's hella, for battery generation, transport properties are different.

**Producer file.** [producer.md](/home/hal/dev/interp/latent_open/runs/loop/battery/20261017-213943/r0/card/work/seed-1/seed/idea/0bdd3c5c/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: quote at numbers.mattergen_params.quote: 46.8 does not appear in the quote "MatterGen contains 46.8M parameters"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: quote at numbers.sample_v100_h_per_1k.quote: 2 does not appear in the quote "Sampling 1,000 structures takes around two hours using a single NVIDIA V100 GPU"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: quote at numbers.cond_threshold.quote: -4 does not appear in the quote "We develop supervised regression and classification models to predict the lithium ion conductivity and assess whether a material will possess an ionic conductivity log10(sigma) >= 4 at room temperature, where the conductivity is reported in units of S cm-1."; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: uncut plan at the p_predictor gate threshold costs $2,787.76, over budget; the plan relies on: fall back to classifier-only conditioning on P(log10 sigma >= -4) as the label
seed:idea:seed: uncut plan at the p_validate gate threshold costs $2,787.76, over budget; the plan relies on: skip DFT-NEB and report CHGNet-NEB only (conditioning failed to yield low-barrier candidates)
seed:idea:seed: thin headroom: the budget is reached if DFT-NEB cost per material is 1.0× higher
seed:idea:seed: thin headroom: the budget is reached if CHGNet-NEB cost per material is 1.0× higher
seed:idea:seed: thin headroom: the budget is reached if Fine-tune GPU work is 1.0× higher
seed:idea:seed: thin headroom: the budget is reached if Expected held-out predictor MAE is 1.0× higher
seed:idea:seed: thin headroom: the budget is reached if Expected median CHGNet-NEB barrier of top candidates is 1.0× higher
seed:idea:seed: restructuring.condition is empty
seed:idea:seed: restructuring.condition_phase is empty
seed:idea:seed: restructuring.baseline_sequential is empty
seed:idea:seed: restructuring.baseline_copies is empty
seed:idea:seed: question: a sentence of 23 words
seed:idea:seed: hypothesis: a sentence of 22 words
seed:idea:seed: restructuring.method: a sentence of 22 words
seed:idea:seed: predictions.if_not: a sentence of 23 words
seed:idea:seed: test_summary: a sentence of 28 words
seed:idea:seed: novelty.closest_prior: a sentence of 24 words
seed:idea:seed: card fields failing: test_summary (dollar figure)
seed:idea:seed: test_summary: rewritten by the field repair
seed:idea:seed: card field test_summary still fails: dollar figure
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:hypothesis; degenerate: card:sequential_part; degenerate: card:method; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:limits
seed:idea:seed: critic: baseline: value "NA"
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:hypothesis; degenerate: card:sequential_part; degenerate: card:method; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg-2: card:limits: 0 findings
seed:idea:seed: dramaturg-2 (resample): card:limits: 0 findings; degenerate: card:if_not
seed:idea:seed: dramaturg-2 findings failed G-find after a resample; decided as returned
seed:idea:seed: critic (resample): baseline: value "NA"
seed:idea:seed: critique failed G-crit after a resample; shown as returned
```