# Result

Picks 1 · PASS 0 · on-goal cards U4 0 · U3 0 · halts: cost record broken 1

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) Mapping AAV capsid-receptor interactions to explain barrier transcytosis versus intracellular retention | halted: cost record broken | seed | if_not | — | — → — | — → — | — | — | — → — | — | not judged · plan $0 · 0 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**B1 · Mapping AAV capsid-receptor interactions to explain barrier transcytosis versus intracellular retention.** seed pick · compute tested: yes · plan expects: not the lever · halted: cost record broken

**Question.** Which capsid-receptor binding signatures distinguish AAV variants that transcytose brain microvascular endothelial cells from those retained inside, and can a model predict this?

**What is known.** A published in-silico AAV design method (ALICE) mapped receptor binding and CNS tropism for 6,387 capsid sequences [src_alice]; it never separated transcytosis from endothelial retention. No published dataset matches computed capsid-receptor binding signatures to transcytosis versus intracellular retention in brain endothelial cells at more than a handful of capsids [src_merkel2016].

**Hypothesis.** Capsid-receptor binding signatures, not sequence alone, will classify which variants cross brain endothelium because receptor engagement drives transcytosis [src_tfr1_2023].

**Restructuring.** Adaptive selection rounds: each of four rounds waits on the previous model before scoring its 250 pairs. Pair signatures do not depend on the model, so all four rounds' pairs are scored in one batch instead of sequentially.

**If compute is the lever.** At 4,000 scored pairs accuracy reaches >=0.80, beating 1,000 pairs by >=0.10; batching takes 16 hours versus 64 for four sequential rounds.

**If not.** Accuracy stays <=0.65 at 250, 1,000 and 4,000 pairs; sequential selection hits that ceiling at 1,000 pairs, so batching buys speed only.

**Test.** Score 250, 1,000, 4,000 capsid-receptor pairs for binding signatures; classify published transcytosis versus retention under leave-one-capsid-family-out folds against sequence-only and affinity-rank baselines; time batch scoring versus four-round sequential scoring and side-by-side copies.

*Compute axis.* Capsid-receptor pair signature evaluations the answer needs: 250–4,000 pair evaluations, 3 levels. Closest prior: 6,387 [src_alice].

**Check first.** Predicted AAV1-AAVR contacts match published cryo-EM residues, and batch scoring matches four-round sequential accuracy within 0.03 [src_zhang2019]. Tolerance: contact-residue recall >=0.80 within 5 Angstrom; correct AAV1-over-AAV2 affinity order; |batch minus sequential| balanced accuracy <=0.03.

**Would not show.** Labels come from few published capsids, so accuracy intervals are wide. Predicted signatures are structural approximations, not measured affinities. No wet-lab BMEC validation is paid for here.

*Cost.* The cost record did not evaluate (2 errors); see the cost block.

**Halted at cost record broken.** undefined at full_scale.fs_wetlab_panel.ratio_to: "budget_usd" is not a number id

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-20
Errors     undefined at full_scale.fs_wetlab_panel.ratio_to: "budget_usd" is not a number id
           quote at numbers.sec_pair_seed.quote: 20 does not appear in the quote "NVIDIA H100 80GB HBM3 | 4.60 | 20.03 | 42.66 | 97.04"; a value transformed from the page belongs in a DERIVED number
```

**Derivations.**
```
Derivations: the cost record did not evaluate.
```

**Producer says (not judged).** expected if_not (Matched published transcytosis-versus-retention labels number in the tens [src_merkel2016][src_tfr1_2023], so extra scored pairs densify features without adding label information.); compute_tested yes (The axis is the number of capsid-receptor pair signature evaluations (250, 1,000, 4,000), which parallel GPUs buy directly, and classifier accuracy is measured at each level.); decides no; searched yes.

**Annotations.**
- cost record repaired: 1 expression(s) rewritten; unknown ids ignored: fs_wetlab_panel
- quote at numbers.sec_pair_seed.quote: 20 does not appear in the quote "NVIDIA H100 80GB HBM3 | 4.60 | 20.03 | 42.66 | 97.04"; a value transformed from the page belongs in a DERIVED number
- prose over 280 words (286)

**Root question (null).** Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-01/20261020-1922-card/out/work/seed-1/seed/idea/0bdd3c5c/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: G-plan repair: undefined at full_scale.fs_wetlab_panel.ratio_to: "budget_usd" is not a number id
seed:idea:seed: cost record repaired: 1 expression(s) rewritten; unknown ids ignored: fs_wetlab_panel
seed:idea:seed: quote at numbers.sec_pair_seed.quote: 20 does not appear in the quote "NVIDIA H100 80GB HBM3 | 4.60 | 20.03 | 42.66 | 97.04"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: halted at cost record broken: undefined at full_scale.fs_wetlab_panel.ratio_to: "budget_usd" is not a number id
seed:idea:seed: prose over 280 words (286)
```