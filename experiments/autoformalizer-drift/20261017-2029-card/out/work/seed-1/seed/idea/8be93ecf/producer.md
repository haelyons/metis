# I1 — Drift probes on the autoformalizer

## What I will build

A linear probe over a Lean 4 autoformalizer's activations that flags, while it writes a
formal statement, when the statement has silently drifted from the natural-language one:
a strengthened hypothesis, a guessed convention, a reversed implication. The generator
used is **DeepSeek-Prover-V1.5-RL**, a 7B open-weights Lean 4 model
(`https://huggingface.co/deepseek-ai/DeepSeek-Prover-V1.5-RL`: "We release the
DeepSeek-Prover-V1.5 with 7B parameters, including base, SFT and RL models, to the
public."). 7B bf16 ≈ 14 GiB of weights, so one NVIDIA A6000 (48 GB) holds the model and
the cached hidden states.

The probe is the exact recipe from the MATH trace-correctness paper: standardize the
last-token hidden state per dimension, fit a logistic regression with C=0.1, select the
best layer by 5-fold cross-validated AUROC
(`https://arxiv.org/html/2605.09502v1`). That paper reports a linear probe predicts trace
correctness at 0.95 AUROC while verbalized confidence reaches only 0.67, and that the
signal is "diagnostic, not causal".

The novelty is the domain and the label. The only prior interp work on autoformalization
is on **SMT-LIB, not Lean**: a linear SAE probe reached 0.960 AUROC against a Z3 solver
oracle but only 0.679 against panel-majority intent labels
(`https://arxiv.org/html/2609.11085v2`). No one has (a) measured whether Lean statement
drift is linearly readable at all, (b) scored a probe against *human audit* labels rather
than solver or LLM-proxy labels, or (c) tested whether probes trained on *synthetic* drift
transfer to *natural* misformalizations.

## Baseline

The SMT-LIB autoformalization probe: 0.960 AUROC vs solver oracle, 0.679 vs LLM-proxy
intent (`https://arxiv.org/html/2609.11085v2`), on 950 candidate encodings. The MATH-500
trace probe (0.953 held-out AUROC, verbalized confidence 0.674) is the second baseline
(`https://arxiv.org/html/2605.09502v1`).

## Data

- **Seed faithful statements.** miniF2F's 488 informal+formal Lean theorem pairs
  (`https://arxiv.org/html/2109.00110v2`: "consists of 488 problem statements drawn from
  the AIME, AMC, and the International Mathematical Olympiad (IMO)"). A 2025 audit found
  discrepancies between the formal and informal statements in more than half of miniF2F
  (`https://arxiv.org/html/2511.03108v1`: "we trace back a considerable portion of this
  drop to discrepancies between the formal and informal statements for more than half of
  the problems in miniF2F") — drift is genuinely common, not a toy.
- **DriftBench.** 2,183 NL/Lean 4 pairs with controlled drift labels across six subfields
  (`https://arxiv.org/abs/2606.16541`: "We release DriftBench, a benchmark of 2,183 NL/Lean
  4 pairs with controlled drift labels across six subfields of mathlib4."). BPF+CPG, its
  counterfactual-probe method, detects 89.6% of drifted formalizations at a 3.0% false
  positive rate, against 41.2% for typecheck and 63.3% for an LLM judge (same page).
- **Synthetic drift (the parallel-labelling trick).** For each of 400 faithful seed
  statements, apply 5 counterfactual perturbations (strengthen a hypothesis, reverse an
  implication, swap a quantifier, drop an assumption, guess a typeclass) following BPF's
  Counterfactual Probe Generation (`https://arxiv.org/abs/2606.16541`). This yields 2,000
  synthetic drifted statements with labels by construction, in parallel, with no human in
  the loop.
- **Natural drift (the human audit).** Run the autoformalizer on 200 held-out informal
  statements; an expert labels each output faithful vs drifted. This is the serial step,
  and it is outside the GPU budget (≈ 20 expert-hours).

## How I check it is right

1. **Planted-signal sanity check (anchor).** We inject the drift signal ourselves; a
   working pipeline must recover it. Train the probe on planted synthetic drift and require
   AUROC ≥ 0.90, with a shuffled-label control at 0.50. Cross-check the probe with an
   independent RandomForest head. Compare against the published SMT-LIB SAE-probe 0.960
   (`https://arxiv.org/html/2609.11085v2`) as the external prior.
2. **Concealment gap.** A TF-IDF surface classifier on the same statements should sit near
   0.59 (the MATH paper's text classifier) and verbalized confidence near 0.674; a large
   probe-minus-surface gap is what makes the probe worth having
   (`https://arxiv.org/html/2605.09502v1`).
3. **Held-out evaluation.** The probe is scored on 200 human-audited natural drift pairs it
   never saw in training. AUROC ≥ 0.80 counts as readable (if_lever); ≤ 0.70 counts as
   weakly readable (if_not, near the 0.679 intent-label prior).
4. **Noise.** Bootstrap 95% CI over the held-out statements; 5 probe seeds × 3 generation
   seeds; a real difference is one whose CI does not overlap the 0.70/0.80 thresholds.

## What is serial, and how parallelism is used

Sequential chain: expert-labelled faithful/drifted pairs → one forward pass per statement
→ probe fit → held-out evaluation (4 steps; only labelling is serial, per the option
record). The plan breaks the serial dependency in two ways:

- **Labels in parallel:** synthetic drift is produced by counterfactual perturbation
  (BPF CPG), not by human labelling. Precedent for synthetic→real transfer: Goodfire's
  Rakuten SAE probes, trained on synthetic data, "outperformed other approaches when
  generalizing from synthetic to real production data"
  (`https://www.goodfire.com/research/rakuten-sae-probes-for-pii-detection`).
- **Forward passes in parallel:** each statement's activations are cached independently,
  so 4 A6000s cache disjoint shards side by side.

The condition for this to pay off: synthetic-drift-trained probes must transfer to natural
misformalizations. The cheap check is the transfer gate (below), run before the main spend.

## Phases (execution order)

1. **anchor** (1×A6000, time box 2h). Load the 7B model, run the planted-signal + shuffle
   controls, measure real tokens/s. Gate: planted AUROC ≥ 0.90, else stop (pipeline can't
   recover an injected signal). This also measures the throughput the cost depends on.
2. **audit** (human, outside budget). Expert labels 200 natural autoformalizer outputs.
   Runs in parallel with phase 3.
3. **transfer-gate** (1×A6000, ≈4.2h). Generate 2,000 synthetic CPG drift pairs, cache
   activations, train the probe on synthetic drift, evaluate on the 200 audited pairs.
   Gate: transfer AUROC ≥ 0.70, else fall back (train only on the 200 human labels and
   skip the 100k scale-up).
4. **scale** (4×A6000, ≈52 wall-h). Cache 100,000 statement-runs (six subfields × ~16k),
   fit probes, held-out evaluation; then 20,000-run transfers to a 14B model (1×A6000) and
   a 32B model (1×GH200) to test the "any model" claim and the non-monotonic-scaling
   finding from MATH (7B/14B dip, recovery at 32B/72B).
5. **report** (local CPU). AUROC vs priors, concealment gap, subfield + scale transfer
   table.

## Cost (Lambda on-demand, read 2026-10-17)

Rates from `https://lambda.ai/pricing` as read at the start of this run:
- A6000 48 GB, 1× or 4×, $1.09/GPU/hr.
- GH200 96 GB, 1×, $2.29/GPU/hr.
- H100 SXM 80 GB, 2×, $4.19/GPU/hr.

| Line | Phase | Rate | Hours | USD |
|---|---|---|---|---|
| anchor | anchor | 1×A6000 | 2 | 2.18 |
| synth | transfer-gate | 1×A6000 | 2000×7.5/3600 = 4.17 | 4.54 |
| scale-7b | scale | 4×A6000 | 100000×7.5/3600/4 = 52.1 | 227.1 |
| transfer-14b | scale | 1×A6000 | 20000×(300/30)/3600 = 55.6 | 60.6 |
| transfer-32b | scale | 1×GH200 | 20000×(300/20)/3600 = 83.3 | 190.8 |
| storage | scale | — | — | 10 GiB × $0.20 = 2.0 |
| *(opt) transfer-72b* | scale | 2×H100 | 5000×(300/5)/3600/2 = 41.7 | 349.2 |

**Core total ≈ $487.** With the optional 72B run, ≈ $836. Hard stop $1,000. The unused
headroom is deliberate: the probe fit and caching are cheap; the binding constraint is the
human audit (outside budget), not GPU.

Throughput figures (40/30/20/5 tok/s for 7B/14B/32B/72B) are GUESSes to be replaced by the
anchor-phase measurement; if the 7B rate comes in under ~20 tok/s the 100k-run scale line
shrinks to stay inside budget.

## Outside budget

- ~20 expert-hours to audit 200 natural drift pairs (the label the prior work lacked).
- Local 4-core CPU for probe fits and the report (probe fit is minutes on a fraction of a
  GPU, covered in the anchor/synth time boxes).

## What $1,000 cannot buy

- Causal repair of drift (the MATH signal is diagnostic, not causal) — only detection.
- Beyond-Lean cross-domain transfer (MATH→ARC was only 0.54/0.55).
- Closed autoformalizers (GPT-4-class) whose weights cannot be probed.
- A 9-model × 6-subfield × 50k-run full sweep (≈ $2.0k, the published 9-model scale).
